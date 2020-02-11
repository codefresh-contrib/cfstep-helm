from BaseCommandBuilder import BaseCommandBuilder


class Helm3CommandBuilder(BaseCommandBuilder):

    def build_export_commands(self, google_application_credentials_json):
        lines = super().build_export_commands(google_application_credentials_json)
        lines.append('export XDG_CACHE_HOME=/root/.helm')
        lines.append('export XDG_DATA_HOME=/root/.helm')
        lines.append('export XDG_CONFIG_HOME=/root/.helm')
        return lines

    def build_helm_upgrade_command(self, release_name, chart_ref):
        return 'helm upgrade %s %s --install --reset-values ' % (release_name, chart_ref)
