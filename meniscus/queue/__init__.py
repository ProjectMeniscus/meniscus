from celery import Celery

celery = Celery('meniscus', broker='librabbitmq://guest@localhost//')
