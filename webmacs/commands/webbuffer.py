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

from ..commands import define_command
from ..minibuffer import Prompt, KEYMAP
from ..webbuffer import WebBuffer, close_buffer
from .. import current_window, current_minibuffer, BUFFERS, \
    current_buffer
from ..keymaps import Keymap


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

    def close_buffer_at(self, index):
        try:
            if not close_buffer(self._buffers[index.row()]):
                return
        except ValueError:
            return

        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        self._buffers.pop(index.row())
        self.endRemoveRows()


BUFFERLIST_KEYMAP = Keymap("buffer-list", parent=KEYMAP)


@BUFFERLIST_KEYMAP.define_key("C-k")
def close_buffer_in_prompt_selection():
    pinput = current_minibuffer().input()

    selection = pinput.popup().selectionModel().currentIndex()
    if not selection.isValid():
        return

    selection = selection.model().mapToSource(selection)
    pinput.completer_model().close_buffer_at(selection)


class BufferListPrompt(Prompt):
    label = "switch buffer:"
    complete_options = {
        "match": Prompt.FuzzyMatch,
        "complete-empty": True,
    }
    keymap = BUFFERLIST_KEYMAP

    def completer_model(self):
        return BufferTableModel()

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        # auto-select the most recent not currently visible buffer
        for i, buf in enumerate(BUFFERS):
            if not buf.view():
                minibuffer.input().popup().selectRow(i)
                break


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
    close_buffer(current)
