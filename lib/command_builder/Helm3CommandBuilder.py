from lib.command_builder.BaseCommandBuilder import BaseCommandBuilder


class Helm3CommandBuilder(BaseCommandBuilder):

    def build_export_commands(self, google_application_credentials_json):
        return super().build_export_commands(google_application_credentials_json)
