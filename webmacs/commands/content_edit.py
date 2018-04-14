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

from . import define_command


def run_js(ctx, cmd):
    ctx.buffer.runJavaScript(cmd, QWebEngineScript.ApplicationWorld)


@define_command("content-edit-cancel")
def cancel(ctx):
    """
    If a mark is active, clear that but keep the focus. If there is no
    mark active, then just unfocus the editable js object.
    """
    run_js(ctx, """
    var e = getActiveElement();
    if (has_any_mark(e)) {
        // be sure that we have a mark, then unset it.
        text_marks[e] = true;
        set_or_unset_mark(e);
    } else {
        e.blur();
    }
    """)


@define_command("content-edit-set-mark")
def set_mark(ctx):
    """
    Set or clear the mark in browser text field.
    """
    run_js(ctx, "set_or_unset_mark(getActiveElement());")


@define_command("content-edit-forward-char")
def forward_char(ctx):
    """
    Move one character forward in browser text field.
    """
    run_js(ctx, "forward_char(getActiveElement());")


@define_command("content-edit-backward-char")
def backward_char(ctx):
    """
    Move one character backward in browser text field.
    """
    run_js(ctx, "backward_char(getActiveElement());")


@define_command("content-edit-forward-word")
def forward_word(ctx):
    """
    Move one word forward in browser text field.
    """
    run_js(ctx, "forward_word(getActiveElement());")


@define_command("content-edit-backward-word")
def backward_word(ctx):
    """
    Move one word backward in browser text field.
    """
    run_js(ctx, "backward_word(getActiveElement());")


@define_command("content-edit-beginning-of-line")
def move_beginning_of_line(ctx):
    """
    Move to the beginning of the line in browser text field.
    """
    run_js(ctx, "move_beginning_of_line(getActiveElement());")


@define_command("content-edit-end-of-line")
def move_end_of_line(ctx):
    """
    Move to the end of the line in browser text field.
    """
    run_js(ctx, "move_end_of_line(getActiveElement());")


@define_command("content-edit-delete-forward-char")
def delete_char(ctx):
    """
    Delete one character forward in browser text field.
    """
    run_js(ctx, "delete_char(getActiveElement());")


@define_command("content-edit-delete-forward-word")
def delete_word(ctx):
    """
    Delete one word forward in browser text field.
    """
    run_js(ctx, "delete_word(getActiveElement());")


@define_command("content-edit-delete-backward-word")
def delete_word_backward(ctx):
    """
    Delete one word backward in browser text field.
    """
    run_js(ctx, "delete_word_backward(getActiveElement());")


@define_command("content-edit-copy")
def copy(ctx):
    """
    Copy browser text field selection in the clipboard.
    """
    run_js(ctx, "copy_text(getActiveElement());")


@define_command("content-edit-cut")
def cut(ctx):
    """
    Cut browser text field selection in the clipboard.
    """
    run_js(ctx, "copy_text(getActiveElement(), true);")


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
