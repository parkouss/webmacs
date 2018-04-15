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

from PyQt5.QtWebEngineWidgets import QWebEngineScript
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QKeyEvent

from ..application import app
from . import define_command


def send_raw_key(ctx, key, with_ctrl=False, auto_shift=True):
    a = app()
    modifiers = Qt.NoModifier
    if auto_shift:
        if ctx.buffer.hasSelection() and not ctx.buffer.text_edit_mark:
            ctx.buffer.set_text_edit_mark(True)
        if ctx.buffer.text_edit_mark:
            modifiers |= Qt.ShiftModifier
    if with_ctrl:
        modifiers |= Qt.ControlModifier

    a.postEvent(ctx.sender, QKeyEvent(QEvent.KeyPress, key, modifiers))
    a.postEvent(ctx.sender, QKeyEvent(QEvent.KeyRelease, key, modifiers))


def run_js(ctx, cmd, cb=None):
    if cb:
        ctx.buffer.runJavaScript(cmd, QWebEngineScript.ApplicationWorld, cb)
    else:
        ctx.buffer.runJavaScript(cmd, QWebEngineScript.ApplicationWorld)


@define_command("content-edit-cancel")
def cancel(ctx):
    """
    If a mark is active, clear that but keep the focus. If there is no
    mark active, then just unfocus the editable js object.
    """
    if ctx.buffer.hasSelection():
        run_js(ctx, "clear_mark(getActiveElement());")
    else:
        run_js(ctx, "getActiveElement().blur();")
    ctx.buffer.set_text_edit_mark(False)


@define_command("content-edit-set-mark")
def set_mark(ctx):
    """
    Set or clear the mark in browser text field.
    """
    if ctx.buffer.hasSelection():
        run_js(ctx, "clear_mark(getActiveElement());")
    ctx.buffer.set_text_edit_mark(
        not ctx.buffer.text_edit_mark
    )


@define_command("content-edit-forward-char")
def forward_char(ctx):
    """
    Move one character forward in browser text field.
    """
    send_raw_key(ctx, Qt.Key_Right)


@define_command("content-edit-backward-char")
def backward_char(ctx):
    """
    Move one character backward in browser text field.
    """
    send_raw_key(ctx, Qt.Key_Left)


@define_command("content-edit-forward-word")
def forward_word(ctx):
    """
    Move one word forward in browser text field.
    """
    send_raw_key(ctx, Qt.Key_Right, with_ctrl=True)


@define_command("content-edit-backward-word")
def backward_word(ctx):
    """
    Move one word backward in browser text field.
    """
    send_raw_key(ctx, Qt.Key_Left, with_ctrl=True)


@define_command("content-edit-beginning-of-line")
def move_beginning_of_line(ctx):
    """
    Move to the beginning of the line in browser text field.
    """
    send_raw_key(ctx, Qt.Key_Home)


@define_command("content-edit-end-of-line")
def move_end_of_line(ctx):
    """
    Move to the end of the line in browser text field.
    """
    send_raw_key(ctx, Qt.Key_End)


def delete_selection(ctx):
    def wrapper(_):
        send_raw_key(ctx, Qt.Key_Backspace, auto_shift=False)
        ctx.buffer.set_text_edit_mark(False)
    return wrapper


@define_command("content-edit-delete-forward-char")
def delete_char(ctx):
    """
    Delete one character forward in browser text field.
    """
    run_js(
        ctx,
        "select_text(getActiveElement(), 'forward', 'character');",
        delete_selection(ctx),
    )


@define_command("content-edit-delete-forward-word")
def delete_word(ctx):
    """
    Delete one word forward in browser text field.
    """
    run_js(
        ctx,
        "select_text(getActiveElement(), 'forward', 'word');",
        delete_selection(ctx),
    )


@define_command("content-edit-delete-backward-word")
def delete_word_backward(ctx):
    """
    Delete one word backward in browser text field.
    """
    run_js(
        ctx,
        "select_text(getActiveElement(), 'backward', 'word');",
        delete_selection(ctx),
    )


@define_command("content-edit-copy")
def copy(ctx):
    """
    Copy browser text field selection in the clipboard.
    """
    ctx.buffer.set_text_edit_mark(False)
    run_js(ctx, "copy_text(getActiveElement(), true);")


@define_command("content-edit-cut")
def cut(ctx):
    """
    Cut browser text field selection in the clipboard.
    """
    run_js(ctx, "copy_text(getActiveElement());",
           delete_selection(ctx))


@define_command("content-edit-upcase-forward-word")
def upcase_word(ctx):
    """
    Upcase the word forward in browser text field.
    """
    run_js(ctx, "upcase_word(getActiveElement());")


@define_command("content-edit-downcase-forward-word")
def downcase_word(ctx):
    """
    Downcase the word forward in browser text field.
    """
    run_js(ctx, "downcase_word(getActiveElement());")


@define_command("content-edit-capitalize-forward-word")
def capitalize_word(ctx):
    """
    Capitalize the word forward in browser text field.
    """
    run_js(ctx, "capitalize_word(getActiveElement());")


@define_command("content-edit-open-external-editor")
def open_external_editor(ctx):
    """
    Open an external editor to change the text field content.
    """
    run_js(ctx, "external_editor_open(getActiveElement())");
