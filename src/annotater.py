import typer
from dotenv import load_dotenv

from typing_extensions import Annotated


load_dotenv()

app = typer.Typer()


@app.command()
def annotate_ed_desc_images(
    debug: Annotated[bool, typer.Option("--debug", "-v")] = False,
):
    annotater = Annotater(debug)
    annotater.process()
    # annotater.write(Path("../gannett-data/fs_eds.parquet"))


class Annotater:
    def __init__(self, debug):
        pass

    def process(self):
        print("do stuff")


if __name__ == "__main__":
    app()
