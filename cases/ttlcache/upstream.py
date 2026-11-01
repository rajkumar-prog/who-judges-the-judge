# The fix cachetools shipped in 7.2.2: work out the expiration time before touching the cache.
KIND = "correct"
FILE = "cachetools/__init__.py"
OLD = """        with self.timer as time:
            self.expire(time)
            cache_setitem(self, key, value)
        try:
            link = self.__getlink(key)
        except KeyError:
            self.__links[key] = link = TTLCache._Link(key)
        else:
            link.unlink()
        link.expires = time + self.__ttl
"""
NEW = """        with self.timer as time:
            expires = time + self.__ttl
            self.expire(time)
            cache_setitem(self, key, value)
        try:
            link = self.__getlink(key)
        except KeyError:
            self.__links[key] = link = TTLCache._Link(key)
        else:
            link.unlink()
        link.expires = expires
"""
