try:
    import uwsgi
    UWSGI = True
except ImportError:
    uwsgi = None
    UWSGI = False

CACHE_CONFIG = 'cache_config'
CACHE_TENANT = 'cache_tenant'


class NativeProxy(object):
    def __init__(self, cache_expires=900):
        self.server = uwsgi
        # Default timeout = 15 minutes
        self.expires = cache_expires

    def cache_exists(self, key, cache_name):
        if UWSGI:
            return self.server.cache_exists(key, cache_name)
        else:
            return None

    def cache_get(self, key, cache_name):
        if UWSGI:
            return self.server.cache_get(key, cache_name)
        else:
            return None

    def cache_set(self, key, value, cache_name):
        if UWSGI:
            self.server.cache_set(key, value, self.expires, cache_name)

    def cache_update(self, key, value, cache_name):
        if UWSGI:
            self.server.cache_update(key, value, self.expires, cache_name)

    def cache_del(self, key, cache_name):
        if UWSGI:
            self.server.cache_del(key, cache_name)

    def cache_clear(self, cache_name):
        if UWSGI:
            self.server.cache_clear(cache_name)

    def restart(self):
        if UWSGI:
            self.server.reload()
