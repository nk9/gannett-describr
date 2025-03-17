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
    offline: Annotated[bool, typer.Option("--offline", "-o")] = False,
):
    scraper = Scraper(debug, driver(use_dummy=headless, use_offline=offline))

    # Let the browser launch
    time.sleep(3)

    scraper.scrape_ed_desc_images()


class Scraper:
    def __init__(self, debug, driver):
        self.debug = debug
        self.driver = driver
        # self.image_response_ids = set()
        self.written_arks = set()
        self.out_path = Path("../ed-desc-img/")  # TODO: make this dynamic

        db_path = "annotated.db"
        self.connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        self.cursor = self.connection.cursor()
        self.store = Store(self.cursor, buildImageList())

    def scrape_ed_desc_images(self):
        # Let the user sign in
        self.driver.get(
            "https://www.familysearch.org/auth/familysearch/login?returnUrl=https%3A%2F%2Fwww.familysearch.org%2Fen%2Fhome%2Fportal%2F"
        )

        val = input("Waiting… [q to quit] ")

        if val.lower() == "q":
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

                time.sleep(5)

                self.clickButtonLabelled("Download")
                self.waitForDownload(ark_path)
                print(" Done.", flush=True)

                # Avoid overwhelming the site
                time.sleep(random.randint(15, 30))

                if (
                    load_count % LOAD_LIMIT == 0
                    or img.short_ark not in self.written_arks
                ):
                    target = dt.datetime.now() + dt.timedelta(minutes=61)
                    print(f"Taking a break to avoid throttling. Resuming at {target}…")
                    time.sleep(61 * 60)

            else:
                print(f"        Skipping {last_3}")

    def image_path(self, img):
        return self.out_path / str(img.year) / img.utp_code / f"{img.short_ark}.jpg"

    def load_next(self, old, new):
        if old.utp_code == new.utp_code and new.image_index == old.image_index + 1:
            self.clickButtonLabelled("Next Image")
        else:
            self.driver.get(new.url)

    def clickButtonLabelled(self, ariaLabel):
        self.driver.execute_script(
            f"""
            window.document.querySelector('button[aria-label="{ariaLabel}"]')?.click();
            """
            # var click = new Event('click');
            # button.dispatchEvent(click);
        )

    def waitForDownload(self, ark_path: Path, timeout=60, check_interval=1):
        """
        Waits for a file to fully download, then moves it to `ark_path`.

        :param ark_path: Full destination path (including filename).
        :param timeout: Max time to wait for the file to download (in seconds).
        :param check_interval: Time interval between file existence checks.
        """
        download_dir = Path.home() / "Downloads"
        downloaded_file = download_dir / ark_path.name

        elapsed_time = 0
        last_size = -1

        while elapsed_time < timeout:
            if downloaded_file.exists():
                current_size = downloaded_file.stat().st_size
                if (
                    current_size > 0 and current_size == last_size
                ):  # Stable file size check
                    break
                last_size = current_size
            time.sleep(check_interval)
            elapsed_time += check_interval
        else:
            raise TimeoutError(
                f"Download timed out after {timeout} seconds: {ark_path.name}"
            )

        downloaded_file.rename(ark_path)
        self.written_arks.add(ark_path.stem)


if __name__ == "__main__":
    app()
