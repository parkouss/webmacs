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
from PyQt5.QtWebEngineWidgets import QWebEngineScript

from ..commands import define_command
from ..minibuffer import Prompt, KEYMAP
from ..webbuffer import WebBuffer, close_buffer
from ..killed_buffers import KilledBuffer
from ..keyboardhandler import send_key_event
from .. import BUFFERS
from ..keymaps import Keymap, KeyPress


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
def close_buffer_in_prompt_selection(ctx):
    pinput = ctx.minibuffer.input()

    selection = pinput.popup().selectionModel().currentIndex()
    if not selection.isValid():
        return

    selection = selection.model().mapToSource(selection)
    pinput.completer_model().close_buffer_at(selection)


class BufferListPrompt(Prompt):
    label = "select buffer:"
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


class BufferSwitchListPrompt(BufferListPrompt):
    label = "switch to buffer:"


class BufferKillListPrompt(BufferListPrompt):
    label = "kill all buffers except:"

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        # auto-select the currently visible buffer
        minibuffer.input().popup().selectRow(0)


@define_command("switch-buffer", prompt=BufferSwitchListPrompt)
def switch_buffer(ctx):
    """
    Prompt to select a buffer to display in the current view.
    """
    selected = ctx.prompt.index()
    if selected.row() >= 0:
        view = ctx.window.current_webview()
        buffer = selected.internalPointer()
        if view.buffer() == buffer:
            # swith to the same buffer, nothing to do
            return
        if buffer.view():
            # swap buffers if the buffer is already displayed
            otherbuffer = view.buffer()
            view.setBuffer(None)
            otherview = buffer.view()
            otherview.setBuffer(otherbuffer)
        view.setBuffer(buffer)


@define_command("go-forward")
def go_forward(ctx):
    """
    Navigate forward in history for the current buffer.
    """
    if not ctx.buffer.history().canGoForward():
        ctx.minibuffer.show_info("Can't go forward in history.")
    else:
        ctx.buffer.triggerAction(WebBuffer.Forward)


@define_command("go-backward")
def go_backward(ctx):
    """
    Navigate backward in history for the current buffer.
    """
    if not ctx.buffer.history().canGoBack():
        ctx.minibuffer.show_info("Can't go back in history.")
    else:
        ctx.buffer.triggerAction(WebBuffer.Back)


@define_command("scroll-down")
def scroll_down(ctx):
    """
    Scroll the current buffer down a bit.
    """
    ctx.buffer.scroll_by(y=20)


@define_command("scroll-up")
def scroll_up(ctx):
    """
    Scroll the current buffer up a bit.
    """
    ctx.buffer.scroll_by(y=-20)


@define_command("scroll-page-down")
def scroll_page_down(ctx):
    """
    Scroll the current buffer one page down.
    """
    send_key_event(ctx.sender, KeyPress.from_str("PageDown"))


@define_command("scroll-page-up")
def scroll_page_up(ctx):
    """
    Scroll the current buffer one page up.
    """
    send_key_event(ctx.sender, KeyPress.from_str("PageUp"))


@define_command("scroll-top")
def scroll_top(ctx):
    """
    Scroll the current buffer to the top.
    """
    send_key_event(ctx.sender, KeyPress.from_str("Home"))


@define_command("scroll-bottom")
def scroll_bottom(ctx):
    """
    Scroll the current buffer to the bottom.
    """
    send_key_event(ctx.sender, KeyPress.from_str("End"))


@define_command("webcontent-copy")
def webcontent_copy(ctx):
    """
    Copy the selection in the current buffer.
    """
    ctx.buffer.triggerAction(WebBuffer.Copy)


@define_command("webcontent-cut")
def webcontent_cut(ctx):
    """
    Cut the selection in the current buffer.
    """
    ctx.buffer.triggerAction(WebBuffer.Cut)


@define_command("webcontent-paste")
def webcontent_paste(ctx):
    """
    Paste the selection in the current buffer.
    """
    ctx.buffer.triggerAction(WebBuffer.Paste)


@define_command("reload-buffer")
def reload_buffer(ctx):
    """
    Reload the current buffer.
    """
    ctx.buffer.triggerAction(WebBuffer.Reload)


