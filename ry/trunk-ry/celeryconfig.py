# coding: utf-8
#import sys
#sys.path.append('.')

BROKER_HOST = "213.186.119.121"
BROKER_PORT = 5672
BROKER_USER = "celery"
BROKER_PASSWORD = "123qwe"
BROKER_VHOST = "myvhost"
CELERY_RESULT_BACKEND = "amqp"

CELERY_IMPORTS = ("rynok.lib.tasks", )

CELERYD_CONCURRENCY = 5
