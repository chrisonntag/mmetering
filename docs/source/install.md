## Install <a name="install"></a>

Provided you already installed [Python 3.x](https://www.python.org/downloads/) and
[pip](https://bootstrap.pypa.io/get-pip.py)

Create a new virtualenvironment and install all dependencies from ```requirements.txt``` using pip.
```bash
python3 -m venv env/
source env/mmetering_server/bin/activate
pip install -r requirements.txt
```

### MySQL <a name="mysql"></a>

Create a new user and a database (e.g. MMETERING) and grant all privileges. After that, copy ```my.sample.cnf```
and rename it to ```my.cnf```. Change the file according to what you specified before.

```mysql
[client]
database = [DB_NAME]
host = localhost
user = [USER]
password = [PASS]
default-character-set = utf8
```

Set the __absolute path__ to this file in ```mmetering_server/settings.py```.

### Django <a name="django"></a>

Run the following commands to migrate and start the server.

```bash
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py collectstatic
python3 manage.py runserver 127.0.0.1:8000
```

#### Production

For production don't use the django-built-in server but instead use Apache with modwsgi.

### Celery workers <a name="celery"></a>

Simply start both workers in different terminal windows with

```bash
celery -A mmetering_server worker -l info
celery -A mmetering_server beat -l info
```

#### Production

In production you don't want to start the workers manually everytime, so let's create a supervisor for that.

Install supervisord ```sudo apt-get install supervisor``` and copy both files, ```mmetering_celery.conf``` and
```mmetering_celerybeat.conf``` (TODO: add these files) into ```/etc/supervisor/conf.d/```.

You also need to create both logfiles, mentioned in the scripts.
```bash
touch /var/log/mmetering/mmetering_worker.log
touch /var/log/mmetering/mmetering_beat.log
```

Finally update the supervisor in order to make him aware of the new services.
```bash
sudo supervisorctl reread
sudo supervisorctl update
```

Use these commands followed by the programs name {mmeteringcelery|mmeteringcelerybeat} to start/stop or get it's status.
```bash
sudo supervisorctl stop [program_name]
sudo supervisorctl start [program_name]
sudo supervisorctl status [program_name]
```

### SMTP-Server <a name="smtp"></a>
__TODO__  
In order to send mails when the system fails, you need to setup a SMTP server on your machine and change the following
things in ```settings.py```:

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = <host>'localhost'
EMAIL_PORT = <port>1025
DEFAULT_FROM_EMAIL = <your_mail>
```

## Setup <a name="setup"></a>

### Add user

Beside your admin account, which you create on the console with
```python3 manage.py createsuperuser```
you need to create two more user profiles in the admin backend. The first one has only the permission
to view the live data on the dashboard. The second one can also create flats and meters and can download
the whole data.

Log into the admin backend, click on Users -> Add User and create both users. After that, edit each of them
and add the desired permissions.

Note: Both users need to have staff status in order to be able to login at all.

### Add flats and meters

Log into the admin backend with either the admin or the service provider account. Follow all instructions.



