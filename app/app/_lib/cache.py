
# This class can only be used to cache data from the upload process in admin.py
import csv
import io
from ast import literal_eval
from os import remove


def read_cache(file) -> list:
    file_content = []
    with io.open(file, "r", encoding='utf-8') as rf:
        reader = csv.reader(
            rf, 
            delimiter=';',
            quotechar='"', 
            quoting=csv.QUOTE_MINIMAL, 
            skipinitialspace=True
        )
        for row in reader:
            if(row):
                file_content.append(row)
    return file_content


def write_cache(file, new_content: list) -> None:
    with open(file, "w", newline='', encoding="utf-8") as wf:
        writer = csv.writer(
            wf, 
            delimiter=';', 
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL
        )
        writer.writerow(new_content)

#--------------------------------------------------------------------------------------------------------------

# creates an object dedicated to accessing one cache file
class Cache:
    def __init__(self, id):
        self.id = id
        self.file = f"static/temp/{id}.csv"
        self.cache = read_cache(file=self.file)

        self.article_content = str(self.cache[0][0])
        try:
            self.num_images = int(self.cache[0][1])
        except ValueError:
            self.num_images = None

        self.images = [n.strip() for n in literal_eval(self.cache[0][2])]

        try:
            self.num_answers = int(self.cache[0][3])
        except ValueError:
            self.num_answers = None
        

    def __repr__(self):
        return f"\n\tid: {self.id} \
        \n\tarticle_content: {self.article_content} \
        \n\tnum_images: {self.num_images} \
        \n\timages: {self.images} \
        \n\tnum_answers: {self.num_answers}"

    def commit(self) -> None:
        write_cache(
            self.file,
            [self.article_content, self.num_images, self.images, self.num_answers]
        )


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
    global read_cache
    global write_cache

    def __init__(self):
        self.log = lambda msg: print(f"cache.CacheDistribution -> {msg}")

    # saves cache to csv as [content, num_images, images:list, num_answers]
    def create_cache(self, id: str=None):
        write_cache(
            file=f"static/temp/{id}.csv",
            new_content=[None, None, [], None]
        )
        self.log(f"created cache: {id}.csv")

    def remove_cache(self, id: str=None) -> None:
        remove(f"static/temp/{id}.csv")
        






