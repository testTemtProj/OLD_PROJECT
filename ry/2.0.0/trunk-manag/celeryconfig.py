# coding: utf-8
import  sys
sys.path.append('.')

#CELERYD_POOL = "eventlet"

BROKER_HOST = "10.0.0.8"
BROKER_PORT = 5672
BROKER_USER = "celery-rynok-rpc"
BROKER_PASSWORD = "123qwe"
BROKER_VHOST = "rynok-rpc"
CELERY_RESULT_BACKEND = "amqp"
CELERY_IMPORTS = ("manager.lib.tasks", )# не забываем запятую
CELERY_TRACK_STARTED = True
# только для debug режима
CELERY_SEND_EVENTS = True
CELERYD_LOG_LEVEL = "DEBUG"
#CELERY_AMQP_TASK_RESULT_EXPIRES = 18000  # 18000 seconds.
"""
CELERY_RESULT_PERSISTENT = False

CELERYD_CONCURRENCY = 1

CELERY_DEFAULT_QUEUE = "default"
CELERY_QUEUES = {
    "default": {
        "binding_key": "task.#",
    },
    "products_tasks": {
        "binding_key": "products.parse",
        "exchange": "products_parse_tasks",
        "exchange_type": "direct",
    },
}
CELERY_ROUTES = ({"manager.lib.tasks":{
	"queue": "products_tasks",
	"routing_key": "products.parse"},
	},
	)
CELERY_DEFAULT_EXCHANGE = "tasks"
CELERY_DEFAULT_EXCHANGE_TYPE = "direct"
CELERY_DEFAULT_ROUTING_KEY = "task.default"
"""
