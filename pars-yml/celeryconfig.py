# coding: utf-8
import  sys
sys.path.append('.')

#CELERYD_POOL = "eventlet"

BROKER_HOST = "10.0.0.8"
BROKER_PORT = 5672
BROKER_USER = "celery-parser-rpc"
BROKER_PASSWORD = "123qwe"
BROKER_VHOST = "parser-rpc"

#CELERY_RESULT_BACKEND = "cache"
#CELERY_CACHE_BACKEND = 'memcached://10.0.0.8:11211/'
#CELERY_RESULT_BACKEND = "mongodb"
CELERY_RESULT_BACKEND = "redis"
CELERY_REDIS_HOST = "10.0.0.8"
CELERY_REDIS_PORT = 6379
CELERY_REDIS_DB = 0
#CELERY_MONGODB_BACKEND_SETTINGS = {
#    "host": "ws1",
#    "database": "mydb",
#    "taskmeta_collection": "my_taskmeta_collection",
#}

CELERY_TRACK_STARTED = True
CELERY_SEND_EVENTS = True

CELERY_IMPORTS = ("parseryml.lib.tasks", "parseryml.lib.task_image")# не забываем запятую

CELERY_AMQP_TASK_RESULT_EXPIRES = 18000  # seconds.

CELERY_RESULT_PERSISTENT = False

#CELERYD_CONCURRENCY = 10   #тест 

CELERY_QUEUES = {
    "default": {
        "binding_key": "task.#",
    },
    "image_tasks": {
        "binding_key": "image.process",
        "exchange": "processing_image_tasks",
        "exchange_type": "direct",
    },
    "parse_yml_task": {
	    "binding_key": "parseryml.process",
	    "exchange": "processing_yml_tasks",
	    'exchange_type': "direct"},
    "result": {
	    "binding_key": "result.queue",
	    "exchange": "result",
	    "exchange_type": "direct"},
}

CELERY_ROUTES = ({"parseryml.lib.tasks":{
	"queue": "parse_yml_task",
	"routing_key": "parseryml.process"},
	},
	{"parseryml.lib.task_image":{
		"queue":"image_task",
		"routing_key":"image.process"},
		},
	)
CELERY_DEFAULT_QUEUE = "default"

CELERY_DEFAULT_EXCHANGE = "tasks"

CELERY_DEFAULT_EXCHANGE_TYPE = "direct"

CELERY_DEFAULT_ROUTING_KEY = "task.default"

