
class EntrypointScriptBuilder(object):

    def __init__(self, env):
        self.action = env.get('ACTION', 'install').lower()
        self.kube_context = env.get('KUBE_CONTEXT')
        self.chart_ref = env.get('CHART_REF')
        self.chart_name = env.get('CHART_NAME')
        self.chart_repo_url = env.get('CHART_REPO_URL')
        self.chart_version = env.get('CHART_VERSION')
        self.release_name = env.get('RELEASE_NAME')
        self.namespace = env.get('NAMESPACE')
        self.dry_run = env.get('DRY_RUN')
        self.cmd_ps = env.get('CMD_PS')
        self.google_application_credentials_json = env.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')

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

        # Extract Helm repos to add from attached Helm repo contexts prefixed with "CF_CTX_" and suffixed with "_URL"
        helm_repos = {}
        chart_repo_url = self.chart_repo_url
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
                    if helm_repo_username is not None and helm_repo_password is not None:
                        repo_url = repo_url.replace('://', '://%s:%s@' % (helm_repo_username, helm_repo_password), 1)
                helm_repos[repo_name] = repo_url
                if self.chart_repo_url is None:
                    chart_repo_url = repo_url
        self.chart_repo_url = chart_repo_url
        self.helm_repos = helm_repos

        # Workaround a bug in Helm where url that doesn't end with / breaks --repo flags
        if self.chart_repo_url is not None and not self.chart_repo_url.endswith('/'):
            self.chart_repo_url += '/'

    def _build_export_commands(self):
        lines = []
        lines.append('export HELM_REPO_ACCESS_TOKEN=$CF_API_KEY')
        lines.append('export HELM_REPO_AUTH_HEADER=x-access-token')
        if self.google_application_credentials_json is not None:
            lines.append('echo -E $GOOGLE_APPLICATION_CREDENTIALS_JSON > /tmp/google-creds.json')
            lines.append('export GOOGLE_APPLICATION_CREDENTIALS=/tmp/google-creds.json')
        return lines

    def _build_kubectl_commands(self):
        lines = []
        if self.action == 'install':
            if self.kube_context is None:
                raise Exception('Must set KUBE_CONTEXT in environment (Name of Kubernetes cluster as named in Codefresh)')
            kubectl_cmd = 'kubectl config use-context %s' % self.kube_context
            if self.dry_run:
                kubectl_cmd = 'echo ' + kubectl_cmd
            lines.append(kubectl_cmd)
        return lines

    def _build_helm_commands(self):
        lines = []

        if self.action == 'auth':
            return lines

        chart_ref = self.chart_ref
        if chart_ref is None:
            if self.chart_name is None:
                raise Exception('Must set CHART_REF in the environment (this should be a reference to the chart as Helm CLI expects)')
            else:
                chart_ref = self.chart_name

        for repo_name, repo_url in sorted(self.helm_repos.items()):
            helm_repo_add_cmd = 'helm repo add %s %s' % (repo_name, repo_url)
            if self.dry_run:
                helm_repo_add_cmd = 'echo ' + helm_repo_add_cmd
            lines.append(helm_repo_add_cmd)

        if self.action == 'install':
            if self.release_name is None:
                raise Exception('Must set RELEASE_NAME in the environment (desired Helm release name)')

            # If CHART_REPO_URL is specified, we do not attempt to gather dependencies
            if self.chart_repo_url is None:
                helm_dep_build_cmd = 'helm dependency build %s' % chart_ref
                if self.dry_run:
                    helm_dep_build_cmd = 'echo ' + helm_dep_build_cmd
                lines.append(helm_dep_build_cmd)

            helm_upgrade_cmd = 'helm upgrade %s %s --install --force --reset-values ' % (self.release_name, chart_ref)
            if self.chart_repo_url is not None:
                helm_upgrade_cmd += '--repo %s ' % self.chart_repo_url
            if self.chart_version is not None:
                helm_upgrade_cmd += '--version %s ' % self.chart_version
            if self.namespace is not None:
                helm_upgrade_cmd += '--namespace %s ' % self.namespace
            for custom_valuesfile in self.custom_valuesfiles:
                helm_upgrade_cmd += '--values %s ' % custom_valuesfile
            for cli_set_key, val in sorted(self.custom_values.items()):
                helm_upgrade_cmd += '--set %s=%s' % (cli_set_key, val)
            if self.cmd_ps is not None:
                helm_upgrade_cmd += self.cmd_ps
            if self.dry_run:
                helm_upgrade_cmd = 'echo ' + helm_upgrade_cmd
            lines.append(helm_upgrade_cmd)

        elif self.action == 'push':
            if self.chart_repo_url is None:
                raise Exception('Must set CHART_REPO_URL in the environment, otherwise attach a Helm Repo context (prefixed with CF_CTX_)')

            helm_repo_add_cmd = 'helm repo add remote %s' % self.chart_repo_url
            if self.dry_run:
                helm_repo_add_cmd = 'echo ' + helm_repo_add_cmd
            lines.append(helm_repo_add_cmd)

            helm_dep_build_cmd = 'helm dependency build %s' % chart_ref
            if self.dry_run:
                helm_dep_build_cmd = 'echo ' + helm_dep_build_cmd
            lines.append(helm_dep_build_cmd)

            if self.dry_run:
                package_var = 'dryrun-0.0.1.tgz'
            else:
                package_var = '$(helm package %s ' % chart_ref
                if self.chart_version is not None:
                    package_var += self.chart_version + ' '
                package_var += '--destination /tmp | cut -d " " -f 8)'
            lines.append('PACKAGE="%s"' % package_var)

            if self.chart_repo_url.startswith('cm://'):
                helm_push_command = 'helm push $PACKAGE remote'
            elif self.chart_repo_url.startswith('s3://'):
                helm_push_command = 'helm s3 push $PACKAGE remote'
            elif self.chart_repo_url.startswith('gs://'):
                helm_push_command = 'helm gcs push $PACKAGE remote'
            else:
                raise Exception('Unsupported protocol in CHART_REPO_URL')

            if self.dry_run:
                helm_push_command = 'echo ' + helm_push_command

            lines.append(helm_push_command)

        return lines

    def build(self):
        lines = ['#!/bin/bash -e']
        lines += self._build_export_commands()
        lines += self._build_kubectl_commands()
        lines += self._build_helm_commands()
        return '\n'.join(lines)
