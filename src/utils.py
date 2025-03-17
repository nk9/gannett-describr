import csv
import json
import re
from pathlib import Path
from src.store import Image
from logging import error

DB_FILE_NAME = "annotated.db"


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
            if row["digital_film_no"] and row["start_index"] and row["stop_index"]:
                start = int(row["start_index"])
                stop = int(row["stop_index"])

                if start < stop:
                    metro_index = 0
                    if info := film_info.get(row["digital_film_no"]):
                        for index, ark in enumerate(info):
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
                    else:
                        error(f"No film info json found for {row['digital_film_no']}")
                else:
                    error(
                        f"{row['year']} {row['utp_code']}: start_index {start} > stop_index {stop}"
                    )

    return images
