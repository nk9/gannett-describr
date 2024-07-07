import csv
import json
import re
from pathlib import Path

prev = lambda obj: obj.prev()

CAT_1930 = "1037259"
FS_IMG_URL = "https://www.familysearch.org/ark:/61903/{ark}?i={i}&cat={cat}"


class Image:
    def __init__(self, year, utp_code, ark, i, cat):
        self.year = year
        self.utp_code = utp_code
        self.ark = ark
        self.image_index = i
        self.cat = cat

    def __eq__(self, other):
        return self.ark == other.ark

    def __repr__(self):
        return f"{self.year} {self.utp_code:15} {self.image_index:4} {self.ark}"

    @property
    def url(self):
        return FS_IMG_URL.format_map(
            {"ark": ark, "i": self.image_index, "cat": self.cat}
        )


class Store:
    def __init__(self, images):
        self.images = images
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index + 1 < len(self.images):
            self.index += 1
            return self.images[self.index]

        raise StopIteration

    def prev(self):
        if self.index - 1 >= 0:
            self.index -= 1
            return self.images[self.index]

        raise StopIteration

    def curr(self):
        return self.images[self.index]
