from PyQt5.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QLabel, \
    QCompleter
from PyQt5.QtCore import QObject, pyqtSignal as Signal, pyqtSlot as Slot

from .keyboardhandler import KeyboardHandler, is_keypress
from .keymap import Keymap


KEYMAP = Keymap("minibuffer")


class Prompt(QObject):
    label = ""
    got_value = Signal(object)
    closed = Signal()

    def completer_model(self):
        return None

    def validate(self, text):
        return text

    def enable(self, minibuffer):
        self.minibuffer = minibuffer
        minibuffer.label.setText(self.label)
        buffer_input = minibuffer.line_edit
        buffer_input.show()
        buffer_input.setFocus()
        buffer_input.completer().setModel(self.completer_model())
        buffer_input.edition_finished.connect(self._on_edition_finished)

    def close(self):
        minibuffer = self.minibuffer
        minibuffer.label.setText("")
        buffer_input = minibuffer.line_edit
        buffer_input.hide()
        buffer_input.setText("")
        c_model = buffer_input.completer().model()
        buffer_input.completer().setModel(None)
        if c_model:
            c_model.deleteLater()
        self.closed.emit()

    @Slot()
    def _on_edition_finished(self):
        txt = self.minibuffer.line_edit.text()
        value = self.validate(txt)
        self.got_value.emit(value)
        self.close()


class MinibufferInput(QLineEdit):
    edition_finished = Signal()

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

        self.completer = Completer(self)
        self.completer.setMaxVisibleItems(10)
        self.line_edit.setCompleter(self.completer)
        self.line_edit.hide()
        self._prompt = None

    def prompt(self, prompt):
        self.close_prompt()
        self._prompt = prompt
        if prompt:
            prompt.enable(self)
            prompt.closed.connect(self._prompt_closed)
            prompt.closed.connect(prompt.deleteLater)

    def close_prompt(self):
        if self._prompt:
            self._prompt.close()
            self._prompt = None

    def _prompt_closed(self):
        self._prompt = None


def current_minibuffer():
    from .window import current_window
    return current_window().minibuffer()


@KEYMAP.define_key("Tab")
def complete():
    completer = current_minibuffer().completer

    if not completer.popup().isVisible():
        completer.complete()
    else:
        completer.highlight_next_completion()


@KEYMAP.define_key("C-n")
def next_completion():
    current_minibuffer().completer.highlight_next_completion()


@KEYMAP.define_key("C-p")
def previous_completion():
    current_minibuffer().completer.highlight_next_completion(False)


@KEYMAP.define_key("Return")
def edition_finished():
    current_minibuffer().line_edit.edition_finished.emit()


@KEYMAP.define_key("C-g")
def cancel():
    minibuffer = current_minibuffer()
    completer = minibuffer.completer
    if completer.popup().isVisible():
        completer.popup().close()
    else:
        minibuffer.close_prompt()
