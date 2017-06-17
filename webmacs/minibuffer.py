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


class Completer(QCompleter):
    def highlight_next_completion(self, forward=True):
        if not self.popup().isVisible():
            return

        row = self.currentRow()

        # weird case, the first highlight on forward go to the second item
        # without this fix
        if row == 0 and forward:
            sel = self.popup().selectionModel()
            if not sel or not sel.hasSelection():
                row = -1

        count = self.completionModel().rowCount()
        pos = row + (1 if forward else -1)

        if pos < 0:
            pos = count - 1
        elif pos >= count:
            pos = 0
        self.setCurrentRow(pos)
        self.popup().setCurrentIndex(self.currentIndex())


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
        self.completer = Completer(self)
        self.completer.setMaxVisibleItems(10)
        self.completer.setModel(model)
        self.line_edit.setCompleter(self.completer)


def minibuffer():
    from .window import current_window
    return current_window().minibuffer()


@KEYMAP.define_key("Tab")
def complete():
    completer = minibuffer().completer

    if not completer.popup().isVisible():
        completer.complete()
    else:
        completer.highlight_next_completion()


@KEYMAP.define_key("C-n")
def next_completion():
    minibuffer().completer.highlight_next_completion()


@KEYMAP.define_key("C-p")
def previous_completion():
    minibuffer().completer.highlight_next_completion(False)


@KEYMAP.define_key("C-g")
def cancel():
    completer = minibuffer().completer
    if completer.popup().isVisible():
        completer.popup().close()
