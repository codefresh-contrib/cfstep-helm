from BaseCommandBuilder import BaseCommandBuilder


class Helm3CommandBuilder(BaseCommandBuilder):

    def build_export_commands(self):
        lines = super().build_export_commands()
        lines.append('export HELM_PLUGINS=/root/.helm/plugins')
        return lines

    def build_helm_install_commands(self):
        helm_upgrade_cmd = 'helm upgrade %s %s --install --reset-values ' % (self.release_name, self.chart_ref)
        return super().build_helm_install_commands_common(helm_upgrade_cmd)
