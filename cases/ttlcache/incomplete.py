# An honest but incomplete fix: roll back on failure by deleting the key. Fine for a new key in a
# cache with room, but an overwrite loses the old value, and an insert into a full cache has
# already evicted something by the time the error happens.
KIND = "incomplete"
FILE = "cachetools/__init__.py"
OLD = """        else:
            link.unlink()
        link.expires = time + self.__ttl
"""
NEW = """        else:
            link.unlink()
        try:
            link.expires = time + self.__ttl
        except BaseException:
            del self.__links[key]
            Cache.__delitem__(self, key)
            raise
"""
