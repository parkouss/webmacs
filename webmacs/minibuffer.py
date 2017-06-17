from PyQt5.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QLabel, \
    QCompleter, QFileSystemModel

from .keyboardhandler import KeyboardHandler, is_keypress
from .keymap import Keymap


KEYMAP = Keymap("minibuffer")


class MinibufferInput(QLineEdit):
    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)
        self.keyboard_handler = KeyboardHandler([KEYMAP])

    def event(self, event):
        if is_keypress(event) and self.keyboard_handler.handle_keypress(event):
            return True
        return QLineEdit.event(self, event)


class Minibuffer(QWidget):
    def __init__(self, window):
        QWidget.__init__(self, window)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.label = QLabel(self)
        layout.addWidget(self.label)

        self.line_edit = MinibufferInput(self)
        layout.addWidget(self.line_edit)

        model = QFileSystemModel(self)
        model.setRootPath("/")
        self.completer = QCompleter(self)
        self.completer.setMaxVisibleItems(10)
        self.completer.setModel(model)
        self.line_edit.setCompleter(self.completer)


def minibuffer():
    from .window import current_window
    return current_window().minibuffer()


@KEYMAP.define_key("Tab")
def complete():
    completer = minibuffer().completer

    def next_completion():
        index = completer.currentIndex()
        completer.popup().setCurrentIndex(index)
        start = index.row()
        if not completer.setCurrentRow(start + 1):
            completer.setCurrentRow(0)

    if not completer.popup().isVisible():
        completer.complete()
    else:
        next_completion()


@KEYMAP.define_key("C-g")
def cancel():
    completer = minibuffer().completer
    if completer.popup().isVisible():
        completer.popup().close()
