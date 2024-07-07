import csv
import json
import re
from pathlib import Path

import readchar
import typer
import undetected_chromedriver as uc
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing_extensions import Annotated

from src.store import Store, prev, Image, CAT_1930

YEARS = ["1930"]

load_dotenv()

app = typer.Typer()


@app.command()
def annotate_ed_desc_images(
    debug: Annotated[bool, typer.Option("--debug", "-v")] = False,
):
    annotator = Annotator(debug)
    # annotator.process()
    # annotator.write(Path("../gannett-data/fs_eds.parquet"))


class Annotator:
    def __init__(self, debug):
        # self.driver = uc.Chrome(user_data_dir="selenium")

        self.store = Store(self.buildImageList())

    def buildImageList(self):
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

        for img in images:
            print(img)

        return images

    def process(self):
        self.driver.get(self.store.curr().url)

        while True:
            key = readchar.readkey()
            print(key)

            match key:
                case x if "0" <= x <= "9":
                    print("digit")
                case "[":
                    self.prevImage()
                case "]":
                    self.nextImage()
                case "n":
                    self.addNextED()
                case "p":
                    self.addPrevED()
                case "q":
                    break

    def addNextED(self):
        pass

    def addPrevED(self):
        pass

    def nextImage(self):
        old = self.store.curr()
        new = next(self.store)
        print(new)

        if old.utp_code == new.utp_code:
            self.clickSpanWithClass("next")
        else:
            self.driver.get(new.url)

    def prevImage(self):
        old = self.store.curr()
        new = prev(self.store)
        print(new)

        if old.utp_code == new.utp_code:
            self.clickSpanWithClass("previous")
        else:
            self.driver.get(new.url)

    def clickSpanWithClass(self, name):
        self.driver.execute_script(
            f"""
            var span = window.document.getElementsByClassName('{name}')[0];
            var click = new Event('click');
            span.dispatchEvent(click);
        """
        )


if __name__ == "__main__":
    app()
