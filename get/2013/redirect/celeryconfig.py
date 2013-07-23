# coding: utf-8
import sys
sys.path.append('.')

BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "getmyad_redirect"
BROKER_PASSWORD = "123qwe"
BROKER_VHOST = "getmyad_redirect_celery"
BROKER_CONNECTION_TIMEOUT = 1
BROKER_CONNECTION_MAX_RETRIES = 0
CELERY_RESULT_BACKEND = "cache"
CELERY_CACHE_BACKEND = 'memcached://127.0.0.1:11211/'
CELERY_IMPORTS = ("tasks",)
CELERY_TASK_RESULT_EXPIRES = 3600
CELERYD_CONCURRENCY = 1		# TODO: Разобраться с блокировками AdLoad и убрать эту строку 
