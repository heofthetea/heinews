
# This class can only be used to cache data from the upload process in admin.py
class Cache:

    def __init__(self, id):
        self.id = id
        self.article_content = None
        self.num_images = None
        self.images = []
        self.num_answers = None

    def __repr__(self):
        return f"id: {self.id} \
        \n\tarticle_content: {self.article_content} \
        \n\tnum_images: {self.num_images} \
        \n\timages: {self.images} \
        \n\tnum_answers: {self.num_answers}"


    def set_article_content(self, value) -> None:
        self.article_content = value

    def set_num_images(self, value) -> None:
        self.num_images = value

    def add_image(self, value) -> None:
        self.images.append(value)

    def set_num_answers(self, value) -> None:
        self.num_answers = value

    #--------------------------------------------------------------------------------------------------------------

    def get_article_content(self) -> str:
        return self.article_content

    def get_num_images(self) -> int:
        return self.num_images

    def get_images(self) -> list:
        return self.images

    def get_num_answers(self) -> int:
        return self.num_answers



class CacheDistribution:
    def __init__(self):
        self.log = lambda msg: print(f"cache.CacheDistribution -> {msg}")
        self.caches = []

    def create_cache(self, id: str=None) -> Cache:
        temp_cache = Cache(id)
        self.caches.append(temp_cache)
        self.log(f"found cache: {temp_cache}")
        return temp_cache

    def get_cache(self, id) -> Cache:
        for cache in self.caches:
            if cache.id == id:
                return cache
        return None

    def remove_cache(self, id: str=None) -> None:
        temp_cache = self.get_cache(id)
        self.caches.remove(temp_cache)
        self.log([c.id for c in self.caches])
        



