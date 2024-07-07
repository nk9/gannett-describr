import csv
import json
import re
from pathlib import Path

prev = lambda obj: obj.prev()

YEARS = ["1930"]
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
    def __init__(self):
        self.store = self.populateStore()

        self.index = 0

    def populateStore(self):
        images = []
        film_info = {}
        data_dir = Path("../gannett-data/scrape_fs")
        ark_re = re.compile("(3:1:[^/]+)")

        for film_path in (data_dir / "films").glob("*.json"):
            with open(film_path) as jsonf:
                arks = []
                film_json = json.load(jsonf)
                for image in film_json["images"]:
                    m = ark_re.search(image)
                    if m:
                        arks.append(m.group(1))
                film_info[film_path.stem] = arks

        with open(data_dir / "ed_descr_nums.csv") as csvf:
            for row in csv.DictReader(csvf):
                if row["year"] in YEARS:
                    start = int(row["start_index"])
                    stop = int(row["stop_index"])
                    for index, ark in enumerate(film_info[row["digital_film_no"]]):
                        if index >= start and index <= stop:
                            images.append(
                                Image(
                                    row["year"], row["utp_code"], ark, index, CAT_1930
                                )
                            )

        return images

    def __iter__(self):
        return self

    def __next__(self):
        if self.index + 1 < len(self.store):
            self.index += 1
            return self.store[self.index]

        raise StopIteration

    def prev(self):
        if self.index - 1 >= 0:
            self.index -= 1
            return self.store[self.index]

        raise StopIteration

    def curr(self):
        return self.store[self.index]
