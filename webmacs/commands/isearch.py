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

from ..minibuffer import Prompt, KEYMAP as MKEYMAP
from ..keymaps import Keymap
from ..keyboardhandler import local_keymap
from ..webbuffer import WebBuffer
from ..commands import define_command
from ..commands import caret_browsing as caret_browsing_commands
from ..keymaps.caret_browsing import KEYMAP as CARET_BROWSING_KEYMAP

KEYMAP = Keymap("i-search", MKEYMAP)


@KEYMAP.define_key("C-s")
def search_next(ctx):
    prompt = ctx.minibuffer.prompt()
    prompt.set_isearch_direction(0)
    prompt.find_text()


@KEYMAP.define_key("C-r")
def search_previous(ctx):
    prompt = ctx.minibuffer.prompt()
    prompt.set_isearch_direction(WebBuffer.FindBackward)
    prompt.find_text()


@KEYMAP.define_key("Return")
def validate(ctx):
    buff = ctx.buffer
    buff.findText("")  # to clear the highlight
    ctx.minibuffer.close_prompt()


@KEYMAP.define_key("C-g")
@KEYMAP.define_key("Esc")
def cancel(ctx):
    prompt = ctx.minibuffer.prompt()
    scroll_pos = prompt.page_scroll_pos
    validate(ctx)
    prompt.set_page_scroll_pos(scroll_pos)


class ISearchPrompt(Prompt):
    label = "ISearch:"
    keymap = KEYMAP

    isearch_direction = 0  # forward

    def enable(self, minibuffer):
        self._caret_browsing = local_keymap() == CARET_BROWSING_KEYMAP
        if self._caret_browsing:
            caret_browsing_commands.shutdown()
        Prompt.enable(self, minibuffer)
        self._update_label()
        self.page = self.ctx.buffer
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
        if self._caret_browsing:
            caret_browsing_commands.init()


@define_command("i-search-forward", prompt=ISearchPrompt)
def i_search_forward(ctx):
    """
    Begin an incremental search (forward).
    """
    pass


class ISearchPromptBackward(ISearchPrompt):
    isearch_direction = WebBuffer.FindBackward


@define_command("i-search-backward", prompt=ISearchPromptBackward)
def i_search_backward(ctx):
    """
    Begin an incremental search (backward).
    """
    pass
