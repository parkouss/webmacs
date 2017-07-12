from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt

from ..commands import define_command
from ..minibuffer import Prompt
from ..webbuffer import BUFFERS, current_buffer, WebBuffer, close_buffer
from ..window import current_window


class BufferTableModel(QAbstractTableModel):
    def __init__(self):
        QAbstractTableModel.__init__(self)
        self._buffers = BUFFERS[:]

    def rowCount(self, index=QModelIndex()):
        return len(self._buffers)

    def columnCount(self, index=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        buff = index.internalPointer()
        if not buff:
            return

        col = index.column()
        if role == Qt.DisplayRole:
            if col == 0:
                return buff.url().toString()
            else:
                return buff.title()
        elif role == Qt.DecorationRole and col == 0:
            return buff.icon()

    def index(self, row, col, parent=QModelIndex()):
        try:
            return self.createIndex(row, col, self._buffers[row])
        except IndexError:
            return QModelIndex()


class BufferListPrompt(Prompt):
    label = "switch buffer:"
    complete_options = {
        "match": Prompt.FuzzyMatch,
        "complete-empty": True,
    }

    def completer_model(self):
        return BufferTableModel()


@define_command("switch-buffer", prompt=BufferListPrompt)
def switch_buffer(prompt):
    selected = prompt.index()
    if selected.row() >= 0:
        view = current_window().current_web_view()
        view.setBuffer(selected.internalPointer())


@define_command("go-forward")
def go_forward():
    current_buffer().triggerAction(WebBuffer.Forward)


@define_command("go-backward")
def go_backward():
    current_buffer().triggerAction(WebBuffer.Back)


@define_command("scroll-down")
def scroll_down():
    current_buffer().scroll_by(y=20)


@define_command("scroll-up")
def scroll_up():
    current_buffer().scroll_by(y=-20)


@define_command("scroll-page-down")
def scroll_page_down():
    current_buffer().scroll_page(1)


@define_command("scroll-page-up")
def scroll_page_up():
    current_buffer().scroll_page(-1)


@define_command("scroll-top")
def scroll_top():
    current_buffer().scroll_top()


@define_command("scroll-bottom")
def scroll_bottom():
    current_buffer().scroll_bottom()


@define_command("webcontent-copy")
def webcontent_copy():
    current_buffer().triggerAction(WebBuffer.Copy)


@define_command("webcontent-cut")
def webcontent_cut():
    current_buffer().triggerAction(WebBuffer.Cut)


@define_command("webcontent-paste")
def webcontent_paste():
    current_buffer().triggerAction(WebBuffer.Paste)


@define_command("reload-buffer")
def reload_buffer():
    current_buffer().triggerAction(WebBuffer.Reload)


@define_command("reload-buffer-no-cache")
def reload_buffer_no_cache():
    current_buffer().triggerAction(WebBuffer.ReloadAndBypassCache)


@define_command("close-buffer")
def buffer_close():
    current = current_buffer()
    available_buffers = [b for b in BUFFERS if b == current or not b.view()]

    if len(available_buffers) < 2:
        return

    index = available_buffers.index(current) + 1
    if index >= len(available_buffers):
        index = 0

    current_window().current_web_view().setBuffer(available_buffers[index])
    close_buffer(current)
