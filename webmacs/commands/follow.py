from PyQt5.QtCore import QEvent, Qt

from ..minibuffer import Prompt, KEYMAP as MKEYMAP
from ..keymaps import Keymap
from ..commands import define_command
from .. import current_minibuffer, current_buffer


KEYMAP = Keymap("follow", MKEYMAP)


class FollowPrompt(Prompt):
    label = "follow:"
    keymap = KEYMAP

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        self.page = current_buffer()
        # took from conkeror
        selector = (
            "//*[@onclick or @onmouseover or @onmousedown or @onmouseup or "
            "@oncommand or @role='link' or @role='button' or @role='menuitem']"
            " | //input[not(@type='hidden')] | //a[@href] | //area"
            " | //iframe | //textarea | //button | //select"
            " | //*[@contenteditable = 'true']"
            " | //xhtml:*[@onclick or @onmouseover or @onmousedown or"
            " @onmouseup or @oncommand or @role='link' or @role='button' or"
            " @role='menuitem'] | //xhtml:input[not(@type='hidden')]"
            " | //xhtml:a[@href] | //xhtml:area | //xhtml:iframe"
            " | //xhtml:textarea | //xhtml:button | //xhtml:select"
            " | //xhtml:*[@contenteditable = 'true'] | //svg:a"
        )
        self.page.start_select_browser_objects(selector)
        self.numbers = ""
        minibuffer.input().textChanged.connect(self.on_text_edited)
        self.browser_object_activated = {}
        self.page.content_handler.browserObjectActivated.connect(
            self.on_browser_object_activated
        )
        minibuffer.input().installEventFilter(self)

    def on_browser_object_activated(self, bo):
        self.browser_object_activated = bo
        self.minibuffer.input().set_right_italic_text(bo.get("url", ""))

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
