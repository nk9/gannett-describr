import csv
import json
import re
import sqlite3
from pathlib import Path
from pyrate_limiter import Duration, Limiter, RequestRate
import os
import logging
import textwrap
import typer
from dotenv import load_dotenv
from typing_extensions import Annotated

from src.be_nice import CachedLimiterSession

# Enable logging for Requests, etc
# logging.basicConfig(level=logging.DEBUG)

ED_DESC_URL = "https://www.familysearch.org/search/image/download?uri=https%3A%2F%2Fsg30p0.familysearch.org%2Fservice%2Frecords%2Fstorage%2Fdascloud%2Fdas%2Fv2%2F{}"

load_dotenv()

app = typer.Typer()


@app.command()
def scrape_ed_desc_images(
    debug: Annotated[bool, typer.Option("--debug", "-v")] = False,
):
    scraper = Scraper(debug)
    scraper.scrape_ed_desc_images()
    # scraper.write(Path("../gannett-data/fs_eds.parquet"))


class Scraper:
    def __init__(self, debug):
        self.debug = debug

        db_path = "annotated.db"
        self.connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        self.cursor = self.connection.cursor()

        rate = RequestRate(2, Duration.SECOND * 61)
        limiter = Limiter(rate)

        self.session = CachedLimiterSession(
            cache_name="scrape_fs_ed_desc",
            allowable_codes=[200],
            allowable_methods=["GET", "HEAD", "POST"],
            limiter=limiter,
        )
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.71 Safari/537.36",
            "Cookie": os.getenv("FS_COOKIE"),
            # "Authorization": os.getenv("FS_AUTH"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        }

    def scrape_ed_desc_images(self):
        arks = self.cursor.execute(
            "SELECT year, utp_code, ark FROM images ORDER BY id"
        ).fetchall()
        out_path = Path("../ed-desc-img/1930/")
        count = len(arks)

        for i, (
            year,
            utp_code,
            ark,
        ) in enumerate(arks):
            short_ark = ark[4:]
            ark_path = out_path / str(year) / utp_code / f"{short_ark}.jpg"
            ark_path.parent.mkdir(parents=True, exist_ok=True)
            if not ark_path.is_file():
                url = ED_DESC_URL.format(ark)
                headers = self.headers | {
                    "Referer": f"https://www.familysearch.org/ark:/61903/{ark}?cat=1037259",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Priority": "u=0, i",
                    "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126"',
                    "Sec-Fetch-Site": "same-origin",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-User": "?1",
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": '"macOS"',
                    "Accept-Language": "en-GB",
                    "Upgrade-Insecure-Requests": "1",
                }
                print(f"### Fetching {ark}")
                res = self.session.get(
                    url,
                    headers=headers,
                    # hooks={"response": print_roundtrip},
                    allow_redirects=False,
                )
                print("###", res.status_code)
                if res.status_code == 302:
                    redir_url = "https://www.familysearch.org" + res.headers["Location"]
                    res2 = self.session.get(
                        redir_url,
                        headers=headers,
                        # hooks={"response": print_roundtrip}
                    )
                    if res2.status_code == 200:
                        with open(ark_path, "wb") as f:
                            print(f"### [{i:5}/{count}] Writing {short_ark}.jpg")
                            f.write(res2.content)
                    else:
                        logging.warning(f"### Failed with code {res.status_code}")


def print_roundtrip(response, *args, **kwargs):
    format_headers = lambda d: "\n".join(f"{k}: {v}" for k, v in d.items())
    print(
        textwrap.dedent(
            """
        ---------------- request ----------------
        {req.method} {req.url}
        {reqhdrs}

        {req.body}
        ---------------- response ----------------
        {res.status_code} {res.reason} {res.url}
        {reshdrs}

        {res.text}
    """
        ).format(
            req=response.request,
            res=response,
            reqhdrs=format_headers(response.request.headers),
            reshdrs=format_headers(response.headers),
        )
    )


if __name__ == "__main__":
    app()
