from celery import Celery

celery = Celery('meniscus',
                broker='librabbitmq://guest@localhost//',
                config_source="meniscus.queue.celery_config")
