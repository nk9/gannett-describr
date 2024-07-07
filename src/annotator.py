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

from src.store import Store, prev

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

        self.store = Store()

    def gotoNextImage(self):
        

    def process(self):
        self.driver.get(FS_IMG_URL.format(ark=ark, i=index, cat=CAT_1930))

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
