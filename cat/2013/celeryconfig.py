from datetime import timedelta
from celery.schedules import crontab

import sys
sys.path.append('./')
sys.path.append('./catalog/lib/celery/')

BROKER_URL = "localhost"
BROKER_PORT = 5672
BROKER_USER = "catalog"
BROKER_PASSWORD = "123qwe"
BROKER_VHOST = "celery_catalog"
CELERY_BACKEND = "amqp"
CELERY_IMPORTS = ("tasks","sites_check", )

CELERYBEAT_SCHEDULE = {
    "test-task": {
        "task": "sites_check.check_sites",
        #"schedule": timedelta(seconds=5),
        "schedule": crontab(minute=00, hour=00),
        "args": ()
    },
}
