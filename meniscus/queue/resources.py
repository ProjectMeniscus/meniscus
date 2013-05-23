from celery import Celery

celery = Celery('meniscus', broker='amqp://guest@localhost//')

