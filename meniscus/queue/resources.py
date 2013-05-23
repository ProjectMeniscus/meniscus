from celery import Celery

from meniscus.api.storage import persistence

celery = Celery('meniscus', broker='amqp://guest@localhost//')

