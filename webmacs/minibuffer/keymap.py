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

from ..keymaps import Keymap

KEYMAP = Keymap("minibuffer")


@KEYMAP.define_key("Tab")
def complete(ctx):
    input = ctx.minibuffer.input()

    if not input.popup().isVisible():
        input.show_completions()
    else:
        input.select_next_completion()


@KEYMAP.define_key("C-n")
@KEYMAP.define_key("Down")
def next_completion(ctx):
    ctx.minibuffer.input().select_next_completion()


@KEYMAP.define_key("C-p")
@KEYMAP.define_key("Up")
def previous_completion(ctx):
    ctx.minibuffer.input().select_next_completion(False)


def _prompt_history(ctx, func):
    minibuff = ctx.minibuffer
    history = minibuff.prompt().history
    if history:
        if history.in_user_value():
            history.set_user_value(minibuff.input().text())
        text = func(history)
        if text is not None:
            minibuff.input().setText(text)


@KEYMAP.define_key("M-n")
def prompt_history_next(ctx):
    _prompt_history(ctx, lambda h: h.get_next())


@KEYMAP.define_key("M-p")
def prompt_history_previous(ctx):
    _prompt_history(ctx, lambda h: h.get_previous())


@KEYMAP.define_key("Return")
def edition_finished(ctx):
    minibuffer_input = ctx.minibuffer.input()
    minibuffer_input.complete()
    minibuffer_input.popup().hide()
    minibuffer_input.returnPressed.emit()


@KEYMAP.define_key("C-g")
@KEYMAP.define_key("Esc")
def cancel(ctx):
    minibuffer = ctx.minibuffer
    input = minibuffer.input()
    if input.popup().isVisible():
        input.popup().hide()
    minibuffer.close_prompt()


@KEYMAP.define_key("M-Backspace")
def clean_aindent_bsunindent(ctx):
    edit = ctx.minibuffer.input()
    if edit.hasSelectedText():
        edit.deselect()

    edit.cursorWordBackward(True)
    if edit.hasSelectedText():
        edit.del_()


@KEYMAP.define_key("C-Space")
def set_mark(ctx):
    minibuffer_input = ctx.minibuffer.input()
    if not minibuffer_input.set_mark():
        minibuffer_input.deselect()


@KEYMAP.define_key("C-f")
@KEYMAP.define_key("Right")
def forward_char(ctx):
    edit = ctx.minibuffer.input()
    edit.cursorForward(edit.mark(), 1)


@KEYMAP.define_key("C-b")
@KEYMAP.define_key("Left")
def backward_char(ctx):
    edit = ctx.minibuffer.input()
    edit.cursorBackward(edit.mark(), 1)


@KEYMAP.define_key("M-f")
@KEYMAP.define_key("M-Right")
def forward_word(ctx):
    edit = ctx.minibuffer.input()
    edit.cursorWordForward(edit.mark())


@KEYMAP.define_key("M-b")
@KEYMAP.define_key("M-Left")
def backward_word(ctx):
    edit = ctx.minibuffer.input()
    edit.cursorWordBackward(edit.mark())


@KEYMAP.define_key("M-w")
def copy(ctx):
    edit = ctx.minibuffer.input()
    edit.copy()
    edit.deselect()


@KEYMAP.define_key("C-w")
def cut(ctx):
    ctx.minibuffer.input().cut()


@KEYMAP.define_key("C-y")
def paste(ctx):
    ctx.minibuffer.input().paste()


@KEYMAP.define_key("C-d")
def delete_char(ctx):
    ctx.minibuffer.input().del_()


@KEYMAP.define_key("M-d")
def delete_word(ctx):
    edit = ctx.minibuffer.input()
    if edit.hasSelectedText():
        edit.deselect()

    edit.cursorWordBackward(True)
    if edit.hasSelectedText():
        edit.del_()


@KEYMAP.define_key("C-a")
def beginning_of_line(ctx):
    edit = ctx.minibuffer.input()
    edit.home(edit.mark())


@KEYMAP.define_key("C-e")
def end_of_line(ctx):
    edit = ctx.minibuffer.input()
    edit.end(edit.mark())
