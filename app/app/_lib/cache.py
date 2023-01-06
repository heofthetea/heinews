
class Cache:

    CACHE: dict = {}

    def __init__(self, module):
        self.CACHE["cache-for"] = module


    def set(self, *, key=None, value=None) -> None:
        self.CACHE[key] = value

    def get(self, key) -> object:
        return self.CACHE.get(key)


    def keys(self):
        return self.CACHE.keys()

    def values(self):
        return self.CACHE.values()

    def pop(self, key) -> None:
        self.CACHE.pop(key)
