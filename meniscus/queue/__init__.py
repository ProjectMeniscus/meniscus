from celery import Celery

celery = Celery('meniscus',
                broker='librabbitmq://guest@localhost//')

celery.conf.CELERYD_CONCURRENCY = 10
CELERY_DISABLE_RATE_LIMITS = True