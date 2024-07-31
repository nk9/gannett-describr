import base64
import csv
import json
import logging
import os
import random
import re
import sqlite3
import textwrap
import time
from pathlib import Path

import typer
from dotenv import load_dotenv
from pyrate_limiter import Duration, Limiter, RequestRate
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from typing_extensions import Annotated

from src.be_nice import CachedLimiterSession
from src.driver import driver
from src.ed import Ed
from src.store import Store
from src.utils import buildImageList

# Enable logging for Requests, etc
# logging.basicConfig(level=logging.DEBUG)

ED_DESC_URL = "https://www.familysearch.org/search/image/download?uri=https%3A%2F%2Fsg30p0.familysearch.org%2Fservice%2Frecords%2Fstorage%2Fdascloud%2Fdas%2Fv2%2F{}"

load_dotenv()

app = typer.Typer()


@app.command()
def scrape_ed_desc_images(
    debug: Annotated[bool, typer.Option("--debug", "-v")] = False,
    headless: Annotated[bool, typer.Option("--headless", "-h")] = False,
):
    scraper = Scraper(debug, driver(headless))
    scraper.scrape_ed_desc_images()
    # scraper.write(Path("../gannett-data/fs_eds.parquet"))


class Scraper:
    def __init__(self, debug, driver):
        self.debug = debug
        self.driver = driver

        db_path = "annotated.db"
        self.connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        self.cursor = self.connection.cursor()
        self.store = Store(self.cursor, buildImageList())

    def scrape_ed_desc_images(self):
        out_path = Path("../ed-desc-img/1930/")

        # Let the user sign in
        self.driver.get(
            "https://www.familysearch.org/auth/familysearch/login?returnUrl=https%3A%2F%2Fwww.familysearch.org%2Fen%2Fhome%2Fportal%2F"
        )

        val = input("Waiting… [q to quit] ")

        if val == "q":
            return

        last = None

        for img in self.store:
            attempt = 0

            short_ark = img.ark[4:]
            ark_path = out_path / str(img.year) / img.utp_code / f"{short_ark}.png"
            ark_path.parent.mkdir(parents=True, exist_ok=True)
            last_3 = "/".join(ark_path.parts[-3:])

            if not ark_path.is_file() or ark_path.stat().st_size < 50_000:
                while True:
                    attempt += 1
                    self.loadImagePage(last, img)
                    time.sleep(10)  # Let the image fully load

                    try:
                        canvas = self.driver.find_element(
                            By.CSS_SELECTOR, ".openseadragon-canvas canvas"
                        )
                        data_url = self.driver.execute_script(
                            "return arguments[0].toDataURL()", canvas
                        )
                        header, encoded = data_url.split(",", 1)
                        image_data = base64.b64decode(encoded)

                        if len(image_data) < 1_000_000:
                            time.sleep(attempt * 10 * 60)  # Wait for awhile
                        else:
                            with open(ark_path, "wb") as file:
                                print(f"Writing  {last_3}")
                                file.write(image_data)
                                last = img
                                break  # out of the infinite while

                    except Exception as e:
                        logging.warn(f"Failed to find download link for {img.ark}")

                time.sleep(random.randint(10, 45))
            else:
                print(f"Skipping {last_3}")

    def loadImagePage(self, last, img):
        if img:
            if (
                last is not None
                and last.utp_code == img.utp_code
                and img.image_index == last.image_index + 1
            ):
                self.clickSpanWithClass("next")
            else:
                self.driver.get(img.url)

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
