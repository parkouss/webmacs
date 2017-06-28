from ..minibuffer import Prompt, KEYMAP as MKEYMAP, current_minibuffer
from ..keymaps import Keymap
from ..window import current_window
from ..webbuffer import WebBuffer
from ..commands import define_command

KEYMAP = Keymap("i-search", MKEYMAP)


@KEYMAP.define_key("C-s")
def search_next():
    buff = current_window().current_web_view().buffer()
    buff.findText(current_minibuffer().input().text())


@KEYMAP.define_key("C-r")
def search_previous():
    buff = current_window().current_web_view().buffer()
    buff.findText(current_minibuffer().input().text(), WebBuffer.FindBackward)


@KEYMAP.define_key("Return")
def validate():
    buff = current_window().current_web_view().buffer()
    buff.findText("")  # to clear the highlight
    current_minibuffer().close_prompt()


@KEYMAP.define_key("C-g")
@KEYMAP.define_key("Esc")
def cancel():
    scroll_pos = current_minibuffer()._prompt.page_scroll_pos
    validate()
    buff = current_window().current_web_view().buffer()
    buff.set_scroll_pos(*scroll_pos)


class ISearchPrompt(Prompt):
    label = "ISearch:"
    keymap = KEYMAP

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        self.page = current_window().current_web_view().buffer()
        self.page_scroll_pos = (0, 0)
        self.page.async_scroll_pos(
            lambda p: setattr(self, "page_scroll_pos", p))
        minibuffer.input().textChanged.connect(self.on_text_edited)

    def on_text_edited(self, text):
        self.page.findText(text)
        if not text:
            self.page.set_scroll_pos(*self.page_scroll_pos)

    def close(self):
        self.minibuffer.input().textChanged.disconnect(self.on_text_edited)
        Prompt.close(self)


@define_command("i-search", prompt=ISearchPrompt)
def i_search_forward(prompt):
    pass
