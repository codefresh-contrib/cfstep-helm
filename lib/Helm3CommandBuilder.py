from lib.BaseCommandBuilder import BaseCommandBuilder


class Helm3CommandBuilder(BaseCommandBuilder):

    def build_export_commands(self, google_application_credentials_json):
        lines = super().build_export_commands(google_application_credentials_json)
        return lines

    def build_helm_upgrade_command(self, release_name, chart_ref):
        return 'helm upgrade %s %s --install --reset-values ' % (release_name, chart_ref)

    def build_repo_commands(self, skip_stable, dry_run):
        lines = []
        if not skip_stable:
            add_stable_command = 'helm repo add cf-stable https://charts.helm.sh/stable'
            if dry_run:
                add_stable_command = 'echo ' + add_stable_command
            lines.append(add_stable_command)
        return lines

    def build_pull_command(self):
        return 'helm pull'
