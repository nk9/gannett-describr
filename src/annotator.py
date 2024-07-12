import csv
import json
import re
import sqlite3
from pathlib import Path

import readchar
import typer
import undetected_chromedriver as uc
from dotenv import load_dotenv
from prompt_toolkit import prompt
from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.data_structures import Point
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import ConditionalKeyBindings, KeyBindings
from prompt_toolkit.layout import ConditionalContainer, DynamicContainer
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.validation import ValidationError, Validator
from prompt_toolkit.widgets import SearchToolbar, TextArea
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing_extensions import Annotated

from src.ed import Ed
from src.store import CAT_1930, Image, Store, prev

# Turn on to get verbose Selenium logs
# import logging
# logging.basicConfig(level=10)

YEARS = ["1930"]

load_dotenv()

app = typer.Typer()


@app.command()
def annotate_ed_desc_images(
    debug: Annotated[bool, typer.Option("--debug", "-v")] = False,
):
    annotator = Annotator(debug)
    annotator.process()
    # annotator.write(Path("../gannett-data/fs_eds.parquet"))


show_ed_input = False
show_jump_input = False
DISABLE_DRIVER = True


@Condition
def notShowingInput():
    return not (show_ed_input or show_jump_input)


class DummyDriver:
    def get(self, url):
        pass

    def execute_script(self, script):
        pass


