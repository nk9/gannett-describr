import readchar
import typer
import undetected_chromedriver as uc
from dotenv import load_dotenv
from selenium import webdriver
from typing_extensions import Annotated
from selenium.webdriver.chrome.options import Options

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
        # chrome_options = uc.ChromeOptions()
        # chrome_options.user_data_dir = "selenium"
        # chrome_options.add_argument("user-data-dir=selenium")
        # options=chrome_options
        self.driver = uc.Chrome(user_data_dir="selenium")

    def process(self):
        self.driver.get(
            "https://www.familysearch.org/ark:/61903/3:1:3QHV-R32D-GPLS?i=493&cat=1037259"
        )

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
                case "q":
                    break

    def nextImage(self):
        self.clickSpanWithClass("next")

    def prevImage(self):
        self.clickSpanWithClass("previous")

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
