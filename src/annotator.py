import sqlite3
from enum import Enum, auto
from pathlib import Path

import readchar
import typer
from dotenv import load_dotenv
from prompt_toolkit import prompt
from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.data_structures import Point
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import (
    ConditionalKeyBindings,
    KeyBindings,
    merge_key_bindings,
)
from prompt_toolkit.layout import ConditionalContainer, DynamicContainer
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.validation import ValidationError, Validator
from prompt_toolkit.widgets import SearchToolbar, TextArea
from selenium.webdriver.chrome.options import Options
from typing_extensions import Annotated

from src.driver import driver
from src.ed import Ed, ManualEDList
from src.store import Image, Store, prev
from src.utils import buildImageList

# Turn on to get verbose Selenium logs
# import logging
# logging.basicConfig(level=10)

SHOWING_ED_INPUT = False
SHOWING_JUMP_INPUT = False


class EDState(Enum):
    NONE = auto()
    CURRENT_ED = auto()
    CUSTOM_ED = auto()
    FILL_TO_ED = auto()


load_dotenv()

app = typer.Typer()


@app.command()
def annotate_ed_desc_images(
    debug: Annotated[bool, typer.Option("--debug", "-v")] = False,
    headless: Annotated[
        bool, typer.Option("--headless", "-h", "--dummy", "-d")
    ] = False,
):
    annotator = Annotator(debug, driver(headless))
    annotator.process()
    # annotator.write(Path("../gannett-data/fs_eds.parquet"))


@Condition
def notShowingInput():
    return not (SHOWING_ED_INPUT or SHOWING_JUMP_INPUT)


@Condition
def showingInput():
    return SHOWING_ED_INPUT or SHOWING_JUMP_INPUT


class DummyDriver:
    def get(self, url):
        pass

    def execute_script(self, script):
        pass


