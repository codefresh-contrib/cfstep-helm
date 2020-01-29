from BaseCommandBuilder import BaseCommandBuilder


class Helm2CommandBuilder(BaseCommandBuilder):

    def build_export_commands(self, google_application_credentials_json):
        return super().build_export_commands(google_application_credentials_json)
