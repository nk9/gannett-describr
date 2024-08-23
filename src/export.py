from pathlib import Path

import typer
from typing_extensions import Annotated

app = typer.Typer()


@app.command()
def export(
    debug: Annotated[bool, typer.Option("--debug", "-v")] = False,
):
    exporter = Exporter(debug)
    exporter.write(Path("../gannett-data/fs_ed_descriptions.parquet"))


class Exporter:
    def __init__(self, debug):
        pass

    def write(self, path):
        print("writing…")
        pass


if __name__ == "__main__":
    app()
