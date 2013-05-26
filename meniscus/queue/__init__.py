from celery import Celery

celery = Celery('meniscus',
                broker='librabbitmq://guest@localhost//')

#celery.conf.CELERYD_POOL = 'eventlet'
celery.conf.CELERYD_CONCURRENCY = 100
celery.conf.CELERY_DISABLE_RATE_LIMITS = True