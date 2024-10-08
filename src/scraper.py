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
import datetime as dt
from pathlib import Path
from pprint import pformat

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
LOAD_LIMIT = 650

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
        self.image_response_ids = set()
        self.written_arks = set()
        self.out_path = Path("../ed-desc-img/")  # TODO: make this dynamic

        self.driver.add_cdp_listener("Network.responseReceived", self.response_received)
        self.driver.add_cdp_listener("Network.loadingFinished", self.loading_finished)

        db_path = "annotated.db"
        self.connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        self.cursor = self.connection.cursor()
        self.store = Store(self.cursor, buildImageList())

    def response_received(self, event):
        params = event["params"]
        res = params["response"]
        req_id = params["requestId"]

        if params["type"] == "Image" and "/dist.jpg?" in res["url"]:
            self.image_response_ids.add(req_id)

    def loading_finished(self, event):
        req_id = event["params"]["requestId"]

        if req_id in self.image_response_ids:
            try:
                body = self.driver.execute_cdp_cmd(
                    "Network.getResponseBody", {"requestId": req_id}
                )

                img = self.store.curr()
                image_path = self.image_path(img)
                image_data = base64.b64decode(body["body"])
                # print(image_data)

                if len(image_data) > 20_000:
                    with open(image_path, "wb") as file:
                        file.write(image_data)
                        self.written_arks.add(img.ark)
                        print(" Written.")
            except Exception as e:
                print("Failed:", e)

    def scrape_ed_desc_images(self):
        # Let the user sign in
        self.driver.get(
            "https://www.familysearch.org/auth/familysearch/login?returnUrl=https%3A%2F%2Fwww.familysearch.org%2Fen%2Fhome%2Fportal%2F"
        )

        val = input("Waiting… [q to quit] ")

        if val == "q":
            return

        last = self.store.curr()
        load_count = 0

        for img in self.store:
            ark_path = self.image_path(img)
            ark_path.parent.mkdir(parents=True, exist_ok=True)
            last_3 = "/".join(ark_path.parts[-3:])

            if not ark_path.is_file() or ark_path.stat().st_size < 20_000:
                print(f"[{load_count:5}] Loading  {last_3}…", end="", flush=True)

                self.load_next(last, img)
                load_count += 1
                last = img

                # Let the image fully load
                time.sleep(random.randint(15, 30))

                if load_count % LOAD_LIMIT == 0 or img.ark not in self.written_arks:
                    target = dt.datetime.now() + dt.timedelta(minutes=61)
                    print(f"Taking a break to avoid throttling. Resuming at {target}…")
                    time.sleep(61 * 60)

            else:
                print(f"        Skipping {last_3}")

    def image_path(self, img):
        short_ark = img.ark[4:]
        return self.out_path / str(img.year) / img.utp_code / f"{short_ark}.png"

    def load_next(self, old, new):
        if old.utp_code == new.utp_code and new.image_index == old.image_index + 1:
            self.clickSpanWithClass("next")
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