@define_command("reload-buffer-no-cache")
def reload_buffer_no_cache(ctx):
    """
    Reload the current buffer bypassing any cache.
    """
    ctx.buffer.triggerAction(WebBuffer.ReloadAndBypassCache)


@define_command("close-buffer")
def buffer_close(ctx):
    """
    Close the current buffer.
    """
    close_buffer(ctx.buffer)


@define_command("close-other-buffers", prompt=BufferKillListPrompt)
def close_other_buffers(ctx):
    """
    Close all but one buffer.
    """
    # Select a buffer
    selected = ctx.prompt.index()
    if selected.row() >= 0:
        # Get all other buffers and kill them
        for wb in [b for b in BUFFERS if b != selected.internalPointer()]:
            close_buffer(wb)


@define_command("select-buffer-content")
def buffer_select_content(ctx):
    """
    Select all content in the buffer.
    """
    ctx.buffer.triggerAction(WebBuffer.SelectAll)


@define_command("zoom-in")
def zoom_in(ctx):
    """
    Zoom-in in the buffer.
    """
    ctx.buffer.zoom_in()


@define_command("zoom-out")
def zoom_out(ctx):
    """
    Zoom-out in the buffer.
    """
    ctx.buffer.zoom_out()


@define_command("zoom-normal")
def zoom_normal(ctx):
    """
    Zoom-normal in the buffer.
    """
    ctx.buffer.zoom_normal()


def _show_info_text_zoom(ctx):
    def _wrapper(ratio):
        ctx.minibuffer.show_info("Text zoom level: %02d%%"
                                 % (ratio * 100))
    return _wrapper


@define_command("text-zoom-in")
def text_zoom_in(ctx):
    """
    Zom in (text only) in the buffer.
    """
    ctx.buffer.runJavaScript("textzoom.changeFont(0.1);",
                             QWebEngineScript.ApplicationWorld,
                             _show_info_text_zoom(ctx))


@define_command("text-zoom-out")
def text_zoom_out(ctx):
    """
    Zom out (text only) in the buffer.
    """
    ctx.buffer.runJavaScript("textzoom.changeFont(-0.1);",
                             QWebEngineScript.ApplicationWorld,
                             _show_info_text_zoom(ctx))


@define_command("text-zoom-reset")
def text_zoom_reset(ctx):
    """
    Reset the zoom (text only) in the buffer.
    """
    ctx.buffer.runJavaScript("textzoom.resetChangeFont();",
                             QWebEngineScript.ApplicationWorld,
                             _show_info_text_zoom(ctx))


@define_command("buffer-unselect")
def buffer_unselect(ctx):
    """
    Unselect selection in the current web buffer.
    """
    ctx.buffer.triggerAction(WebBuffer.Unselect)


class KilledBufferTableModel(QAbstractTableModel):
    def __init__(self):
        QAbstractTableModel.__init__(self)
        self._buffers = list(KilledBuffer.all)

    def rowCount(self, index=QModelIndex()):
        return len(self._buffers)

    def columnCount(self, index=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        killed_buff = index.internalPointer()
        if not killed_buff:
            return

        col = index.column()
        if role == Qt.DisplayRole:
            if col == 0:
                return killed_buff.url.toString()
            else:
                return killed_buff.title
        elif role == Qt.DecorationRole and col == 0:
            return killed_buff.icon

    def index(self, row, col, parent=QModelIndex()):
        try:
            return self.createIndex(row, col, self._buffers[row])
        except IndexError:
            return QModelIndex()


class KilledBufferListPrompt(Prompt):
    label = "buffer to revive:"
    complete_options = {
        "match": Prompt.FuzzyMatch,
        "complete-empty": True,
    }

    def completer_model(self):
        return KilledBufferTableModel()

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        if KilledBuffer.all:
            minibuffer.input().popup().selectRow(0)


@define_command("revive-buffer", prompt=KilledBufferListPrompt)
def revive_buffer(ctx):
    """
    Revive a previously killed buffer in the current view.
    """
    selected = ctx.prompt.index()
    if selected.row() >= 0:
        killed_buffer = selected.internalPointer()
        buff = killed_buffer.revive()

        ctx.window.current_webview().setBuffer(buff)
