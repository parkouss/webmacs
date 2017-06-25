from PyQt5.QtCore import QEvent, Qt

from .minibuffer import Prompt, KEYMAP as MKEYMAP, current_minibuffer
from .keymap import Keymap
from .webbuffer import current_buffer
from .commands import define_command
from .application import Application


KEYMAP = Keymap("i-search", MKEYMAP)


class FollowPrompt(Prompt):
    label = "follow:"
    keymap = KEYMAP

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        self.page = current_buffer()
        selector = "a[href], input:not([hidden]), textarea:not([hidden])"
        self.page.start_select_browser_objects(selector)
        self.numbers = ""
        minibuffer.input().textChanged.connect(self.on_text_edited)
        self.browser_object_activated = {}
        Application.INSTANCE.sock_client.content_handler \
                                        .browserObjectActivated.connect(
                                            self.on_browser_object_activated
                                        )
        minibuffer.input().installEventFilter(self)

    def on_browser_object_activated(self, bo):
        self.browser_object_activated = bo

    def on_text_edited(self, text):
        self.page.filter_browser_objects(text)

    def _update_label(self):
        label = self.__class__.label
        if self.numbers:
            label = label[:-1] + (" #%s:" % self.numbers)
        self.minibuffer.label.setText(label)

    def eventFilter(self, obj, event):
        numbers = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0")
        if event.type() == QEvent.KeyPress:
            text = event.text()
            if text in numbers:
                self.numbers += text
                self.page.select_visible_hint(self.numbers)
                self._update_label()
                return True
            elif not event.key() in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt,
                                     Qt.Key_Meta, Qt.Key_unknown):
                self.numbers = ""
                self._update_label()
        return Prompt.eventFilter(self, obj, event)


@define_command("follow", prompt=FollowPrompt)
def follow(prompt):
    url = prompt.browser_object_activated.get("url")
    if url:
        prompt.page.load(url)
    else:
        prompt.page.focus_active_browser_object()
        current_buffer().stop_select_browser_objects()


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
