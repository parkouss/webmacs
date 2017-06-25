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


@define_command("follow", prompt=FollowPrompt)
def follow(prompt):
    pass


@KEYMAP.define_key("C-g")
@KEYMAP.define_key("Esc")
def cancel():
    current_buffer().stop_select_browser_objects()
    current_minibuffer().close_prompt()
