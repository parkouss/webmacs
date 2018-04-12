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

from . import CONTENT_EDIT_KEYMAP as KEYMAP


def run_js(ctx, cmd):
    ctx.buffer.runJavaScript(cmd, QWebEngineScript.ApplicationWorld)


@KEYMAP.define_key("C-g")
def cancel(ctx):
    # if a mark is active, clear that but keep the focus. If there is no mark
    # active, then just unfocus the editable js object.
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


KEYMAP.define_key("C-n", "send-key-down")
KEYMAP.define_key("C-p", "send-key-up")


@KEYMAP.define_key("C-Space")
def set_mark(ctx):
    run_js(ctx, "set_or_unset_mark(getActiveElement());")


@KEYMAP.define_key("C-f")
def forward_char(ctx):
    run_js(ctx, "forward_char(getActiveElement());")


@KEYMAP.define_key("C-b")
def backward_char(ctx):
    run_js(ctx, "backward_char(getActiveElement());")


@KEYMAP.define_key("M-f")
def forward_word(ctx):
    run_js(ctx, "forward_word(getActiveElement());")


@KEYMAP.define_key("M-b")
def backward_word(ctx):
    run_js(ctx, "backward_word(getActiveElement());")


@KEYMAP.define_key("C-a")
def move_beginning_of_line(ctx):
    run_js(ctx, "move_beginning_of_line(getActiveElement());")


@KEYMAP.define_key("C-e")
def move_end_of_line(ctx):
    run_js(ctx, "move_end_of_line(getActiveElement());")


@KEYMAP.define_key("C-d")
def delete_char(ctx):
    run_js(ctx, "delete_char(getActiveElement());")


@KEYMAP.define_key("M-d")
def delete_word(ctx):
    run_js(ctx, "delete_word(getActiveElement());")


@KEYMAP.define_key("M-Backspace")
def delete_word_backward(ctx):
    run_js(ctx, "delete_word_backward(getActiveElement());")


@KEYMAP.define_key("M-w")
def copy(ctx):
    run_js(ctx, "copy_text(getActiveElement());")


@KEYMAP.define_key("C-w")
def cut(ctx):
    run_js(ctx, "copy_text(getActiveElement(), true);")


KEYMAP.define_key("C-y", "webcontent-paste")


@KEYMAP.define_key("M-u")
def upcase_word(ctx):
    run_js(ctx, "upcase_word(getActiveElement());")


@KEYMAP.define_key("M-l")
def downcase_word(ctx):
    run_js(ctx, "downcase_word(getActiveElement());")


@KEYMAP.define_key("M-c")
def capitalize_word(ctx):
    run_js(ctx, "capitalize_word(getActiveElement());")
