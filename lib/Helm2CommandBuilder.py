from lib.BaseCommandBuilder import BaseCommandBuilder


class Helm2CommandBuilder(BaseCommandBuilder):

    def build_export_commands(self, google_application_credentials_json):
        return super().build_export_commands(google_application_credentials_json)

    def build_helm_upgrade_command(self, release_name, chart_ref):
        return 'helm upgrade %s %s --install --reset-values ' % (release_name, chart_ref)

    def build_repo_commands(self, skip_stable, dry_run):
        return []

    def build_pull_command(self):
        return 'helm fetch'