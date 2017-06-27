from .keymaps import Keymap
from .webbuffer import current_buffer

KEYMAP = Keymap("webcontent-edit")


@KEYMAP.define_key("C-g")
def cancel():
    current_buffer().runJavaScript("""
    if (document.activeElement) { document.activeElement.blur(); }
    """)
