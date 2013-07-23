# coding: utf-8
import sys
sys.path.append('.')

BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "celery"
BROKER_PASSWORD = "123qwe"
BROKER_VHOST = "myvhost"
CELERY_RESULT_BACKEND = "amqp"
CELERY_IMPORTS = ("getmyad.tasks.tasks", "getmyad.tasks.sendmail")

CELERYD_CONCURRENCY = 1		# TODO: Разобраться с блокировками AdLoad и убрать эту строку 
