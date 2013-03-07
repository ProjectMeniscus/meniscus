try:
    import uwsgi
    UWSGI = True
except ImportError:
    uwsgi = None
    UWSGI = False


class NativeProxy(object):
    def __init__(self):
        self.server = uwsgi

    def cache_exists(self, key):
        if UWSGI:
            return self.server.cache_exists(key)
        else:
            return None

    def cache_get(self, key):
        if UWSGI:
            return self.server.cache_get(key)
        else:
            return None

    def cache_set(self, key, value):
        if UWSGI:
            self.server.cache_set(key, value)

    def cache_update(self, key, value):
        if UWSGI:
            self.server.cache_update(key, value)

    def cache_del(self, key):
        if UWSGI:
            self.server.cache_del(key)

    def cache_clear(self):
        if UWSGI:
            self.server.cache_clear()

    def restart(self):
        if UWSGI:
            self.server.restart()