class BaseCommandBuilder:

    def __init__(self, context):
        self.google_application_credentials_json = context["google_application_credentials_json"]
        self.release_name = context["release_name"]
        self.chart_ref = context["chart_ref"]
        self.chart_repo_url = context["chart_repo_url"]
        self.chart_version = context["chart_version"]
        self.namespace = context["namespace"]
        self.custom_valuesfiles = context["custom_valuesfiles"]
        self.custom_values = context["custom_values"]
        self.string_values = context["string_values"]
        self.recreate_pods = context["recreate_pods"]
        self.cmd_ps = context["cmd_ps"]
        self.dry_run = context["dry_run"]
        self.tiller_namespace = context["tiller_namespace"]

    def build_export_commands(self):
        lines = []
        lines.append('export HELM_REPO_ACCESS_TOKEN=$CF_API_KEY')
        lines.append('export HELM_REPO_AUTH_HEADER=Authorization')
        if self.google_application_credentials_json is not None:
            lines.append('echo -E $GOOGLE_APPLICATION_CREDENTIALS_JSON > /tmp/google-creds.json')
            lines.append('export GOOGLE_APPLICATION_CREDENTIALS=/tmp/google-creds.json')
        return lines

    def build_helm_upgrade_command(self, helm_upgrade_cmd):
        if self.chart_repo_url is not None:
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
            helm_upgrade_cmd += '--set %s=%s ' % (cli_set_key, val)
        for cli_set_key, val in sorted(self.string_values.items()):
            helm_upgrade_cmd += '--set-string %s=%s ' % (cli_set_key, val)
        if self.recreate_pods:
            helm_upgrade_cmd += '--recreate-pods '
        if self.cmd_ps is not None:
            helm_upgrade_cmd += self.cmd_ps
        if self.dry_run:
            helm_upgrade_cmd = 'echo ' + helm_upgrade_cmd
        return helm_upgrade_cmd

    def build_helm_install_commands_common(self, helm_upgrade_cmd):
        lines = []

        if self.release_name is None:
            raise Exception('Must set RELEASE_NAME in the environment (desired Helm release name)')

        # Only build dependencies if CHART_REPO_URL is not specified
        if self.chart_repo_url is None:
            helm_dep_build_cmd = 'helm dependency build %s' % self.chart_ref
            if self.dry_run:
                helm_dep_build_cmd = 'echo ' + helm_dep_build_cmd
            lines.append(helm_dep_build_cmd)

        lines.append(helm_upgrade_cmd)

        return lines
