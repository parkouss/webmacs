from .minibuffer import Prompt, KEYMAP as MKEYMAP, current_minibuffer
from .keymap import Keymap
from .webbuffer import current_buffer
from .commands import define_command


KEYMAP = Keymap("i-search", MKEYMAP)


class FollowPrompt(Prompt):
    label = "follow:"
    keymap = KEYMAP

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        self.page = current_buffer()
        selector = "a[href], input:not([hidden]), textarea:not([hidden])"
        self.page.start_select_browser_objects(selector)
        minibuffer.input().textChanged.connect(self.on_text_edited)

    def on_text_edited(self, text):
        self.page.filter_browser_objects(text)


@define_command("follow", prompt=FollowPrompt)
def follow(prompt):
    pass


@KEYMAP.define_key("C-g")
@KEYMAP.define_key("Esc")
def cancel():
    current_buffer().stop_select_browser_objects()
    current_minibuffer().close_prompt()


@KEYMAP.define_key("C-n")
@KEYMAP.define_key("Down")
def next_completion():
    current_buffer().select_nex_browser_object()


@KEYMAP.define_key("C-p")
@KEYMAP.define_key("Up")
def previous_completion():
    current_buffer().select_nex_browser_object(False)
