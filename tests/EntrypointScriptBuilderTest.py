import unittest
import os
import sys
import urllib.request
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name)
from lib.EntrypointScriptBuilder import EntrypointScriptBuilder
from unittest.mock import patch, MagicMock

class ResponseMock(object):
    def __init__(self, headers):
        self.headers = headers;

    @property
    def _headers(self):
        return self.headers

class EntrypointScriptBuilderTest(unittest.TestCase):

    def test_custom_variables(self):
        env = {
            'KUBE_CONTEXT': 'local',
            'CHART_NAME': 'tomcat',
            'RELEASE_NAME': 'tomcat',
            'NAMESPACE': 'default',
            'CHART_VERSION': '0.4.3',
            'CHART_REPO_URL': 'https://charts.helm.sh/stable',
            'HELM_VERSION': '3',
            'CUSTOM_containers_node_env_secret_VALUE1': 'value1,',
            'CUSTOM_containers_node_env_secret_VALUE2': 'foo:bar;baz:qux;',
            'CUSTOM_containers_node_env_secret_VALUE3': 'value3',
            'CUSTOM_containers_node_env_secret_VALUE4': 'value4'
        }
        expect = '#!/bin/bash -e\n'
        expect += 'export HELM_REPO_ACCESS_TOKEN=$CF_API_KEY\n'
        expect += 'export HELM_REPO_AUTH_HEADER=Authorization\n'
        expect += 'kubectl config use-context "local"\n'
        expect += 'helm version --short -c\n'
        expect += 'helm upgrade tomcat tomcat --install --reset-values --repo https://charts.helm.sh/stable/ '
        expect += '--version 0.4.3 --namespace default --set containers.node.env.secret.VALUE1=value1, '
        expect += '--set containers.node.env.secret.VALUE2="foo:bar;baz:qux;" '
        expect += '--set containers.node.env.secret.VALUE3=value3 --set containers.node.env.secret.VALUE4=value4 '

        builder = EntrypointScriptBuilder(env)
        script_source = builder.build()

        self.assertEqual(script_source, expect)

    def test_helm_behind_firewall(self):
        env = {
            'KUBE_CONTEXT': 'local',
            'CHART_NAME': 'tomcat',
            'RELEASE_NAME': 'tomcat',
            'NAMESPACE': 'default',
            'CHART_VERSION': '0.4.3',
            'CHART_REPO_URL': 'azsp://test.azure.io',
            'HELM_VERSION': '3',
            'HELM_REPO_TOKEN': 'helmRepoToken',
            'CUSTOM_containers_node_env_secret_VALUE1': 'value1,',
            'CUSTOM_containers_node_env_secret_VALUE2': 'foo:bar;baz:qux;',
            'CUSTOM_containers_node_env_secret_VALUE3': 'value3',
            'CUSTOM_containers_node_env_secret_VALUE4': 'value4'
        }
        expect = '#!/bin/bash -e\n'
        expect += 'export HELM_REPO_ACCESS_TOKEN=$CF_API_KEY\n'
        expect += 'export HELM_REPO_AUTH_HEADER=Authorization\n'
        expect += 'kubectl config use-context "local"\n'
        expect += 'helm version --short -c\n'
        expect += 'helm upgrade tomcat tomcat --install --reset-values --repo https://00000000-0000-0000-0000-000000000000:helmRepoToken@test.azure.io/helm/v1/repo/ '
        expect += '--version 0.4.3 --namespace default --set containers.node.env.secret.VALUE1=value1, '
        expect += '--set containers.node.env.secret.VALUE2="foo:bar;baz:qux;" '
        expect += '--set containers.node.env.secret.VALUE3=value3 --set containers.node.env.secret.VALUE4=value4 '

        builder = EntrypointScriptBuilder(env)
        script_source = builder.build()

        self.assertEqual(script_source, expect)

    def test_helm_behind_firewall_mi(self):
        env = {
            'KUBE_CONTEXT': 'local',
            'CHART_NAME': 'tomcat',
            'RELEASE_NAME': 'tomcat',
            'NAMESPACE': 'default',
            'CHART_VERSION': '0.4.3',
            'CHART_REPO_URL': 'azmi://test2.azure.io',
            'HELM_VERSION': '3',
            'HELM_REPO_TOKEN': 'helmRepoToken2',
            'CUSTOM_containers_node_env_secret_VALUE1': 'value1,',
            'CUSTOM_containers_node_env_secret_VALUE2': 'foo:bar;baz:qux;',
            'CUSTOM_containers_node_env_secret_VALUE3': 'value3',
            'CUSTOM_containers_node_env_secret_VALUE4': 'value4'
        }
        expect = '#!/bin/bash -e\n'
        expect += 'export HELM_REPO_ACCESS_TOKEN=$CF_API_KEY\n'
        expect += 'export HELM_REPO_AUTH_HEADER=Authorization\n'
        expect += 'kubectl config use-context "local"\n'
        expect += 'helm version --short -c\n'
        expect += 'helm upgrade tomcat tomcat --install --reset-values --repo https://00000000-0000-0000-0000-000000000000:helmRepoToken2@test2.azure.io/helm/v1/repo/ '
        expect += '--version 0.4.3 --namespace default --set containers.node.env.secret.VALUE1=value1, '
        expect += '--set containers.node.env.secret.VALUE2="foo:bar;baz:qux;" '
        expect += '--set containers.node.env.secret.VALUE3=value3 --set containers.node.env.secret.VALUE4=value4 '

        builder = EntrypointScriptBuilder(env)
        script_source = builder.build()

        self.assertEqual(script_source, expect)

    @patch('urllib.request.urlopen')
    def test_jfrog_repo(self, mock_urlopen):
        cm = MagicMock()
        cm.getcode.return_value = 200
        cm.read.return_value = 'contents'
        cm.info.return_value = ResponseMock({'X-Artifactory-Id':'test', 'Server': 'Test'})
        mock_urlopen.return_value = cm
        env = {
            'ACTION': 'push',
            'KUBE_CONTEXT': 'local',
            'CHART_NAME': 'tomcat',
            'RELEASE_NAME': 'tomcat',
            'NAMESPACE': 'default',
            'CHART_VERSION': '0.4.3',
            'CHART_REPO_URL': 'https://my-cm-repo.jfrog.io/',
            'HELM_VERSION': '3',
            'CREDENTIALS_IN_ARGUMENTS': 'true',
            'HELMREPO_USERNAME': 'user',
            'HELMREPO_PASSWORD': 'pass'
        }
        expect = '#!/bin/bash -e\n'
        expect += 'export HELM_REPO_ACCESS_TOKEN=$CF_API_KEY\n'
        expect += 'export HELM_REPO_AUTH_HEADER=Authorization\n'
        expect += 'helm version --short -c\n'
        expect += 'helm repo add remote https://my-cm-repo.jfrog.io/ --username user --password pass \n'
        expect += 'helm dependency build tomcat || helm dependency update tomcat || echo "dependencies cannot be updated"\n'
        expect += 'PACKAGE="$(helm package tomcat --version 0.4.3 --destination /tmp | cut -d " " -f 8)"\n'
        expect += 'curl -u $HELMREPO_USERNAME:$HELMREPO_PASSWORD -T $PACKAGE https://my-cm-repo.jfrog.io/$(basename $PACKAGE)'
        builder = EntrypointScriptBuilder(env)
        script_source = builder.build()

        self.assertEqual(script_source, expect)

    def test_jfrog_repo_with_skip_repo_credentials_validation(self):
        env = {
            'ACTION': 'push',
            'KUBE_CONTEXT': 'local',
            'CHART_NAME': 'tomcat',
            'RELEASE_NAME': 'tomcat',
            'NAMESPACE': 'default',
            'CHART_VERSION': '0.4.3',
            'CHART_REPO_URL': 'https://my-cm-repo.jfrog.io/',
            'HELM_VERSION': '3',
            'CREDENTIALS_IN_ARGUMENTS': 'true',
            'SKIP_REPO_CREDENTIALS_VALIDATION': 'true',
            'HELMREPO_USERNAME': 'user',
            'HELMREPO_PASSWORD': 'pass'
        }
        expect = '#!/bin/bash -e\n'
        expect += 'export HELM_REPO_ACCESS_TOKEN=$CF_API_KEY\n'
        expect += 'export HELM_REPO_AUTH_HEADER=Authorization\n'
        expect += 'helm version --short -c\n'
        expect += 'helm repo add remote https://my-cm-repo.jfrog.io/ --username user --password pass \n'
        expect += 'helm dependency build tomcat || helm dependency update tomcat || echo "dependencies cannot be updated"\n'
        expect += 'PACKAGE="$(helm package tomcat --version 0.4.3 --destination /tmp | cut -d " " -f 8)"\n'
        expect += 'curl -u $HELMREPO_USERNAME:$HELMREPO_PASSWORD -T $PACKAGE https://my-cm-repo.jfrog.io/$(basename $PACKAGE)'
        builder = EntrypointScriptBuilder(env)
        script_source = builder.build()

        self.assertEqual(script_source, expect)


    @patch('urllib.request.urlopen')
    def test_jfrog_repo_exception(self, mock_urlopen):
        cm = MagicMock()
        cm.getcode.return_value = 200
        cm.read.return_value = 'contents'
        cm.info.return_value = ResponseMock({'Server': 'Test'})
        mock_urlopen.return_value = cm
        env = {
            'ACTION': 'push',
            'KUBE_CONTEXT': 'local',
            'CHART_NAME': 'tomcat',
            'RELEASE_NAME': 'tomcat',
            'NAMESPACE': 'default',
            'CHART_VERSION': '0.4.3',
            'CHART_REPO_URL': 'https://my-cm-repo.jfrog.io/',
            'HELM_VERSION': '3',
            'CREDENTIALS_IN_ARGUMENTS': 'true',
            'HELMREPO_USERNAME': 'user',
            'HELMREPO_PASSWORD': 'pass'
        }
        builder = EntrypointScriptBuilder(env)

        with self.assertRaises(Exception) as exc:
            script_source = builder.build()
        self.assertEquals(str(exc.exception), "\033[91mFailed to infer the Helm repository type\033[0m")

    @patch('urllib.request.urlopen')
    def test_jfrog_repo_url_validation(self, mock_urlopen):
        cm = MagicMock()
        cm.getcode.return_value = 302
        cm.read.return_value = 'contents'
        cm.info.return_value = ResponseMock({'Server': 'Test'})
        mock_urlopen.return_value = cm
        env = {
            'ACTION': 'push',
            'KUBE_CONTEXT': 'local',
            'CHART_NAME': 'tomcat',
            'RELEASE_NAME': 'tomcat',
            'NAMESPACE': 'default',
            'CHART_VERSION': '0.4.3',
            'CHART_REPO_URL': 'https://my-cm-repo.jfrog.io/',
            'HELM_VERSION': '3',
            'CREDENTIALS_IN_ARGUMENTS': 'true',
            'HELMREPO_USERNAME': 'user',
            'HELMREPO_PASSWORD': 'pass'
        }
        builder = EntrypointScriptBuilder(env)
        with self.assertRaises(Exception) as exc:
            script_source = builder.build()
        self.assertEquals(str(exc.exception), "\033[91mFailed to infer the Helm repository type\033[0m")

    @patch('urllib.request.urlopen')
    def test_jfrog_repo_url_validation_exception(self, mock_urlopen):
        mock_urlopen.side_effect = Exception('test')
        env = {
            'ACTION': 'push',
            'KUBE_CONTEXT': 'local',
            'CHART_NAME': 'tomcat',
            'RELEASE_NAME': 'tomcat',
            'NAMESPACE': 'default',
            'CHART_VERSION': '0.4.3',
            'CHART_REPO_URL': 'https://my-cm-repo.jfrog.io/',
            'HELM_VERSION': '3',
            'CREDENTIALS_IN_ARGUMENTS': 'true',
            'HELMREPO_USERNAME': 'user',
            'HELMREPO_PASSWORD': 'pass'
        }
        builder = EntrypointScriptBuilder(env)
        with self.assertRaises(SystemExit) as cm:
            script_source = builder.build()

        self.assertEqual(cm.exception.code, 1)

    @patch('urllib.request.urlopen')
    def test_jfrog_repo_url_validation_url_error(self, mock_urlopen):
        err = urllib.error.URLError('test')
        err.code = 401
        mock_urlopen.side_effect = err
        env = {
            'ACTION': 'push',
            'KUBE_CONTEXT': 'local',
            'CHART_NAME': 'tomcat',
            'RELEASE_NAME': 'tomcat',
            'NAMESPACE': 'default',
            'CHART_VERSION': '0.4.3',
            'CHART_REPO_URL': 'https://my-cm-repo.jfrog.io/',
            'HELM_VERSION': '3',
            'CREDENTIALS_IN_ARGUMENTS': 'true',
            'HELMREPO_USERNAME': 'user',
            'HELMREPO_PASSWORD': 'pass'
        }
        builder = EntrypointScriptBuilder(env)
        with self.assertRaises(SystemExit) as cm:
            script_source = builder.build()

        self.assertEqual(cm.exception.code, 1)

