from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
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
from prompt_toolkit.widgets import SearchToolbar, TextArea

show_input = False


@Condition
def inputHidden():
    return not show_input


@Condition
def inputShowing():
    return show_input


class Annotator:
    def __init__(self):
        self.counter = 1
        self.string = ""

        bindings = self.setupBindings()

        search_field = SearchToolbar()
        self.input = TextArea(height=1, prompt="put it in> ", search_field=search_field)
        self.input.accept_handler = self.acceptInput

        application = Application(
            key_bindings=bindings,
            full_screen=False,
            layout=self.layout(),
        )
        application.timeoutlen = 0
        application.ttimeoutlen = 0
        application.run()

    def layout(self):
        def makeLayout():
            return HSplit(
                [
                    Window(FormattedTextControl(self.status()), height=1),
                    ConditionalContainer(content=self.input, filter=inputShowing),
                ]
            )

        return Layout(DynamicContainer(makeLayout), focused_element=self.input)

    def setupBindings(self):
        kb = KeyBindings()

        @kb.add("+")
        def _(event):
            self.addOne()

        @kb.add("/")
        def _(event):
            self.showInput()

        @kb.add("c-c")
        @kb.add("q")
        def _(event):
            get_app().exit(result=True)

        inputKB = KeyBindings()

        @inputKB.add("escape")
        def _(event):
            self.dismissInput(event)

        return merge_key_bindings(
            [
                ConditionalKeyBindings(kb, inputHidden),
                ConditionalKeyBindings(inputKB, inputShowing),
            ]
        )

    def addOne(self):
        self.counter += 1

    def status(self):
        return f"{self.counter} - '{self.string}'"

    def showInput(self):
        global show_input
        show_input = True

        # Clear field of any stray characters since last Enter
        self.input.text = ""

    def acceptInput(self, buffer):
        self.string = self.input.text

        with open("/tmp/entry_mre.log", "a") as log:
            print(f"acceptInput: {self.string}", file=log)

        global show_input
        show_input = False

    def dismissInput(self, event):
        global show_input

        if show_input:
            show_input = False


if __name__ == "__main__":
    Annotator()
