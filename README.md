# FacebookDumper
Dumps Facebook Messenger group chats to JSON. Useful for backups, or to check full message count.

## How to use
Edit the first few lines in the `facebook_dumper.py` file to match the request your browser sends when retrieving messages
then run it (use your Developer Tools). The script will create a directory and dump the JSON files retreived from the server,
split every X messages, set using `chunk_size` in the Python file. 
