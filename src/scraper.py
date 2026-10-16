import base64
import csv
import json
import logging
import os
import random
import re
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

from gannett_fs import (
    FS_LOGIN_URL,
    Credentials,
    FamilySearchClient,
    FamilySearchError,
    FilmInfoError,
    credentials_from_driver,
    credentials_from_env,
    save_credentials,
)

from src.be_nice import CachedLimiterSession
from src.driver import driver
from src.ed import Ed
from src.utils import buildImageList, missingSources, source_info_path

# Enable logging for Requests, etc
# logging.basicConfig(level=logging.DEBUG)

ED_DESC_URL = "https://www.familysearch.org/search/image/download?uri=https%3A%2F%2Fsg30p0.familysearch.org%2Fservice%2Frecords%2Fstorage%2Fdascloud%2Fdas%2Fv2%2F{}"
LOAD_LIMIT = 650

load_dotenv()

app = typer.Typer()


@app.command()
def scrape_images(
    index_csv: Annotated[Path, typer.Option("--index-csv")],
    img_dir: Annotated[Path, typer.Option("--img-dir")],
    env_file: Annotated[Path, typer.Option("--env-file")] = Path(
        "../gannett-pipeline/.env"
    ),
    debug: Annotated[bool, typer.Option("--debug", "-v")] = False,
    offline: Annotated[bool, typer.Option("--offline", "-o")] = False,
):
    scraper = Scraper(index_csv, img_dir, env_file, debug, offline)

    try:
        scraper.scrape()
    finally:
        scraper.quit()


class Scraper:
    def __init__(self, index_csv, img_dir, env_file, debug, offline):
        self.debug = debug
        self.index_csv = index_csv
        self.img_dir = img_dir
        self.env_file = env_file
        self.offline = offline
        self._driver = None
        self.browser_creds = None
        self.written_arks = set()

    @property
    def driver(self):
        """Only launch the browser once something actually needs it."""
        if self._driver is None:
            self._driver = driver(use_offline=self.offline)
            time.sleep(3)  # Let the browser launch

        return self._driver

    def quit(self):
        if self._driver is not None:
            self._driver.quit()

    def scrape(self):
        if missing := missingSources(self.index_csv):
            self.fetch_source_info(missing)

        images = buildImageList(self.index_csv, self.img_dir)
        pending = [img for img in images if self.needs_download(img)]

        if not images:
            print(f"No images listed in {self.index_csv}.")
            return

        if not pending:
            print(f"All {len(images)} images are already downloaded.")
            return

        print(f"{len(pending)} of {len(images)} images to download.")
        self.ensure_browser_session()
        self.download_images(images)

    # FamilySearch session

    def creds_work(self, creds: Credentials | None):
        return FamilySearchClient(creds).is_valid()

    def api_credentials(self):
        """Credentials for API requests, preferring the ones saved in the env file."""
        creds = credentials_from_env(self.env_file)

        if self.creds_work(creds):
            return creds

        print(f"FamilySearch credentials in {self.env_file} are missing or expired.")
        return self.ensure_browser_session()

    def ensure_browser_session(self):
        """Make sure the browser is signed in, prompting only if it isn't."""
        if self.browser_creds is not None:
            return self.browser_creds

        creds = credentials_from_driver(self.driver)

        if not self.creds_work(creds):
            self.driver.get(FS_LOGIN_URL)
            val = input("Sign into FamilySearch in the browser, then press Return [q to quit] ")

            if val.lower() == "q":
                raise typer.Exit(1)

            creds = credentials_from_driver(self.driver)

            if not self.creds_work(creds):
                print("Still not signed into FamilySearch.")
                raise typer.Exit(1)

        if creds != credentials_from_env(self.env_file):
            save_credentials(self.env_file, creds)
            print(f"Saved fresh FamilySearch credentials to {self.env_file}")

        self.browser_creds = creds
        return creds

    # Film and roll info

    def fetch_source_info(self, missing):
        print(f"Fetching image lists for {len(missing)} film(s)/roll(s)…")

        # Film info needs a signed-in session; rolls are public
        needs_creds = any(source.kind == "film" for source in missing)
        client = FamilySearchClient(self.api_credentials() if needs_creds else None)
        collection_rolls = {}
        failed = []

        for source in missing:
            path = source_info_path(self.index_csv, source)
            print(f"    {source} → {path}")

            try:
                if source.kind == "film":
                    content = client.film_info(source.id, source.collection)
                else:
                    if source.collection not in collection_rolls:
                        collection_rolls[source.collection] = client.collection_rolls(
                            source.collection
                        )
                    info = client.roll_info(
                        source.collection, source.id, collection_rolls[source.collection]
                    )
                    print(f"        {info['title']}: {len(info['images'])} images")
                    content = json.dumps(info, indent=2).encode()
            except (FilmInfoError, FamilySearchError) as e:
                print(f"    !!! {e}")
                failed.append(str(source))
                continue

            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

        if failed:
            print(f"Couldn't fetch image lists for {', '.join(failed)}; stopping.")
            raise typer.Exit(1)

    # Images

    def needs_download(self, img):
        path = img.local_path
        return not path.is_file() or path.stat().st_size < 20_000

    def download_images(self, images):
        last = None
        load_count = 0

        for img in images:
            ark_path = img.local_path
            ark_path.parent.mkdir(parents=True, exist_ok=True)
            last_3 = "/".join(ark_path.parts[-3:])

            if self.needs_download(img):
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

    def load_next(self, old, new):
        if (
            old is not None
            and old.utp_code == new.utp_code
            and new.image_index == old.image_index + 1
        ):
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
