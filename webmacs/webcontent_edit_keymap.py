from PyQt5.QtWebEngineWidgets import QWebEngineScript

from .keymaps import Keymap, KeyPress
from .webbuffer import current_buffer
from .keyboardhandler import send_key_event

KEYMAP = Keymap("webcontent-edit")


@KEYMAP.define_key("C-g")
def cancel():
    # if a mark is active, clear that but keep the focus. If there is no mark
    # active, then just unfocus the editable js object.
    current_buffer().runJavaScript("""
    var e = document.activeElement;
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
        "set_or_unset_mark(document.activeElement);",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("C-f")
def forward_char():
    current_buffer().runJavaScript(
        "forward_char(document.activeElement);",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("C-b")
def backward_char():
    current_buffer().runJavaScript(
        "backward_char(document.activeElement);",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("M-f")
def forward_word():
    current_buffer().runJavaScript(
        "forward_word(document.activeElement);",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("M-b")
def backward_word():
    current_buffer().runJavaScript(
        "backward_word(document.activeElement);",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("C-a")
def move_beginning_of_line():
    current_buffer().runJavaScript(
        "move_beginning_of_line(document.activeElement);",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("C-e")
def move_end_of_line():
    current_buffer().runJavaScript(
        "move_end_of_line(document.activeElement);",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("C-d")
def delete_char():
    current_buffer().runJavaScript(
        "delete_char(document.activeElement);",
        QWebEngineScript.ApplicationWorld
    )


@KEYMAP.define_key("M-d")
def delete_word():
    current_buffer().runJavaScript(
        "delete_word(document.activeElement);",
        QWebEngineScript.ApplicationWorld
    )


KEYMAP.define_key("M-w", "webcontent-copy")
KEYMAP.define_key("C-y", "webcontent-paste")
