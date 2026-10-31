# Written independently of upstream: same idea (nothing changes until the expiry is known),
# different shape. Uses dict.get instead of the try/except and names things differently.
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
NEW = """        with self.timer as now:
            # Compute this first: if it raises, the cache must be left untouched.
            deadline = now + self.__ttl
            self.expire(now)
            cache_setitem(self, key, value)
        link = self.__links.get(key)
        if link is None:
            link = self.__links[key] = TTLCache._Link(key)
        else:
            self.__links.move_to_end(key)
            link.unlink()
        link.expires = deadline
"""
