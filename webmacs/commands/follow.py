# This file is part of webmacs.
#
# webmacs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# webmacs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with webmacs.  If not, see <http://www.gnu.org/licenses/>.

from PyQt5.QtCore import QEvent, Qt

from ..minibuffer import Prompt, KEYMAP as MKEYMAP
from ..keymaps import Keymap
from ..commands import define_command
from ..application import app
from .prompt_helper import PromptNewBuffer


KEYMAP = Keymap("hint", MKEYMAP)

# took from conkeror
SELECTOR_CLICKABLE = (
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

SELECTOR_LINK = "//a[@href]"


class HintPrompt(Prompt):
    keymap = KEYMAP
    hint_selector = ""

    def enable(self, minibuffer):
        super(HintPrompt, self).enable(minibuffer)
        self.page = self.ctx.buffer
        self.page.start_select_browser_objects(self.hint_selector)
        self.numbers = ""
        minibuffer.input().textChanged.connect(self.on_text_edited)
        self.browser_object_activated = {}
        self.page.content_handler.browserObjectActivated.connect(
            self.on_browser_object_activated
        )
        minibuffer.input().installEventFilter(self)

    def close(self):
        self.page.stop_select_browser_objects()
        super(HintPrompt, self).close()

    def on_browser_object_activated(self, bo):
        self.browser_object_activated = bo
        self.minibuffer.input().set_right_italic_text(bo.get("url", ""))

    def on_text_edited(self, text):
        self.page.filter_browser_objects(text)

    def _update_label(self):
        label = self.label
        if self.numbers:
            label = label + (" #%s" % self.numbers)
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
            elif not event.key() in (
                    Qt.Key_Control,
                    Qt.Key_Shift,
                    Qt.Key_Alt,
                    Qt.Key_Meta,
                    Qt.Key_unknown,
                    Qt.Key_Return,
                    ):
                self.numbers = ""
                self._update_label()
        return super(HintPrompt, self).eventFilter(obj, event)


class FollowPrompt(HintPrompt):
    label = "follow:"
    hint_selector = SELECTOR_CLICKABLE

    def enable(self, minibuffer):
        self.new_buffer = PromptNewBuffer(self.ctx)
        if self.new_buffer:
            self.hint_selector = SELECTOR_LINK
        super(FollowPrompt, self).enable(minibuffer)
        self.new_buffer.enable(minibuffer)
        if self.new_buffer:
            self.label = minibuffer.label.text()


class CopyLinkPrompt(HintPrompt):
    label = "copy link:"
    hint_selector = SELECTOR_LINK

    def eventFilter(self, obj, event):
        res = super(CopyLinkPrompt, self).eventFilter(obj, event)
        if self.numbers == "0":
            self.minibuffer.input().set_right_italic_text(
                self.page.url().toString()
            )
        return res


@define_command("follow", prompt=FollowPrompt)
def follow(ctx):
    """
    Hint links in the buffer and follow them on selection.
    """
    prompt = ctx.prompt
    buff = prompt.page
    buff.stop_select_browser_objects()
    if not prompt.new_buffer:
        buff.focus_active_browser_object()
    elif "url" in prompt.browser_object_activated:
        prompt.new_buffer.get_buffer().load(
            prompt.browser_object_activated["url"]
        )


@define_command("copy-link", prompt=CopyLinkPrompt)
def copy_link(ctx):
    """
    Hint links in the buffer to copy them.
    """
    prompt = ctx.prompt
    buff = prompt.page
    url = None
    buff.stop_select_browser_objects()

    if prompt.numbers == "0":
        # special case, copy current url
        url = buff.url().toString()
    else:
        bo = prompt.browser_object_activated
        if "url" in bo:
            url = bo["url"]

    if url:
        app().clipboard().setText(url)
        prompt.minibuffer.show_info("Copied: {}".format(url))


@KEYMAP.define_key("C-g")
@KEYMAP.define_key("Esc")
def cancel(ctx):
    ctx.buffer.stop_select_browser_objects()
    ctx.minibuffer.close_prompt()


@KEYMAP.define_key("C-n")
@KEYMAP.define_key("Down")
def next_completion(ctx):
    ctx.buffer.select_nex_browser_object()


@KEYMAP.define_key("C-p")
@KEYMAP.define_key("Up")
def previous_completion(ctx):
    ctx.buffer.select_nex_browser_object(False)
