import sys

sys.path.append('.')

CELERYD_CONCURRENCY = 10
#CELERYD_POOL = 'eventlet'
CELERY_DISABLE_RATE_LIMITS = True
