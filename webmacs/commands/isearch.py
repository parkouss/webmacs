from ..minibuffer import Prompt, KEYMAP as MKEYMAP, current_minibuffer
from ..keymaps import Keymap
from ..window import current_window
from ..webbuffer import WebBuffer
from ..commands import define_command

KEYMAP = Keymap("i-search", MKEYMAP)


@KEYMAP.define_key("C-s")
def search_next():
    prompt = current_minibuffer().prompt()
    prompt.set_isearch_direction(0)
    prompt.find_text()


@KEYMAP.define_key("C-r")
def search_previous():
    prompt = current_minibuffer().prompt()
    prompt.set_isearch_direction(WebBuffer.FindBackward)
    prompt.find_text()


@KEYMAP.define_key("Return")
def validate():
    buff = current_window().current_web_view().buffer()
    buff.findText("")  # to clear the highlight
    current_minibuffer().close_prompt()


@KEYMAP.define_key("C-g")
@KEYMAP.define_key("Esc")
def cancel():
    prompt = current_minibuffer().prompt()
    scroll_pos = prompt.page_scroll_pos
    validate()
    prompt.set_page_scroll_pos(scroll_pos)


class ISearchPrompt(Prompt):
    label = "ISearch:"
    keymap = KEYMAP

    isearch_direction = 0  # forward

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        self._update_label()
        self.page = current_window().current_web_view().buffer()
        self.page_scroll_pos = (0, 0)
        self.page.async_scroll_pos(
            lambda p: setattr(self, "page_scroll_pos", p))
        minibuffer.input().textChanged.connect(self.on_text_edited)

    def set_isearch_direction(self, direction):
        self.isearch_direction = direction
        self._update_label()

    def set_page_scroll_pos(self, page_scroll_pos):
        self.page.set_scroll_pos(*page_scroll_pos)

    def find_text(self):
        if self.isearch_direction:
            self.page.findText(self.minibuffer.input().text(),
                               self.isearch_direction)
        else:
            self.page.findText(self.minibuffer.input().text())

    def on_text_edited(self, text):
        self.find_text()
        if not self.minibuffer.input().text():
            self.set_page_scroll_pos(self.page_scroll_pos)

    def _update_label(self):
        direction = "forward" if self.isearch_direction == 0 else "backward"
        self.minibuffer.label.setText("ISearch (%s):" % direction)

    def close(self):
        self.minibuffer.input().textChanged.disconnect(self.on_text_edited)
        Prompt.close(self)


@define_command("i-search-forward", prompt=ISearchPrompt)
def i_search_forward(prompt):
    pass


class ISearchPromptBackward(ISearchPrompt):
    isearch_direction = WebBuffer.FindBackward


@define_command("i-search-backward", prompt=ISearchPromptBackward)
def i_search_backward(prompt):
    pass
