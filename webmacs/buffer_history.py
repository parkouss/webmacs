from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt

from .webbuffer import current_buffer
from .minibuffer import Prompt
from .commands import define_command


class BufferHistoryTableModel(QAbstractTableModel):
    def __init__(self, history):
        QAbstractTableModel.__init__(self)
        self._history = history

    def rowCount(self, index=QModelIndex()):
        return len(self._history)

    def columnCount(self, index=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        hitem = index.internalPointer()
        if not hitem:
            return

        col = index.column()
        if role == Qt.DisplayRole:
            if col == 0:
                return hitem.url().toString()
            else:
                return hitem.title()
        elif role == Qt.DecorationRole and col == 0:
            return None  # hitem.iconUrl()

    def index(self, row, col, parent=QModelIndex()):
        try:
            return self.createIndex(row, col, self._history[row])
        except IndexError:
            return QModelIndex()


class BufferHistoryListPrompt(Prompt):
    label = "buffer history:"
    complete_options = {
        "match": Prompt.FuzzyMatch,
        "complete-empty": True,
    }

    def enable(self, minibuffer):
        self.page_history = current_buffer().history()
        # keep a python reference to the items
        self._items = self.page_history.items()
        Prompt.enable(self, minibuffer)
        minibuffer.input().popup().selectRow(
            self.page_history.currentItemIndex())

    def completer_model(self):
        return BufferHistoryTableModel(self._items)


@define_command("buffer-history", prompt=BufferHistoryListPrompt)
def buffer_history(prompt):
    selected = prompt.index()
    if selected.row() >= 0:
        prompt.page_history.goToItem(selected.internalPointer())
