from PyQt5.QtCore import QObject, QEvent

from .keymap import KeyPress


class KeyboardHandler(QObject):
    def __init__(self, keymaps, parent=None):
        QObject.__init__(self, parent)
        self._keymaps = keymaps
        self._keypresses = []

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.KeyPress):
            key = KeyPress.from_qevent(event)
            if key is None:
                return True
            if self.handle_keypress(key):
                return True

        return QObject.eventFilter(self, obj, event)

    def handle_keypress(self, keypress):
        incomplete_keychord = False
        command_called = False
        self._keypresses.append(keypress)

        for keymap in self._keymaps:
            result = keymap.lookup(self._keypresses)

            if result is None:
                pass
            elif not result.complete:
                incomplete_keychord = True
            else:
                result.command()
                command_called = True

        if command_called or not incomplete_keychord:
            self._keypresses = []

        return command_called or incomplete_keychord
