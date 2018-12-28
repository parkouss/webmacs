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

from . import define_command

WORD_SEPS = "#/.-_:"


def move_next_word(edit, forward, mark):
    action = edit.cursorWordForward if forward else edit.cursorWordBackward

    cursor = edit.cursorPosition()
    txt = edit.text()

    while True:
        action(mark)
        nc = edit.cursorPosition()
        if nc == cursor:
            break
        cursor = nc

        if forward:
            nc -= 1

        if txt[nc] not in WORD_SEPS:
            break


@define_command("minibuffer-select-complete")
def complete(ctx):
    """
    Complete completion.
    """
    input = ctx.minibuffer.input()

    if not input.popup().isVisible():
        input.show_completions()
    else:
        input.select_next_completion()


@define_command("minibuffer-select-next")
def next_completion(ctx):
    """
    Select next completion entry.
    """
    ctx.minibuffer.input().select_next_completion()


@define_command("minibuffer-select-prev")
def previous_completion(ctx):
    """
    Select previous completion entry.
    """
    ctx.minibuffer.input().select_next_completion(False)


@define_command("minibuffer-select-first")
def first_complqetion(ctx):
    """
    Select first completion entry.
    """
    ctx.minibuffer.input().select_first_completion()


@define_command("minibuffer-select-last")
def last_completion(ctx):
    """
    Select last completion entry.
    """
    ctx.minibuffer.input().select_last_completion()


@define_command("minibuffer-select-next-page")
def next_page_completion(ctx):
    """
    Move one page down in completion entry list.
    """
    ctx.minibuffer.input().select_next_page_completion()


@define_command("minibuffer-select-prev-page")
def previous_page_completion(ctx):
    """
    Move one page up in completion entry list.
    """
    ctx.minibuffer.input().select_next_page_completion(False)


def _prompt_history(ctx, func):
    minibuff = ctx.minibuffer
    history = minibuff.prompt().history
    if history:
        if history.in_user_value():
            history.set_user_value(minibuff.input().text())
        text = func(history)
        if text is not None:
            minibuff.input().setText(text)


@define_command("minibuffer-history-next")
def prompt_history_next(ctx):
    """
    Insert next history value.
    """
    _prompt_history(ctx, lambda h: h.get_next())


@define_command("minibuffer-history-prev")
def prompt_history_previous(ctx):
    """
    Insert previous history value.
    """
    _prompt_history(ctx, lambda h: h.get_previous())


@define_command("minibuffer-validate")
def edition_finished(ctx):
    """
    Validate input in minibuffer.
    """
    minibuffer_input = ctx.minibuffer.input()
    minibuffer_input.complete()
    minibuffer_input.popup().hide()
    minibuffer_input.returnPressed.emit()


@define_command("minibuffer-abort")
def cancel(ctx):
    """
    Abort edition of the minibuffer.
    """
    minibuffer = ctx.minibuffer
    input = minibuffer.input()
    if input.popup().isVisible():
        input.popup().hide()
    minibuffer.close_prompt()


@define_command("minibuffer-delete-backward-word")
def clean_aindent_bsunindent(ctx):
    """
    Delete the word backward.
    """
    edit = ctx.minibuffer.input()
    if edit.hasSelectedText():
        edit.deselect()

    move_next_word(edit, False, True)
    if edit.hasSelectedText():
        edit.del_()


@define_command("minibuffer-mark")
def set_mark(ctx):
    """
    Set or unset the edit mark.
    """
    minibuffer_input = ctx.minibuffer.input()
    if not minibuffer_input.set_mark():
        minibuffer_input.deselect()


@define_command("minibuffer-forward-char")
def forward_char(ctx):
    """
    Move one character forward.
    """
    edit = ctx.minibuffer.input()
    edit.cursorForward(edit.mark(), 1)


@define_command("minibuffer-backward-char")
def backward_char(ctx):
    """
    Move one character backward.
    """
    edit = ctx.minibuffer.input()
    edit.cursorBackward(edit.mark(), 1)


@define_command("minibuffer-forward-word")
def forward_word(ctx):
    """
    Move one word forward.
    """
    edit = ctx.minibuffer.input()
    move_next_word(edit, True, edit.mark())


@define_command("minibuffer-backward-word")
def backward_word(ctx):
    """
    Move one word backward.
    """
    edit = ctx.minibuffer.input()
    move_next_word(edit, False, edit.mark())


@define_command("minibuffer-copy")
def copy(ctx):
    """
    Copy selected text in the minibuffer.
    """
    edit = ctx.minibuffer.input()
    edit.copy()
    edit.deselect()


@define_command("minibuffer-cut")
def cut(ctx):
    """
    Cut selected text in the minibuffer.
    """
    ctx.minibuffer.input().cut()


@define_command("minibuffer-paste")
def paste(ctx):
    """
    Paste text in the minibuffer.
    """
    ctx.minibuffer.input().paste()


@define_command("minibuffer-delete-forward-char")
def delete_char(ctx):
    """
    Delete forward character.
    """
    ctx.minibuffer.input().del_()


@define_command("minibuffer-delete-forward-word")
def delete_word(ctx):
    """
    Delete forward word.
    """
    edit = ctx.minibuffer.input()
    if edit.hasSelectedText():
        edit.deselect()

    move_next_word(edit, True, True)
    if edit.hasSelectedText():
        edit.del_()


@define_command("minibuffer-beginning-of-line")
def beginning_of_line(ctx):
    """
    Move cursor to the beginning of the line.
    """
    edit = ctx.minibuffer.input()
    edit.home(edit.mark())


@define_command("minibuffer-end-of-line")
def end_of_line(ctx):
    """
    Move cursor to the end of the line.
    """
    edit = ctx.minibuffer.input()
    edit.end(edit.mark())


@define_command("minibuffer-undo")
def undo(ctx):
    """
    Undo in the minibuffer.
    """
    ctx.minibuffer.input().undo()


@define_command("minibuffer-redo")
def redo(ctx):
    """
    Redo in the minibuffer.
    """
    ctx.minibuffer.input().redo()
