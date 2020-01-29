from BaseCommandBuilder import BaseCommandBuilder


class Helm3CommandBuilder(BaseCommandBuilder):

    def build_export_commands(self, google_application_credentials_json):
        lines = super().build_export_commands(google_application_credentials_json)
        lines.append('export HELM_PLUGINS=/root/.helm/plugins')
        return lines
