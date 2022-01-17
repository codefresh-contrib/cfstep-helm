import base64
import errno
import json
import os
import sys
import urllib.parse
import urllib.request
import zlib
import re

from lib.CommitMessageResolver import CommitMessageResolver
from lib.Helm2CommandBuilder import Helm2CommandBuilder
from lib.Helm3CommandBuilder import Helm3CommandBuilder

CHART_DIR = '/opt/chart'
DOWNLOAD_CHART_DIR = '/opt/chart_install_data'


class EntrypointScriptBuilder(object):

    def __init__(self, env):
        self.action = env.get('ACTION', 'install').lower()
        self.kube_context = env.get('KUBE_CONTEXT')
        self.chart_name = env.get('CHART_NAME')
        self.chart_ref = env.get('CHART_REF', env.get('CHART_NAME'))
        self.chart_subdir = env.get('CHART_SUBDIR') #optional Artifactory subfolder (inside Helm repo)
        self.chart_repo_url = env.get('CHART_REPO_URL')
        self.skip_repo_credentials_validation = env.get('SKIP_REPO_CREDENTIALS_VALIDATION', 'false')
        self.helm_repo_username = env.get('HELMREPO_USERNAME')
        self.helm_repo_password = env.get('HELMREPO_PASSWORD')
        self.chart_version = env.get('CHART_VERSION')
        self.app_version = env.get('APP_VERSION')
        self.release_name = env.get('RELEASE_NAME')
        self.namespace = env.get('NAMESPACE')
        self.tiller_namespace = env.get('TILLER_NAMESPACE')
        self.set_file = env.get('SET_FILE')
        self.dry_run = env.get('DRY_RUN')
        self.recreate_pods = env.get('RECREATE_PODS')
        self.wait = env.get('WAIT', 'false')
        self.timeout = env.get('TIMEOUT')
        self.cmd_ps = env.get('CMD_PS')
        self.commit_message = env.get('COMMIT_MESSAGE')
        self.google_application_credentials_json = env.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        self.chart = self._resolve_chart(env)
        self.helm_version = env.get('HELM_VERSION', '2.0.0')
        self.helm_repo_token = env.get('HELM_REPO_TOKEN')
        self.client_id = env.get('CLIENT_ID')
        self.client_secret = env.get('CLIENT_SECRET')
        self.tenant = env.get('TENANT')
        self.helm_repository_context = env.get('HELM_REPOSITORY_CONTEXT')

        credentials_in_arguments_str = env.get('CREDENTIALS_IN_ARGUMENTS', 'false')
        if credentials_in_arguments_str.upper() == 'TRUE':
            self.credentials_in_arguments = True
        else:
            self.credentials_in_arguments = False

        skip_stable_str = env.get('SKIP_CF_STABLE_HELM_REPO', 'false')
        if skip_stable_str.upper() == 'TRUE':
            self.skip_stable = True
        else:
            self.skip_stable = False

        self.azure_helm_token = None
        if self.helm_repository_context:
            context_integration = self._get_variables_from_helm_repo_integration(self.helm_repository_context)
            repo_url = context_integration.get('repositoryUrl')
            integration_name = context_integration.get('name')
            print("Using helm repo integration %s with URL %s" % (integration_name, repo_url))
            if repo_url is not None and integration_name is not None:
                env['CF_CTX_'+integration_name+'_URL'] = repo_url
            variables = context_integration.get('variables')
            if variables is None:
                print("Variables is empty in the %s helm repo integration" % integration_name)
            elif repo_url is not None and repo_url.startswith('gs://'):
                self.google_application_credentials_json = variables.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            elif repo_url is not None and repo_url.startswith('azsp://'):
                self.client_id = variables.get('CLIENT_ID')
                self.client_secret = variables.get('CLIENT_SECRET')
                self.tenant = variables.get('TENANT')
            elif repo_url is not None and (repo_url.startswith('http://') or repo_url.startswith('https://')):
                self.helm_repo_username = variables.get('HELMREPO_USERNAME')
                self.helm_repo_password = variables.get('HELMREPO_PASSWORD')

        if self.helm_version.startswith('2'):
            print("\033[93mCodefresh will discontinue support for Helm 2 on July 16 2021\033[0m")

        # Save chart data in files
        if self.chart is not None:
            self.chart = json.loads(self.chart)

            self.chart_ref = CHART_DIR
            if not os.path.exists(CHART_DIR):
                os.mkdir(CHART_DIR)

            sys.stderr.write('Chart files will be placed in {}\n'.format(CHART_DIR))
            for item in self.chart:
                if item['name'] == 'values':
                    item['name'] = 'values.yaml'
                item['name'] = item['name'].replace('Charts/', 'charts/')

                sys.stderr.write(item['name'] + '\n')

                if not os.path.exists(os.path.dirname('{}/{}'.format(CHART_DIR, item['name']))):
                    try:
                        os.makedirs(os.path.dirname('{}/{}'.format(CHART_DIR, item['name'])))
                    except OSError as exc:
                        if exc.errno != errno.EEXIST:
                            raise

                file = open('{}/{}'.format(CHART_DIR, item['name']), 'w')
                data = item['data'] if 'data' in item.keys() else ''
                file.write(data)
                file.close()

        # Values files (-f/--values) sourced from vars prefixed with "CUSTOMFILE_" or "VALUESFILE_"
        custom_valuesfiles = []
        for key, val in sorted(env.items()):
            key_upper = key.upper()
            if key_upper.startswith('CUSTOMFILE_') or key_upper.startswith('VALUESFILE_'):
                custom_valuesfiles.append(val)
        self.custom_valuesfiles = custom_valuesfiles

        # Specific value overrides (--set) sourced from vars prefixed with "CUSTOM_" or "VALUE_"
        custom_values = {}
        for key, val in sorted(env.items()):
            key_upper = key.upper()
            if key_upper.startswith('CUSTOM_'):
                cli_set_key = key[7:]
            elif key_upper.startswith('VALUE_'):
                cli_set_key = key[6:]
            else:
                continue
            cli_set_key = cli_set_key.replace('_', '.')
            cli_set_key = cli_set_key.replace('..', '_')
            custom_values[cli_set_key] = val
        self.custom_values = custom_values

        # Specific value overrides (--set-string) sourced from vars prefixed with or "VALUESTRING_"
        string_values = {}
        for key, val in sorted(env.items()):
            key_upper = key.upper()
            if key_upper.startswith('VALUESTRING_'):
                cli_set_key = key[12:]
            else:
                continue
            cli_set_key = cli_set_key.replace('_', '.')
            cli_set_key = cli_set_key.replace('..', '_')
            string_values[cli_set_key] = val
        self.string_values = string_values

        # Extract Helm repos to add from attached Helm repo contexts prefixed with "CF_CTX_" and suffixed with "_URL"
        helm_repos = {}
        chart_repo_url = self.chart_repo_url

        if chart_repo_url and chart_repo_url.startswith('az://'):
            if not self.azure_helm_token:
                self.azure_helm_token = self._get_azure_helm_token(chart_repo_url)
            chart_repo_url = chart_repo_url.strip('/').replace('az://',
                                                               'https://00000000-0000-0000-0000-000000000000:%s@' % self.azure_helm_token,
                                                               1) + '/helm/v1/repo'

        if chart_repo_url and chart_repo_url.startswith('azsp://'):
            if self.helm_repo_token is not None:
                self.azure_helm_token = self.helm_repo_token
            if not self.azure_helm_token:
                self.azure_helm_token = self._get_azure_service_principal_helm_token(chart_repo_url)
            chart_repo_url = chart_repo_url.strip('/').replace('azsp://',
                                                               'https://00000000-0000-0000-0000-000000000000:%s@' % self.azure_helm_token,
                                                               1) + '/helm/v1/repo'

        if chart_repo_url and chart_repo_url.startswith('azmi://'):
            self.azure_helm_token = self.helm_repo_token
            chart_repo_url = chart_repo_url.strip('/').replace('azmi://',
                                                               'https://00000000-0000-0000-0000-000000000000:%s@' % self.azure_helm_token,
                                                               1) + '/helm/v1/repo'

        helm_repo_username = env.get('HELMREPO_USERNAME')
        helm_repo_password = env.get('HELMREPO_PASSWORD')
        for key, val in sorted(env.items()):
            key_upper = key.upper()
            if key_upper.startswith('CF_CTX_') and key_upper.endswith('_URL'):
                repo_name = key_upper.replace('CF_CTX_', '', 1).replace('_URL', '', 1).replace('_', '-').lower()
                repo_url = val
                if not repo_url.endswith('/'):
                    repo_url += '/'

                if repo_url.startswith('http://') or repo_url.startswith('https://'):
                    if not self.credentials_in_arguments and (helm_repo_username is not None) and (
                            helm_repo_password is not None):
                        repo_url = repo_url.replace('://', '://%s:%s@' % (helm_repo_username, helm_repo_password), 1)

                # Modify azure URL to use https and contain token
                elif repo_url.startswith('az://'):
                    if not self.azure_helm_token:
                        self.azure_helm_token = self._get_azure_helm_token(repo_url)
                    repo_url = repo_url.replace('az://',
                                                'https://00000000-0000-0000-0000-000000000000:%s@' % self.azure_helm_token,
                                                1) + 'helm/v1/repo'

                elif repo_url.startswith('azsp://'):
                    if self.helm_repo_token is not None:
                        self.azure_helm_token = self.helm_repo_token
                    if not self.azure_helm_token:
                        self.azure_helm_token = self._get_azure_service_principal_helm_token(repo_url)
                    repo_url = repo_url.replace('azsp://',
                                                'https://00000000-0000-0000-0000-000000000000:%s@' % self.azure_helm_token,
                                                1) + 'helm/v1/repo'

                elif repo_url.startswith('azmi://'):
                    self.azure_helm_token = self.helm_repo_token
                    repo_url = repo_url.replace('azmi://',
                                                'https://00000000-0000-0000-0000-000000000000:%s@' % self.azure_helm_token,
                                                1) + 'helm/v1/repo'

                helm_repos[repo_name] = repo_url
                if self.chart_repo_url is None:
                    chart_repo_url = repo_url

        self.chart_repo_url = chart_repo_url
        self.helm_repos = helm_repos

        # Workaround a bug in Helm where url that doesn't end with / breaks --repo flags
        if self.chart_repo_url is not None and not self.chart_repo_url.endswith('/'):
            self.chart_repo_url += '/'

        self.helm_command_builder = self._select_helm_command_builder()

    def _get_variables_from_helm_repo_integration(self, helm_repo_integration):
        if self.dry_run:
            return 'xXxXx'
        cf_build_url = os.getenv('CF_BUILD_URL', 'https://g.codefresh.io')
        if 'local' in cf_build_url:
            cf_build_url = 'http://' + os.getenv('CF_HOST_IP')
        cf_build_url_parsed = urllib.parse.urlparse(cf_build_url)
        query_string = urllib.parse.urlencode({'decrypt': 'true'})
        token_url = '%s://%s/api/contexts/%s?%s' % (
            cf_build_url_parsed.scheme, cf_build_url_parsed.netloc, helm_repo_integration, query_string)
        request = urllib.request.Request(token_url)
        request.add_header('Authorization', os.getenv('CF_API_KEY'))
        data = json.load(urllib.request.urlopen(request))
        return {
            "name": data.get("metadata", {}).get("name"),
            "repositoryUrl": data.get('spec', {}).get('data', {}).get('repositoryUrl'),
            "variables": data.get('spec', {}).get('data', {}).get('variables'),
        };

    def _get_azure_helm_token(self, repo_url):
        service = repo_url.replace('az://', '').strip('/')
        sys.stderr.write('Obtaining one-time token for Azure Helm repo service %s ...\n' % service)
        if self.dry_run:
            return 'xXxXx'
        cf_build_url = os.getenv('CF_BUILD_URL', 'https://g.codefresh.io')
        if 'local' in cf_build_url:
            cf_build_url = 'http://' + os.getenv('CF_HOST_IP')
        cf_build_url_parsed = urllib.parse.urlparse(cf_build_url)
        token_url = '%s://%s/api/clusters/aks/helm/repos/%s/token' % (
            cf_build_url_parsed.scheme, cf_build_url_parsed.netloc, service)
        request = urllib.request.Request(token_url)
        request.add_header('Authorization', os.getenv('CF_API_KEY'))
        data = json.load(urllib.request.urlopen(request))
        return data['access_token']

    def _get_azure_service_principal_helm_token(self, repo_url):
        service = repo_url.replace('azsp://', '').strip('/')
        sys.stderr.write('Obtaining one-time token for Azure Helm repo service %s ...\n' % service)
        if self.dry_run:
            return 'xXxXx'
        cf_build_url = os.getenv('CF_BUILD_URL', 'https://g.codefresh.io')
        if 'local' in cf_build_url:
            cf_build_url = 'http://' + os.getenv('CF_HOST_IP')
        cf_build_url_parsed = urllib.parse.urlparse(cf_build_url)
        token_url = '%s://%s/api/clusters/aks-sp/helm/repos/%s/token' % (
            cf_build_url_parsed.scheme, cf_build_url_parsed.netloc, service)
        request = urllib.request.Request(token_url)
        if self.client_id and self.client_secret and self.tenant:
            data = {'clientId': self.client_id, 'clientSecret': self.client_secret, 'tenant': self.tenant}
            data = urllib.parse.urlencode(data).encode()
            request = urllib.request.Request(token_url, data)
        request.add_header('Authorization', os.getenv('CF_API_KEY'))
        data = json.load(urllib.request.urlopen(request))
        return data['access_token']

    def _build_kubectl_commands(self):
        lines = []
        if self.action in ['install', 'promotion', 'auth']:
            if self.kube_context is not None:
                kubectl_cmd = 'kubectl config use-context "%s"' % self.kube_context
                if self.dry_run:
                    kubectl_cmd = 'echo ' + kubectl_cmd
                lines.append(kubectl_cmd)

            if self.kube_context is None and self.action != 'auth':
                raise Exception(
                    'Must set KUBE_CONTEXT in environment (Name of Kubernetes cluster as named in Codefresh)')

        return lines

    @staticmethod
    def _resolve_chart(env):
        if env.get('CHART_JSON') is not None:
            return env.get('CHART_JSON')

        if env.get('CHART_JSON_GZIP') is not None:
            return zlib.decompress(base64.b64decode(env.get('CHART_JSON_GZIP')), 15 + 32)

        return None

    def _build_helm_commands(self):
        lines = []

        if self.action == 'auth':
            return lines

        if self.chart_ref is None:
            raise Exception(
                'Must set CHART_REF in the environment (this should be a reference to the chart as Helm CLI expects)')

        # Add Helm repos locally
        for repo_name, repo_url in sorted(self.helm_repos.items()):
            if self.credentials_in_arguments and (self.helm_repo_username is not None) and (
                    self.helm_repo_password is not None):
                helm_repo_add_cmd = 'helm repo add %s %s --username %s --password %s ' % (
                repo_name, repo_url, self.helm_repo_username, self.helm_repo_password)
            else:
                helm_repo_add_cmd = 'helm repo add %s %s' % (repo_name, repo_url)
            if self.dry_run:
                helm_repo_add_cmd = 'echo ' + helm_repo_add_cmd
            lines.append(helm_repo_add_cmd)

        if self.action == 'install':
            lines += self._build_helm_install_commands()
        if self.action == 'promotion':
            lines += self._build_helm_promotion_commands()
        elif self.action == 'push':
            lines += self._build_helm_push_commands()

        return lines

    def _build_helm_promotion_commands(self):
        lines = ['cd {} && helm dep update'.format(CHART_DIR)]

        if self.release_name is None:
            raise Exception('Must set RELEASE_NAME in the environment (desired Helm release name)')

        helm_promote_cmd = 'helm upgrade %s %s --install ' % (self.release_name, self.chart_ref)
        if self.tiller_namespace is not None:
            helm_promote_cmd += '--tiller-namespace %s ' % self.tiller_namespace
        if self.namespace is not None:
            helm_promote_cmd += '--namespace %s ' % self.namespace
        for custom_valuesfile in self.custom_valuesfiles:
            helm_promote_cmd += '--values %s ' % custom_valuesfile
        for cli_set_key, val in sorted(self.custom_values.items()):
            helm_promote_cmd += '--set %s=%s ' % (cli_set_key, self._normalize_value_string(val))
        for cli_set_key, val in sorted(self.string_values.items()):
            helm_promote_cmd += '--set-string %s=%s ' % (cli_set_key, val)
        if self.recreate_pods:
            helm_promote_cmd += '--recreate-pods '
        if self.cmd_ps is not None:
            helm_promote_cmd += self.cmd_ps
        if self.dry_run:
            helm_promote_cmd = 'echo ' + helm_promote_cmd
        lines.append(helm_promote_cmd)

        return lines

    def _build_helm_install_commands(self):
        lines = []

        if self.release_name is None:
            raise Exception('Must set RELEASE_NAME in the environment (desired Helm release name)')

        # Only build dependencies if CHART_REPO_URL is not specified. Skip for helm3
        if self.chart_repo_url is None and not self._helm_3():
            helm_dep_build_cmd = 'helm dependency build %s' % self.chart_ref
            if self.dry_run:
                helm_dep_build_cmd = 'echo ' + helm_dep_build_cmd
            lines.append(helm_dep_build_cmd)

        chart_path = self.chart_ref

        if self.commit_message is not None and self.helm_command_builder.need_pull(self.chart_ref, self.chart_name,
                                                                                   self.chart_repo_url,
                                                                                   self.chart_version):
            chart_path = "{}/{}".format(DOWNLOAD_CHART_DIR, self.chart_ref.split("/")[-1])
            pull_args = ' {} --untar --untardir {} '.format(self.chart_ref, DOWNLOAD_CHART_DIR)
            helm_pull_cmd = self.helm_command_builder.build_pull_command() + pull_args
            if self.chart_repo_url is not None:
                if self.credentials_in_arguments and (
                        self.chart_repo_url.startswith('http://') or self.chart_repo_url.startswith('https://')) and (
                        self.helm_repo_username is not None) and (self.helm_repo_password is not None):
                    helm_pull_cmd += '--repo %s --username %s --password %s ' % (
                    self.chart_repo_url, self.helm_repo_username, self.helm_repo_password)
                else:
                    helm_pull_cmd += '--repo %s ' % self.chart_repo_url
            if self.chart_version is not None:
                helm_pull_cmd += '--version %s ' % self.chart_version
            if self.dry_run:
                helm_pull_cmd = 'echo ' + helm_pull_cmd
            lines.append(helm_pull_cmd)

        if self.commit_message is not None:
            lines.extend(CommitMessageResolver.get_command(chart_path + '/templates/NOTES.txt', self.commit_message))

        helm_upgrade_cmd = self.helm_command_builder.build_helm_upgrade_command(self.release_name, chart_path)

        if not self.helm_command_builder.need_pull(self.chart_ref, self.chart_name, self.chart_repo_url,
                                                   self.chart_version) or self.commit_message is None:
            if self.chart_repo_url is not None:
                if self.credentials_in_arguments and (
                        self.chart_repo_url.startswith('http://') or self.chart_repo_url.startswith('https://')) and (
                        self.helm_repo_username is not None) and (self.helm_repo_password is not None):
                    helm_upgrade_cmd += '--repo %s --username %s --password %s ' % (
                    self.chart_repo_url, self.helm_repo_username, self.helm_repo_password)
                else:
                    helm_upgrade_cmd += '--repo %s ' % self.chart_repo_url
            if self.chart_version is not None:
                helm_upgrade_cmd += '--version %s ' % self.chart_version

        if self.tiller_namespace is not None:
            helm_upgrade_cmd += '--tiller-namespace %s ' % self.tiller_namespace
        if self.namespace is not None:
            helm_upgrade_cmd += '--namespace %s ' % self.namespace
        for custom_valuesfile in self.custom_valuesfiles:
            helm_upgrade_cmd += '--values %s ' % custom_valuesfile
        for cli_set_key, val in sorted(self.custom_values.items()):
            helm_upgrade_cmd += '--set %s=%s ' % (cli_set_key, self._normalize_value_string(val))
        for cli_set_key, val in sorted(self.string_values.items()):
            helm_upgrade_cmd += '--set-string %s=%s ' % (cli_set_key, val)
        if self.recreate_pods:
            helm_upgrade_cmd += '--recreate-pods '
        if self.wait.upper() == 'TRUE':
            helm_upgrade_cmd += '--wait '
        if self.timeout is not None:
            helm_upgrade_cmd += '--timeout %s ' % self.timeout
        if self.cmd_ps is not None:
            helm_upgrade_cmd += self.cmd_ps
        if self.set_file is not None:
            helm_upgrade_cmd += '--set-file %s ' % self.set_file
        if self.dry_run:
            helm_upgrade_cmd = 'echo ' + helm_upgrade_cmd
        lines.append(helm_upgrade_cmd)

        return lines

    def _build_helm_push_commands(self):
        lines = []

        if self.chart_repo_url is None:
            raise Exception(
                'Must set CHART_REPO_URL in the environment, otherwise attach a Helm Repo context (prefixed with CF_CTX_)')

        if self.credentials_in_arguments and (self.helm_repo_username is not None) and (
                self.helm_repo_password is not None):
            helm_repo_add_cmd = 'helm repo add remote %s --username %s --password %s ' % (
            self.chart_repo_url, self.helm_repo_username, self.helm_repo_password)
        else:
            helm_repo_add_cmd = 'helm repo add remote %s' % self.chart_repo_url
        if self.dry_run:
            helm_repo_add_cmd = 'echo ' + helm_repo_add_cmd
        lines.append(helm_repo_add_cmd)

        helm_dep_build_cmd = 'helm dependency build {} || ' \
                             'helm dependency update {} || ' \
                             'echo "dependencies cannot be updated"'.format(self.chart_ref, self.chart_ref)
        if not self._helm_3() and self.dry_run:
            helm_dep_build_cmd = 'echo ' + helm_dep_build_cmd
        lines.append(helm_dep_build_cmd)

        if self.dry_run:
            package_var = 'dryrun-0.0.1.tgz'
        else:
            package_var = '$(helm package %s ' % self.chart_ref
            if self.chart_version is not None:
                package_var += '--version ' + self.chart_version + ' '
            if self.app_version is not None:
                package_var += '--app-version ' + self.app_version + ' '
            package_var += '--destination /tmp | cut -d " " -f 8)'
        lines.append('PACKAGE="%s"' % package_var)

        if self.azure_helm_token is not None:
            helm_push_command = 'curl --fail -X PUT --data-binary "@${PACKAGE}" ' + self.chart_repo_url + '_blobs/$(basename $PACKAGE)' + ' || curl --fail -X PATCH --data-binary "@${PACKAGE}" ' + self.chart_repo_url + '_blobs/$(basename $PACKAGE)'
        elif self.chart_repo_url.startswith('cm://'):
            helm_push_command = 'helm push $PACKAGE remote'
        elif self.chart_repo_url.startswith('s3://'):
            helm_push_command = 'helm s3 push $PACKAGE remote'
        elif self.chart_repo_url.startswith('gs://'):
            helm_push_command = 'helm gcs push $PACKAGE remote'
        elif re.match('^(http|https):\/\/', self.chart_repo_url):
            print("CHART_REPO_URL protocol is http/https")
            helm_push_command = self.handle_non_plugin_repos()
        else:
            raise Exception('Unsupported protocol in CHART_REPO_URL')

        if self.cmd_ps is not None:
            helm_push_command += ' ' + self.cmd_ps

        if self.dry_run:
            helm_push_command = 'echo ' + helm_push_command

        lines.append(helm_push_command)

        return lines

    def _get_normalized_chart_repo_url(self):
        normalized_repo_url = self.chart_repo_url
        if normalized_repo_url and '@' in normalized_repo_url:
            normalized_repo_url = normalized_repo_url.split('//')[0] + '//' + normalized_repo_url.split('@')[1]
        return normalized_repo_url

    def handle_non_plugin_repos(self):
        helm_push_command = 'curl -u $HELMREPO_USERNAME:$HELMREPO_PASSWORD -T $PACKAGE ' + self.chart_repo_url
        if self.chart_subdir is not None:
            if not self.chart_subdir.endswith('/'): # adding trailing slash to CHART_SUBDIR
                self.chart_subdir += '/'
            helm_push_command += self.chart_subdir
        helm_push_command += '$(basename $PACKAGE)'
        normalized_repo_url = self._get_normalized_chart_repo_url()
        print("Performing test of the URL '%s' making an authenticated request to it..." % normalized_repo_url)
        if self.skip_repo_credentials_validation.upper() == 'TRUE':
            return helm_push_command

        try:
            request = urllib.request.Request(normalized_repo_url)
            authB64 = base64.b64encode(('%s:%s' % (self.helm_repo_username, self.helm_repo_password)).encode()).decode()
            request.add_header('Authorization', 'Basic %s' % authB64)
            response = urllib.request.urlopen(request)
        except urllib.error.URLError as err:
            print("\033[91mFailed to test your chart repository url, server responded with: %s %s \033[0m" % (
            err.code, err.reason))
            if err.code == 401:
                print("\033[91mPlease check the user name and password you specified for the Helm repository\033[0m")
            else:
                print("\033[91mPlease make sure the repo URL is valid\033[0m")
            sys.exit(1)
        except Exception as e:
            print('\033[91m%s\033[0m' % e)
            print("\033[91mPlease make sure the repo URL is valid\033[0m")
            sys.exit(1)

        print("\033[92mThe CHART_REPO_URL has been tested successfully\033[0m")
        print("Trying to infer Helm repository type from the response headers...")

        if self.is_artifactory_repo(response):
            return helm_push_command
        else:
            raise Exception("\033[91mFailed to infer the Helm repository type\033[0m")

    def is_artifactory_repo(self, repoResponse):
        try:
            headers = repoResponse.info()._headers
            for h in headers:
                if ("X-Artifactory-Id" in h) or ("Server" in h and "Artifactory" in h[1]) or \
                        ("x-artifactory-id" in h) or ("server" in h and "artifactory" in h[1]):
                    print("\033[94mAn Artifactory Helm repository has been recognized\033[0m")
                    return True
            print("\033[91mNot found Artifactory Helm repository headers\033[0m")
        except Exception as e:
            print('\033[91m%s\033[0m' % e)
            return None
        return False

    def _helm_3(self):
        return self.helm_version.startswith('3.')

    def _select_helm_command_builder(self):
        if self._helm_3():
            return Helm3CommandBuilder()
        else:
            return Helm2CommandBuilder()

    def _build_version_command(self):
        build_command = 'helm version --short -c'
        if self.dry_run:
            build_command = 'echo ' + build_command

        return [build_command]

    def _normalize_value_string(self, val):
        if ';' in val:
            val = '"' + val + '"'
        return val.replace(" ", "\\ ")

    def build(self):
        lines = ['#!/bin/bash -e']
        lines += self.helm_command_builder.build_export_commands(self.google_application_credentials_json)
        lines += self._build_kubectl_commands()
        lines += self._build_version_command()
        lines += self.helm_command_builder.build_repo_commands(self.skip_stable, self.dry_run)
        lines += self._build_helm_commands()
        return '\n'.join(lines)
