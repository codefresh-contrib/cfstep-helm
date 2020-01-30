from BaseCommandBuilder import BaseCommandBuilder


class Helm2CommandBuilder(BaseCommandBuilder):

    def build_export_commands(self):
        return super().build_export_commands()

    def build_helm_install_commands(self):
        helm_upgrade_cmd = 'helm upgrade %s %s --install --force --reset-values ' % (self.release_name, self.chart_ref)
        return super().build_helm_install_commands_common(helm_upgrade_cmd)
