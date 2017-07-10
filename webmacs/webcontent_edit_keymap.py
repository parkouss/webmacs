from PyQt5.QtWebEngineWidgets import QWebEngineScript

from .keymaps import Keymap, KeyPress
from .webbuffer import current_buffer
from .keyboardhandler import send_key_event

KEYMAP = Keymap("webcontent-edit")


@KEYMAP.define_key("C-g")
def cancel():
    current_buffer().runJavaScript("""
    if (document.activeElement) { document.activeElement.blur(); }
    """)


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
def forward_char():
    current_buffer().runJavaScript(
        "backward_char(document.activeElement);",
        QWebEngineScript.ApplicationWorld
    )
