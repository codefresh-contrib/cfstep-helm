from string import Template


class CommitMessageResolver:
    @staticmethod
    def get_command(file, message):
        return Template('''
file_path="$file_path"
message="$message_string"

if [[ -f $file_path && $(cat $file_path) =~ commit_message:(.*) ]];  
then
  sed -E "s/(commit_message:)(.*)/\\1${message}/g" $file_path > $file_path.tmp
  mv $file_path.tmp $file_path
else
  echo "commit_message:${message}" >> $file_path
fi
        ''').safe_substitute(file_path=file, message_string=message).split('\n')
