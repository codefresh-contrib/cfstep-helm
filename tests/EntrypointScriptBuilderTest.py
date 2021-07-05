import unittest
import os
import sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name)
from lib.EntrypointScriptBuilder import EntrypointScriptBuilder
from unittest.mock import patch

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

    @patch.object(EntrypointScriptBuilder, 'handleNonPluginRepos', return_value='curl -u $HELMREPO_USERNAME:$HELMREPO_PASSWORD -T $PACKAGE https://my-cm-repo.jfrog.io/$(basename $PACKAGE)')
    def test_jfrog_repo(self, mock_urlopen):
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
