# mmetering-server

... to be continued

# Setup

### MySQL

add a ```my.cnf``` file to the project folder.

```mysql
[client]
database = [DB_NAME]
host = localhost
user = [USER]
password = [PASS]
default-character-set = utf8
```

Set the absolute path to this file in ```mmetering_server/settings.py```