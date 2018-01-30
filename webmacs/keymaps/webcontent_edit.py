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

from . import Keymap, KeyPress
from .. import current_buffer
from ..keyboardhandler import send_key_event


KEYMAP = Keymap("webcontent-edit")


@KEYMAP.define_key("C-g")
def cancel():
    # if a mark is active, clear that but keep the focus. If there is no mark
    # active, then just unfocus the editable js object.
    current_buffer().runJavaScript("""
    var e = getActiveElement();
    if (has_any_mark(e)) {
        // be sure that we have a mark, then unset it.
        text_marks[e] = true;
        set_or_unset_mark(e);
    } else {
        e.blur();
    }
    """, QWebEngineScript.ApplicationWorld)


@KEYMAP.define_key("C-n")
def next():
    key = KeyPress.from_str("Down")
    send_key_event(key)


@KEYMAP.define_key("C-p")
def prev():
    key = KeyPress.from_str("Up")
    send_key_event(key)


@KEYMAP.define_key("C-Space")
def set_mark():
    current_buffer().runJavaScript(
        "set_or_unset_mark(getActiveElement());",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("C-f")
def forward_char():
    current_buffer().runJavaScript(
        "forward_char(getActiveElement());",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("C-b")
def backward_char():
    current_buffer().runJavaScript(
        "backward_char(getActiveElement());",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("M-f")
def forward_word():
    current_buffer().runJavaScript(
        "forward_word(getActiveElement());",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("M-b")
def backward_word():
    current_buffer().runJavaScript(
        "backward_word(getActiveElement());",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("C-a")
def move_beginning_of_line():
    current_buffer().runJavaScript(
        "move_beginning_of_line(getActiveElement());",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("C-e")
def move_end_of_line():
    current_buffer().runJavaScript(
        "move_end_of_line(getActiveElement());",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("C-d")
def delete_char():
    current_buffer().runJavaScript(
        "delete_char(getActiveElement());",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("M-d")
def delete_word():
    current_buffer().runJavaScript(
        "delete_word(getActiveElement());",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("M-Backspace")
def delete_word_backward():
    current_buffer().runJavaScript(
        "delete_word_backward(getActiveElement());",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("M-w")
def copy():
    current_buffer().runJavaScript(
        "copy_text(getActiveElement());",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("C-w")
def cut():
    current_buffer().runJavaScript(
        "copy_text(getActiveElement(), true);",
        QWebEngineScript.ApplicationWorld
    )


KEYMAP.define_key("C-y", "webcontent-paste")


@KEYMAP.define_key("M-u")
def upcase_word():
    current_buffer().runJavaScript(
        "upcase_word(getActiveElement());",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("M-l")
def downcase_word():
    current_buffer().runJavaScript(
        "downcase_word(getActiveElement());",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("M-c")
def capitalize_word():
    current_buffer().runJavaScript(
        "capitalize_word(getActiveElement());",
        QWebEngineScript.ApplicationWorld
    )
