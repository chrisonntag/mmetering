import os
from .defaults import *

if os.environ['MMETERING_PRODUCTION'] == 1:
    from .production import *
    PRODUCTION = True
else:
    from .development import *
    PRODUCTION = False
