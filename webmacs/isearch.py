from .minibuffer import Prompt, KEYMAP as MKEYMAP, current_minibuffer
from .keymap import Keymap
from .window import current_window
from .webbuffer import WebBuffer

KEYMAP = Keymap("i-search", MKEYMAP)


@KEYMAP.define_key("C-s")
def search_next():
    buff = current_window().current_web_view().buffer()
    buff.findText(current_minibuffer().input().text())


@KEYMAP.define_key("C-r")
def search_previous():
    buff = current_window().current_web_view().buffer()
    buff.findText(current_minibuffer().input().text(), WebBuffer.FindBackward)


@KEYMAP.define_key("C-g")
@KEYMAP.define_key("Esc")
def cancel():
    buff = current_window().current_web_view().buffer()
    buff.findText("")  # to clear the highlight
    current_minibuffer().close_prompt()


class ISearchPrompt(Prompt):
    label = "ISearch:"
    keymap = KEYMAP

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        self.page = current_window().current_web_view().buffer()
        minibuffer.input().textChanged.connect(self.on_text_edited)

    def on_text_edited(self, text):
        self.page.findText(text)

    def close(self):
        # calling setFocus() on the view is required, else the view is scrolled
        # to the top automatically. But we don't even get a focus in event;
        self.minibuffer.parent().current_web_view().setFocus()
        self.minibuffer.input().textChanged.disconnect(self.on_text_edited)
        Prompt.close(self)
