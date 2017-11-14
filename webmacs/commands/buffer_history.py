from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSlot as \
    Slot, QThread, pyqtSignal as Signal, QUrl
from PyQt5.QtGui import QImage
import concurrent.futures
import urllib.request

from .. import current_buffer
from ..minibuffer import Prompt
from ..commands import define_command


class IconRetriever(QThread):
    """
    Note: Using QNetworkAcessManager was causing a segfault.
    """
    download_finished = Signal(QUrl, QImage)

    def __init__(self, urls):
        QThread.__init__(self)
        self.urls = urls

    def load_icon(self, url):
        with urllib.request.urlopen(url, timeout=5) as conn:
            img = QImage()
            img.loadFromData(conn.read())
            if img.height() != 16 and img.width != 16:
                img = img.scaled(16, 16, Qt.KeepAspectRatio)
            return img

    def run(self):
        # We can use a with statement to ensure threads are cleaned up promptly
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Start the load operations and mark each future with its URL
            futures = {executor.submit(self.load_icon, url.toString()): url
                       for url in self.urls if url.isValid()}
            for future in concurrent.futures.as_completed(futures):
                url = futures[future]
                try:
                    img = future.result()
                except Exception as exc:
                    print('Got an exception (%s): %s' % (url, exc))
                else:
                    self.download_finished.emit(url, img)


class BufferHistoryTableModel(QAbstractTableModel):
    def __init__(self, history):
        QAbstractTableModel.__init__(self)
        self._history = history
        self._icons = {}
        self._icon_retriever = IconRetriever(h.iconUrl() for h in history)
        self._icon_retriever.download_finished.connect(self.icon_dl_finished)
        self._icon_retriever.start()

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

    @Slot(QUrl, QImage)
    def icon_dl_finished(self, url, img):
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
def buffer_history(prompt):
    selected = prompt.index()
    if selected.row() >= 0:
        prompt.page_history.goToItem(selected.internalPointer())
