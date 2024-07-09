import csv
import json
import re
import sqlite3
from pathlib import Path

import readchar
import typer
import undetected_chromedriver as uc
from dotenv import load_dotenv
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing_extensions import Annotated

from src.ed import Ed
from src.store import CAT_1930, Image, Store, prev

# Turn on to get verbose Selenium logs
# import logging
# logging.basicConfig(level=10)

YEARS = ["1930"]

load_dotenv()

app = typer.Typer()


@app.command()
def annotate_ed_desc_images(
    debug: Annotated[bool, typer.Option("--debug", "-v")] = False,
):
    annotator = Annotator(debug)
    annotator.process()
    # annotator.write(Path("../gannett-data/fs_eds.parquet"))


class Annotator:
    def __init__(self, debug):
        connection = sqlite3.connect("annotated.db")
        cursor = connection.cursor()
        self.store = Store(cursor, self.buildImageList())

        self.curr_ed = Ed(1)
        options = uc.ChromeOptions()
        options.add_argument("--user-data-dir=selenium")
        options.add_argument("--window-size=1504,1573")  # broken?
        options.add_argument("--window-position=1504,25")  # broken?
        self.driver = uc.Chrome(options=options)

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

        return images

    def process(self):
        # self.driver.get(self.store.curr().url)

        bindings = self.setupBindings()
        print("c: assign current ED, n: assign next ED, ]: next image")
        text = prompt("> ", bottom_toolbar=self.bottom_toolbar, key_bindings=bindings)
        print(f"You said: {text}")

    def setupBindings(self):
        kb = KeyBindings()

        @kb.add("s")
        def _(event):
            self.skipToLastEntered()

        @kb.add("n")
        def _(event):
            self.addNextED()

        @kb.add("c")
        def _(event):
            self.addCurrED()

        @kb.add("e")
        def _(event):
            self.addCustomED()

        @kb.add("]")
        def _(event):
            self.nextImage()

        @kb.add("[")
        def _(event):
            self.prevImage()

        @kb.add("c-delete")
        def _(event):
            self.removeLastED()

        return kb

    def bottom_toolbar(self):
        now = self.store.curr()
        return f"Current ED: {self.curr_ed} - {list(now.eds)}"

    def current_image(self):
        now = self.store.curr()
        return str(now)

    def skipToLastEntered(self):
        self.store.skipToLastEntered()
        last = self.store.curr()
        self.curr_ed = Ed.from_str(list(last.eds)[-1])
        next(self.store)

    def addNextED(self):
        self.curr_ed += 1
        self.store.addEDToCurrentImage(self.curr_ed)

    def addCurrED(self):
        self.store.addEDToCurrentImage(self.curr_ed)

    def addCustomED(self):
        custom_ed = Ed.from_str(input("ED: ").strip())
        self.store.addEDToCurrentImage(custom_ed)

    def removeLastED(self):
        self.store.removeLastED()

    def nextImage(self):
        old = self.store.curr()
        new = next(self.store)

        if old.utp_code == new.utp_code:
            self.clickSpanWithClass("next")
        else:
            self.driver.get(new.url)
            self.curr_ed = Ed(1)

    def prevImage(self):
        old = self.store.curr()
        new = prev(self.store)

        if old.utp_code == new.utp_code:
            self.clickSpanWithClass("previous")
        else:
            self.driver.get(new.url)
            self.curr_ed = Ed.from_str(self.store.largestEDForCurrentMetro())

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
