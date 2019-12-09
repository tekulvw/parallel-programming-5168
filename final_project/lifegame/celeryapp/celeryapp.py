from celery import Celery
from . import celeryconfig

app = Celery(
    "tasks",
    backend='rpc://',
    broker="amqp://guest:guest@localhost:5672",
    include=["lifegame.celeryapp.tasks"],
)

app.conf.update(
    result_expires=3600,
)

app.config_from_object(celeryconfig)