class Annotator:
    def __init__(self, debug, driver):
        self.driver = driver
        self.debug = debug
        self.ed_input_state = EDState.NONE

        connection = sqlite3.connect("annotated.db")
        cursor = connection.cursor()
        self.store = Store(cursor, buildImageList())
        self.store.populate_db()
        _ = next(self.store)  # Tee up correct curr() image

        self.counter = 100
        self.manual_eds = ManualEDList()

        self.curr_ed = Ed(1)

    def process(self):
        self.driver.get(self.store.curr().local_url)  # ("https://apple.com")  #

        bindings = self.setupBindings()

        application = Application(
            key_bindings=bindings,
            full_screen=False,
            layout=self.layout(),
        )
        application.timeoutlen = 0
        application.ttimeoutlen = 0
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
            return HSplit(
                [
                    Window(FormattedTextControl(self.top_toolbar()), height=1),
                    Window(FormattedTextControl(self.bottom_toolbar()), height=1),
                    ConditionalContainer(
                        content=self.ed_input, filter=SHOWING_ED_INPUT
                    ),
                    ConditionalContainer(
                        content=self.jump_input, filter=SHOWING_JUMP_INPUT
                    ),
                ]
            )

        return Layout(DynamicContainer(makeLayout))

    def setupBindings(self):
        kb = KeyBindings()

        @kb.add("s")
        def _(event):
            self.skipToLastEnteredWithinMetro()

        @kb.add("S")
        def _(event):
            self.skipToLastEntered()

        @kb.add("n")
        def _(event):
            self.addNextED()

        @kb.add("m")
        def _(event):
            self.addCurrED()

        @kb.add("e")
        def _(event):
            self.display_ed_input(EDState.CURRENT_ED)

        @kb.add("E")
        def _(event):
            self.display_ed_input(EDState.CUSTOM_ED)

        @kb.add("f")
        def _(event):
            self.display_ed_input(EDState.FILL_TO_ED)

        @kb.add("N")
        def _(event):
            self.addNextCustomED()

        @kb.add("]")
        @kb.add(">")
        @kb.add(".")
        def _(event):
            self.nextImage()

        @kb.add("[")
        @kb.add("<")
        @kb.add(",")
        def _(event):
            self.prevImage()

        @kb.add("}")
        def _(event):
            self.nextMetro()

        @kb.add("{")
        def _(event):
            self.prevMetro()

        @kb.add("=")
        def _(event):
            self.increaseED()

        @kb.add("-")
        def _(event):
            self.decreaseED()

        @kb.add("+")
        def _(event):
            self.increaseManualED()

        @kb.add("_")
        def _(event):
            self.decreaseManualED()

        @kb.add("`")
        def _(event):
            self.syncImageWithDriver()

        @kb.add("j")
        def _(event):
            self.jumpToIndex()

        @kb.add("c-delete")
        def _(event):
            self.removeLastED()

        @kb.add("up")
        def _(event):
            self.prevManualEDSlot()

        @kb.add("down")
        def _(event):
            self.nextManualEDSlot()

        @kb.add("c-m")
        def _(event):
            self.removeCurrManualEDSlot()

        @kb.add("M")
        def _(event):
            self.addCurrManualED()

        @kb.add("u")
        def _(event):
            self.loadRemoteURL()

        @kb.add("c-c")
        @kb.add("q")
        def _(event):
            self.driver.quit()
            event.app.exit(result=True)

        inputKB = KeyBindings()

        @inputKB.add("escape")
        def _(event):
            self.dismissInput()

        return merge_key_bindings(
            [
                ConditionalKeyBindings(kb, notShowingInput),
                ConditionalKeyBindings(inputKB, showingInput),
            ]
        )

    def top_toolbar(self):
        now = self.store.curr()
        return f"{str(now)}"

    def bottom_toolbar(self):
        now = self.store.curr()
        return f"<{self.store.index:5}> Cur: {self.curr_ed} - Man: {self.manual_eds.currStr} - Img EDs: {list(now.eds)}"

    def current_image(self):
        now = self.store.curr()
        return str(now)

    def skipToLastEntered(self):
        self.store.skipToLastEntered()
        self.updateLastEntered()

    def skipToLastEnteredWithinMetro(self):
        self.store.skipToLastEnteredWithinMetro()
        self.updateLastEntered()

    def updateLastEntered(self):
        last = self.store.curr()
        self.curr_ed = Ed.from_str(list(last.eds)[-1])
        new = next(self.store)

        self.driver.get(new.local_url)

    def addNextED(self):
        curr = self.store.curr()

        if (
            curr.metro_image_index == 0
            and len(list(curr.eds)) == 0
            and self.curr_ed == Ed(1)
        ):
            # Special case: let "n" add 1 if it's really the first one
            self.store.addEDToCurrentImage(Ed(1))
        else:
            self.curr_ed += 1
            self.store.addEDToCurrentImage(self.curr_ed)

    def addNextCustomED(self):
        new = self.manual_eds.incrementCurr()

        if new is not None:
            self.store.addEDToCurrentImage(new)

    def addCurrED(self):
        self.store.addEDToCurrentImage(self.curr_ed)

    def increaseED(self):
        self.curr_ed += 1

    def increaseManualED(self):
        self.manual_eds.incrementCurr()

    def decreaseED(self):
        self.curr_ed -= 1

    def decreaseManualED(self):
        self.manual_eds.decrementCurr()

    def jumpToIndex(self):
        global SHOWING_JUMP_INPUT
        SHOWING_JUMP_INPUT = True

        self.jump_input.text = str(self.store.index)
        get_app().layout.focus(self.jump_input)
        buf = self.jump_input.buffer
        buf.cursor_position = len(self.jump_input.text)

    def accept_jump(self, buffer):
        global SHOWING_JUMP_INPUT
        SHOWING_JUMP_INPUT = False

        raw = self.jump_input.text
        new_index = int(raw)

        if new_index >= 0 and new_index < len(self.store.images):
            self.store.index = new_index
            new = self.store.curr()
            self.driver.get(new.local_url)

        return False  # reset the buffer

    def dismissInput(self):
        global SHOWING_JUMP_INPUT, SHOWING_ED_INPUT

        SHOWING_ED_INPUT = False
        SHOWING_JUMP_INPUT = False

    def removeLastED(self):
        self.store.removeLastED()

    def nextImage(self):
        old = self.store.curr()
        new = next(self.store)
        self.driver.get(new.local_url)

        if old.utp_code != new.utp_code:
            self.curr_ed = Ed(1)
            self.ed_input.text = ""

    def prevImage(self):
        old = self.store.curr()
        new = prev(self.store)
        self.driver.get(new.local_url)

        if old.utp_code != new.utp_code:
            self.curr_ed = Ed.from_str(self.store.largestEDForCurrentMetro())
            self.ed_input.text = ""

    def nextMetro(self):
        new = self.store.nextMetro()
        self.driver.get(new.local_url)
        self.curr_ed = Ed(1)

    def prevMetro(self):
        new = self.store.prevMetro()
        self.driver.get(new.local_url)
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
        self.driver.get(cur.local_url)

    def display_ed_input(self, ed_input_state):
        global SHOWING_ED_INPUT
        SHOWING_ED_INPUT = True

        self.ed_input_state = ed_input_state

        self.ed_input.text = ""
        get_app().layout.focus(self.ed_input)

    def accept_ed(self, buffer):
        global SHOWING_ED_INPUT
        SHOWING_ED_INPUT = False

        new = None
        stripped = self.ed_input.text.strip()

        match self.ed_input_state:
            case EDState.CURRENT_ED:
                new = Ed.from_str(stripped)
                if new:
                    self.curr_ed = new
            case EDState.CUSTOM_ED:
                new = self.manual_eds.addSlot(stripped)
            case EDState.FILL_TO_ED:
                self.fillToED(stripped)

        if new:
            self.store.addEDToCurrentImage(new)

        self.ed_input_state = EDState.NONE
        return False  # reset the buffer

    def prevManualEDSlot(self):
        self.manual_eds.prev()

    def nextManualEDSlot(self):
        self.manual_eds.next()

    def removeCurrManualEDSlot(self):
        self.manual_eds.removeCurr()

    def addCurrManualED(self):
        self.store.addEDToCurrentImage(self.manual_eds.curr())

    def loadRemoteURL(self):
        curr = self.store.curr()

        self.driver.switch_to.new_window()
        self.driver.get(curr.url)

    def fillToED(self, new_ed_string):
        new_ed = Ed.from_str(new_ed_string)

        if new_ed is not None:
            while self.curr_ed < new_ed:
                self.addNextED()


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