class Annotator:
    def __init__(self, debug):
        connection = sqlite3.connect("annotated.db")
        cursor = connection.cursor()
        self.store = Store(cursor, self.buildImageList())
        self.counter = 100
        self.last_manual_ed_str = ""

        self.curr_ed = Ed(1)
        options = uc.ChromeOptions()
        options.add_argument("--user-data-dir=selenium")
        options.add_argument("--disk-cache-size=524300000")
        options.add_argument("--window-size=1504,1573")  # broken?
        options.add_argument("--window-position=1504,25")  # broken?

        self.driver = DummyDriver() if DISABLE_DRIVER else uc.Chrome(options=options)

    def buildImageList(self):
        images = []
        film_info = {}
        data_dir = Path("../gannett-data/scrape_fs")
        ark_re = re.compile("(3:1:[^/]+)")

        for film_path in (data_dir / "films").glob("*.json"):
            with open(film_path) as jsonf:
                arks = []
                film_json = json.load(jsonf)
                for image in film_json["images"]:
                    m = ark_re.search(image)
                    if m:
                        arks.append(m.group(1))
                film_info[film_path.stem] = arks

        with open(data_dir / "ed_descr_nums.csv") as csvf:
            for row in csv.DictReader(csvf):
                if row["year"] in YEARS:
                    start = int(row["start_index"])
                    stop = int(row["stop_index"])
                    for index, ark in enumerate(film_info[row["digital_film_no"]]):
                        if index >= start and index <= stop:
                            images.append(
                                Image(
                                    row["year"], row["utp_code"], ark, index, CAT_1930
                                )
                            )

        return images

    def process(self):
        self.driver.get(self.store.curr().url)  # ("https://apple.com")  #

        bindings = self.setupBindings()

        application = Application(
            key_bindings=bindings, full_screen=False, layout=self.layout()
        )
        application.run()

    def layout(self):
        ed_search_field = SearchToolbar()
        self.ed_input = TextArea(
            height=1, prompt="ED> ", multiline=False, search_field=ed_search_field
        )
        self.ed_input.accept_handler = self.accept_ed

        jump_search_field = SearchToolbar()
        num_validator = NumberValidator()
        self.jump_input = TextArea(
            height=1,
            prompt="Jump to> ",
            multiline=False,
            search_field=jump_search_field,
            validator=num_validator,
        )
        self.jump_input.accept_handler = self.accept_jump

        def makeLayout():
            global show_ed_input
            global show_jump_input

            return HSplit(
                [
                    Window(FormattedTextControl(self.top_toolbar()), height=1),
                    Window(FormattedTextControl(self.bottom_toolbar()), height=1),
                    ConditionalContainer(content=self.ed_input, filter=show_ed_input),
                    ConditionalContainer(
                        content=self.jump_input, filter=show_jump_input
                    ),
                ]
            )

        return Layout(DynamicContainer(makeLayout))

    def setupBindings(self):
        kb = KeyBindings()

        @kb.add("s")
        def _(event):
            self.skipToLastEntered()

        @kb.add("n")
        def _(event):
            self.addNextED()

        @kb.add("c")
        def _(event):
            self.addCurrED()

        @kb.add("e")
        def _(event):
            self.addCustomED()

        @kb.add("]")
        def _(event):
            self.nextImage()

        @kb.add("[")
        def _(event):
            self.prevImage()

        @kb.add("}")
        def _(event):
            self.nextMetro()

        @kb.add("{")
        def _(event):
            self.prevMetro()

        @kb.add("+")
        def _(event):
            self.increaseED()

        @kb.add("-")
        def _(event):
            self.decreaseED()

        @kb.add("=")
        def _(event):
            self.syncImageWithDriver()

        @kb.add("j")
        def _(event):
            self.jumpToIndex()

        @kb.add("c-delete")
        def _(event):
            self.removeLastED()

        @kb.add("c-c")
        @kb.add("q")
        def _(event):
            get_app().exit(result=True)

        return ConditionalKeyBindings(kb, notShowingInput)

    def top_toolbar(self):
        now = self.store.curr()
        return f"{str(now)}"

    def bottom_toolbar(self):
        now = self.store.curr()
        return (
            f"<{self.store.index:5}> Cur ED: {self.curr_ed} - Img EDs: {list(now.eds)}"
        )

    def current_image(self):
        now = self.store.curr()
        return str(now)

    def skipToLastEntered(self):
        self.store.skipToLastEntered()
        last = self.store.curr()
        self.curr_ed = Ed.from_str(list(last.eds)[-1])
        new = next(self.store)

        self.driver.get(new.url)

    def addNextED(self):
        self.curr_ed += 1
        self.store.addEDToCurrentImage(self.curr_ed)

    def addCurrED(self):
        self.store.addEDToCurrentImage(self.curr_ed)

    def increaseED(self):
        self.curr_ed += 1

    def decreaseED(self):
        self.curr_ed -= 1

    def addCustomED(self):
        global show_ed_input
        show_ed_input = True

        self.ed_input.text = self.last_manual_ed_str
        get_app().layout.focus(self.ed_input)
        buf = self.ed_input.buffer
        buf.cursor_position = len(self.ed_input.text)

    def accept_ed(self, buffer):
        global show_ed_input
        show_ed_input = False

        stripped = self.ed_input.text.strip()
        self.last_manual_ed_str = stripped
        custom_ed = Ed.from_str(stripped)
        self.store.addEDToCurrentImage(custom_ed)

        return False  # reset the buffer

    def jumpToIndex(self):
        global show_jump_input
        show_jump_input = True

        self.jump_input.text = str(self.store.index)
        get_app().layout.focus(self.jump_input)
        buf = self.jump_input.buffer
        buf.cursor_position = len(self.jump_input.text)

    def accept_jump(self, buffer):
        global show_jump_input
        show_jump_input = False

        raw = self.jump_input.text
        new_index = int(raw)

        if new_index > 0 and new_index < len(self.store.images):
            self.store.index = new_index
            new = self.store.curr()
            self.driver.get(new.url)

        return False  # reset the buffer

    def removeLastED(self):
        self.store.removeLastED()

    def nextImage(self):
        old = self.store.curr()
        new = next(self.store)

        if old.utp_code == new.utp_code:
            self.clickSpanWithClass("next")
        else:
            self.driver.get(new.url)
            self.curr_ed = Ed(1)

    def prevImage(self):
        old = self.store.curr()
        new = prev(self.store)

        if old.utp_code == new.utp_code:
            self.clickSpanWithClass("previous")
        else:
            self.driver.get(new.url)
            self.curr_ed = Ed.from_str(self.store.largestEDForCurrentMetro())

    def nextMetro(self):
        new = self.store.nextMetro()
        self.driver.get(new.url)
        self.curr_ed = Ed(1)

    def prevMetro(self):
        new = self.store.prevMetro()
        self.driver.get(new.url)
        self.curr_ed = Ed.from_str(self.store.largestEDForCurrentMetro())

    def clickSpanWithClass(self, name):
        self.driver.execute_script(
            f"""
            var span = window.document.getElementsByClassName('{name}')[0];
            var click = new Event('click');
            span.dispatchEvent(click);
        """
        )

    def syncImageWithDriver(self):
        cur = self.store.curr()
        self.driver.get(cur.url)


class NumberValidator(Validator):
    def validate(self, document):
        text = document.text

        if text and not text.isdigit():
            i = 0

            # Get index of first non numeric character.
            # We want to move the cursor here.
            for i, c in enumerate(text):
                if not c.isdigit():
                    break

            raise ValidationError(message="Array index only", cursor_position=i)


if __name__ == "__main__":
    app()
