import sqlite3
from pathlib import Path

import pandas as pd
import pyarrow as pa
import typer
from typing_extensions import Annotated

app = typer.Typer()


@app.command()
def export(
    db: Annotated[Path, typer.Option("--db")],
    out: Annotated[Path, typer.Option("--out")],
    debug: Annotated[bool, typer.Option("--debug", "-v")] = False,
):
    exporter = Exporter(db, debug)
    exporter.write(out)


class Exporter:
    def __init__(self, db_path, debug):
        self.prepare_db_connection(db_path)
        self.descrs = self.fetch_ed_descrs()

    def write(self, path):
        schema = pa.schema(
            [
                ("year", pa.int16()),
                ("utp_code", pa.string()),
                ("metro_name", pa.string()),
                ("county", pa.string()),
                ("state", pa.string()),
                ("ed", pa.string()),
                ("image_index", pa.int32()),
                ("ark", pa.string()),
                ("description", pa.string()),
            ]
        )
        self.descrs.to_parquet(path, schema=schema, index=False)
        print(f"Written to {path}")

    def prepare_db_connection(self, db_path):
        self.connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        self.db = self.connection.cursor()

    def load_mapping(self):
        return pd.read_csv(Path("../gannett-data/city-county-mapping.csv"))

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
        mappingDF = self.load_mapping()

        mergedDF = pd.merge(df, mappingDF, on=["year", "utp_code"])
        mergedDF = mergedDF.rename(columns={"city": "metro_name"})
        mergedDF["description"] = ""

        return mergedDF


if __name__ == "__main__":
    app()
