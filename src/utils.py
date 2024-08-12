import csv
import json
import re
from pathlib import Path
from src.store import Image


def buildImageList():
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
            if row["digital_film_no"]:
                start = int(row["start_index"])
                stop = int(row["stop_index"])
                metro_index = 0
                for index, ark in enumerate(film_info[row["digital_film_no"]]):
                    if index >= start and index <= stop:
                        images.append(
                            Image(
                                row["year"],
                                row["utp_code"],
                                ark,
                                index,
                                metro_index,
                                stop - start,
                                row["collection"],
                            )
                        )
                        metro_index += 1

    return images
