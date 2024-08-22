import random

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
from prompt_toolkit.widgets import CheckboxList

show_input = False


@Condition
def inputHidden():
    return not show_input


@Condition
def inputShown():
    return show_input


class Annotator:
    def __init__(self):
        self.counter = 1
        self.string = ""

        bindings = self.setupBindings()

        self.remove_list = CheckboxList(
            values=[
                ("a", "a"),
            ]
        )
        self.remove_list.multiple_selection = True

        application = Application(
            key_bindings=bindings, full_screen=False, layout=self.layout()
        )
        application.run()

    def layout(self):
        def makeLayout():
            global show_input

            return HSplit(
                [
                    Window(FormattedTextControl(self.status()), height=1),
                    ConditionalContainer(content=self.remove_list, filter=show_input),
                ]
            )

        return Layout(DynamicContainer(makeLayout), focused_element=self.remove_list)

    def setupBindings(self):
        kb = KeyBindings()

        @kb.add("+")
        def _(event):
            self.addOne()

        @kb.add("r")
        def _(event):
            self.showInput()

        @kb.add("c-c")
        @kb.add("q")
        def _(event):
            get_app().exit(result=True)

        input_kb = KeyBindings()

        @input_kb.add("enter")
        @input_kb.add("q")
        def _(event):
            self.dismissInput()

        return merge_key_bindings(
            [
                ConditionalKeyBindings(kb, inputHidden),
                ConditionalKeyBindings(input_kb, inputShown),
            ]
        )

    def addOne(self):
        self.counter += 1

    def status(self):
        return f"{self.counter} - '{self.string}'"

    def showInput(self):
        global show_input
        show_input = True

        items = random.sample(range(1000), 4)
        self.remove_list.values = [(i, f"{i}") for i in items]
        self.remove_list.current_values = []
        self.remove_list._selected_index = 0

    def dismissInput(self):
        global show_input
        show_input = False

        get_app().invalidate()

        with open("/tmp/remove.txt", "w") as f:
            print("Items to be removed:", self.remove_list.current_values, file=f)


if __name__ == "__main__":
    Annotator()
