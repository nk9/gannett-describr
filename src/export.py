import sqlite3
from pathlib import Path

import pandas as pd
import pyarrow as pa
import typer
from typing_extensions import Annotated

from src.utils import DB_FILE_NAME

app = typer.Typer()


@app.command()
def export(
    debug: Annotated[bool, typer.Option("--debug", "-v")] = False,
):
    exporter = Exporter(debug)
    exporter.write(Path("../gannett-data/fs_ed_descriptions.parquet"))


class Exporter:
    def __init__(self, debug):
        self.prepare_db_connection()
        descrs = self.fetch_ed_descrs()

        print(descrs)

    def write(self, path):
        print("writing…")
        pass

    def prepare_db_connection(self):
        self.connection = sqlite3.connect(f"file:{DB_FILE_NAME}?mode=ro", uri=True)
        self.db = self.connection.cursor()

    def fetch_ed_descrs(self):
        res = self.db.execute(
            """
            SELECT year, utp_code, name, image_index, ark
            FROM overview
            WHERE image_id IS NOT NULL
            ORDER BY year DESC, utp_code, CAST(name AS INTEGER), image_index;
            """
        ).fetchall()

        df = pd.DataFrame(res, columns=("year", "utp_code", "ed", "image_index", "ark"))

        return df


if __name__ == "__main__":
    app()
