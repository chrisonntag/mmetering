from __future__ import absolute_import
import logging

logger = logging.getLogger(__name__)


try:
    from .celery import app as celery_app
except (ImportError, TypeError, ValueError):
    logger.error("Couldn't import app from .celery as celery_app")

import pymysql
pymysql.install_as_MySQLdb()
