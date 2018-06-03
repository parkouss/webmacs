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

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QImage
from PyQt5.QtNetwork import QNetworkRequest

from .. import current_buffer
from ..minibuffer import Prompt
from ..commands import define_command
from ..application import app


class BufferHistoryTableModel(QAbstractTableModel):
    def __init__(self, history):
        QAbstractTableModel.__init__(self)
        self._history = history
        nm = app().network_manager
        self._icons = {}
        for h in history:
            reply = nm.get(QNetworkRequest(h.iconUrl()))
            reply.finished.connect(self.icon_dl_finished)

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
            return self._icons.get(hitem.iconUrl())  # hitem.iconUrl()

    def index(self, row, col, parent=QModelIndex()):
        try:
            return self.createIndex(row, col, self._history[row])
        except IndexError:
            return QModelIndex()

    def icon_dl_finished(self):
        reply = self.sender()
        url = reply.request().url()

        img = QImage()
        img.loadFromData(reply.readAll())
        if img.height() != 16 and img.width != 16:
            img = img.scaled(16, 16, Qt.KeepAspectRatio)

        reply.deleteLater()

        self._icons[url] = img
        for i, item in enumerate(self._history):
            if item.iconUrl() == url:
                index = self.index(i, 0)
                self.dataChanged.emit(index, index)


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
def buffer_history(ctx):
    """
    Prompt to navigate in the local buffer history.
    """
    selected = ctx.prompt.index()
    if selected.row() >= 0:
        ctx.prompt.page_history.goToItem(selected.internalPointer())
