# coding: utf-8
import sys
sys.path.append('.')

BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "celery"
BROKER_PASSWORD = "123qwe"
BROKER_VHOST = "myvhost"
CELERY_RESULT_BACKEND = "cache"
CELERY_CACHE_BACKEND = 'memcached://127.0.0.1:11211/'
CELERY_IMPORTS = ("getmyad.tasks.tasks", "getmyad.tasks.sendmail")
CELERY_TASK_RESULT_EXPIRES = 3600

CELERYD_CONCURRENCY = 1		# TODO: Разобраться с блокировками AdLoad и убрать эту строку 
