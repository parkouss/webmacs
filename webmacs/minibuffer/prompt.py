import os

from PyQt5.QtCore import QObject, QAbstractTableModel, QModelIndex, Qt, \
    pyqtSlot as Slot, pyqtSignal as Signal, QRegExp

from PyQt5.QtGui import QRegExpValidator

from ..keyboardhandler import set_global_keymap_enabled
from ..keymaps import Keymap


class FSModel(QAbstractTableModel):
    """
    A custom filesystemmodel that does work with the custom completer;

    May not be as efficient as the qt version, but works without much pain.
    """
    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._root_dir = ""
        self._files = []

    def rowCount(self, index=QModelIndex()):
        return len(self._files)

    def columnCount(self, index=QModelIndex()):
        return 1

    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        try:
            return os.path.join(self._root_dir, self._files[index.row()])
        except IndexError:
            return None

    @Slot(str)
    def text_changed(self, text):
        if text.endswith("/"):
            root_dir = text
        else:
            root_dir = os.path.dirname(text)

        if root_dir != self._root_dir:
            try:
                files = os.listdir(root_dir)
            except OSError:
                return
            self.beginResetModel()
            self._files = files
            self._root_dir = root_dir
            self.endResetModel()


class PromptTableModel(QAbstractTableModel):
    def __init__(self, data, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, index=QModelIndex()):
        return len(self._data)

    def columnCount(self, index=QModelIndex()):
        if self._data:
            return len(self._data[0])
        return 0

    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        return index.internalPointer()

    def index(self, row, col, parent=QModelIndex()):
        try:
            return self.createIndex(row, col, self._data[row][col])
        except IndexError:
            return QModelIndex()


class Prompt(QObject):
    label = ""
    complete_options = {}
    keymap = None

    SimpleMatch = 0
    FuzzyMatch = 1

    finished = Signal()
    closed = Signal()

    def completer_model(self):
        return None

    def enable(self, minibuffer):
        self.__index = QModelIndex()
        self.minibuffer = minibuffer
        minibuffer.label.setText(self.label)
        buffer_input = minibuffer.input()
        buffer_input.setText("")
        buffer_input.show()
        buffer_input.setFocus()
        completer_model = self.completer_model()
        if hasattr(completer_model, "text_changed"):
            buffer_input.textEdited.connect(completer_model.text_changed)
        buffer_input.set_completer_model(completer_model)
        buffer_input.returnPressed.connect(self._on_edition_finished)
        buffer_input.completion_activated.connect(
            self._on_completion_activated)
        buffer_input.configure_completer(self.complete_options)
        if self.complete_options.get("complete-empty"):
            buffer_input.show_completions()

    def close(self):
        minibuffer = self.minibuffer
        minibuffer.label.setText("")
        buffer_input = minibuffer.input()
        buffer_input.returnPressed.disconnect(self._on_edition_finished)
        buffer_input.completion_activated.disconnect(
            self._on_completion_activated)
        # calling setFocus() on the view is required, else the view is scrolled
        # to the top automatically. But we don't even get a focus in event;
        minibuffer.parent().current_web_view().setFocus()
        buffer_input.hide()
        buffer_input.set_mark(False)
        c_model = buffer_input.completer_model()
        buffer_input.set_completer_model(None)
        if c_model:
            c_model.deleteLater()
        self.closed.emit()

    def _on_completion_activated(self, index):
        self.__index = index

    def value(self):
        return self.minibuffer.input().text()

    def index(self):
        return self.__index

    @Slot()
    def _on_edition_finished(self):
        self.close()
        self.finished.emit()


class YesNoPrompt(Prompt):
    keymap = Keymap("yes-no")  # an empty keymap

    def __init__(self, label, parent=None):
        Prompt.__init__(self, parent)
        self.label = label + "[y/n]"
        self.yes = None

    def enable(self, minibuffer):
        set_global_keymap_enabled(False)  # disable any global keychord
        Prompt.enable(self, minibuffer)
        buffer_input = minibuffer.input()

        validator = QRegExpValidator(QRegExp("[yYnN]"))
        buffer_input.setValidator(validator)
        buffer_input.textEdited.connect(self._on_text_edited)

    def _on_text_edited(self, text):
        self.yes = text in ('y', 'Y')
        self.close()
        buffer_input = self.minibuffer.input()
        buffer_input.validator().deleteLater()
        buffer_input.setValidator(None)
        set_global_keymap_enabled(True)
