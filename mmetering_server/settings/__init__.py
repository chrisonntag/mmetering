from .defaults import *
import configparser

config = configparser.RawConfigParser()
config.read(os.path.join(BASE_DIR, 'my.cnf'))

if config.getboolean('status', 'production'):
  from .production import *
  PRODUCTION = True
else:
  from .development import *
  PRODUCTION = False