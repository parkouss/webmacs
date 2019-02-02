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

import itertools

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWebEngineWidgets import QWebEngineScript

from ..commands import define_command
from ..minibuffer import Prompt
from ..webbuffer import WebBuffer, close_buffer, create_buffer
from ..killed_buffers import KilledBuffer
from ..keyboardhandler import send_key_event
from .. import BUFFERS, version, current_buffer, recent_buffers
from .. import variables, clipboard, GLOBAL_OBJECTS
from ..keymaps import KeyPress, BUFFERLIST_KEYMAP


switch_buffer_current_color = variables.define_variable(
    "switch-buffer-current-color",
    "The color to use for the current buffer in the switch-buffer list."
    " Set to an empty string if you don't want a special color.",
    "#c0d5f7",
    type=variables.String(),
)


class BufferTableModel(QAbstractTableModel):

    def __init__(self, buffers):
        QAbstractTableModel.__init__(self)
        self._buffers = list(buffers)

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
                return "[{}] {}".format(BUFFERS.index(buff) + 1, buff.title())
        elif role == Qt.DecorationRole and col == 0:
            return buff.icon()
        elif role == Qt.BackgroundColorRole:
            if buff == current_buffer():
                if switch_buffer_current_color.value:
                    return QColor(switch_buffer_current_color.value)

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


@define_command("buffer-list-delete-highlighted")
def close_buffer_in_prompt_selection(ctx):
    """
    Close currently highlighted buffer.
    """
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
    value_return_index_data = True

    def completer_model(self):
        return BufferTableModel(self.ordered_buffers())

    def ordered_buffers(self):
        """
        How to display buffers.
        """
        return BUFFERS

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        # select the next buffer
        buffers = self.ordered_buffers()
        index = buffers.index(current_buffer()) + 1
        if index >= len(buffers):
            index = 0
        minibuffer.input().popup().selectRow(index)


class RecentBufferListPrompt(BufferListPrompt):

    def ordered_buffers(self):
        return recent_buffers()


class BufferSwitchListPrompt(BufferListPrompt):
    label = "switch to buffer:"


class RecentBufferSwitchListPrompt(RecentBufferListPrompt):
    label = "switch to buffer:"


class BufferKillListPrompt(BufferListPrompt):
    label = "kill all buffers except:"

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        # auto-select the currently visible buffer
        buffers = self.ordered_buffers()
        minibuffer.input().popup().selectRow(buffers.index(current_buffer()))


def show_buffer(buffer, view):
    """
    Display the given buffer in the given view.
    """
    if view.buffer() == buffer:
        # switch to the same buffer, nothing to do
        return
    if buffer.view():
        # swap buffers if the buffer is already displayed
        otherbuffer = view.buffer()
        view.setBuffer(None)
        otherview = buffer.view()
        otherview.setBuffer(otherbuffer)
    view.setBuffer(buffer)


@define_command("switch-buffer")
def switch_buffer(ctx):
    """
    Prompt to select a buffer to display in the current view.
    """
    buffer = ctx.minibuffer.do_prompt(BufferSwitchListPrompt(ctx))
    if buffer:
        show_buffer(buffer, ctx.view)


@define_command("switch-recent-buffer")
def switch_recent_buffer(ctx):
    """
    Prompt to select a buffer to display in the current view.
    """
    buffer = ctx.minibuffer.do_prompt(RecentBufferSwitchListPrompt(ctx))
    if buffer:
        show_buffer(buffer, ctx.view)


def _next_buffer(ctx, reverse=False):
    if len(BUFFERS) <= 1:
        return

    buffers = itertools.cycle(reversed(BUFFERS) if reverse else BUFFERS)
    next_b = next(buffers)
    while next_b != ctx.buffer:
        next_b = next(buffers)

    show_buffer(next(buffers), ctx.view)


@define_command("next-buffer")
def next_buffer(ctx):
    """
    Cycle to the next buffer in the current view.
    """
    _next_buffer(ctx)


@define_command("previous-buffer")
def previous_buffer(ctx):
    """
    Cycle to the previous buffer in the current view.
    """
    _next_buffer(ctx, reverse=True)


class OpenDevToolsPrompt(BufferListPrompt):
    label = "open dev tools for buffer:"
    keymap = None

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        # auto-select the currently visible buffer
        minibuffer.input().popup().selectRow(0)


@define_command("open-dev-tools")
def open_dev_tools(ctx):
    """
    Opens a dev tool page for a buffer.
    """
    if version.min_qt_version < (5, 11):
        ctx.minibuffer.show_info("Only available with qt version >= 5.11")
        return
    buffer = ctx.minibuffer.do_prompt(OpenDevToolsPrompt(ctx))
    if buffer:
        dev_tools = create_buffer()
        buffer.setDevToolsPage(dev_tools)


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
    send_key_event(KeyPress.from_str("PageDown"))


@define_command("scroll-page-up")
def scroll_page_up(ctx):
    """
    Scroll the current buffer one page up.
    """
    send_key_event(KeyPress.from_str("PageUp"))


@define_command("scroll-top")
def scroll_top(ctx):
    """
    Scroll the current buffer to the top.
    """
    send_key_event(KeyPress.from_str("Home"))


@define_command("scroll-bottom")
def scroll_bottom(ctx):
    """
    Scroll the current buffer to the bottom.
    """
    send_key_event(KeyPress.from_str("End"))


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


@define_command("close-other-buffers")
def close_other_buffers(ctx):
    """
    Close all but one buffer.
    """
    # Select a buffer
    buffer = ctx.minibuffer.do_prompt(BufferKillListPrompt(ctx))
    if buffer:
        # Get all other buffers and kill them
        for wb in [b for b in BUFFERS if b != buffer]:
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


@define_command("buffer-escape")
def buffer_escape(ctx):
    """
    Clear selection or menus in the current buffer.

    The implementation clears the selection in the buffer if there is any, else
    it sends the Escape key which usually closes whatever takes the focus.
    """
    if ctx.buffer.hasSelection():
        buffer_unselect(ctx)
    else:
        send_key_event(KeyPress.from_str("Esc"))


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
    value_return_index_data = True

    def completer_model(self):
        return KilledBufferTableModel()

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        if KilledBuffer.all:
            minibuffer.input().popup().selectRow(0)


@define_command("revive-buffer")
def revive_buffer(ctx):
    """
    Revive a previously killed buffer in the current view.
    """
    killed_buffer = ctx.minibuffer.do_prompt(KilledBufferListPrompt(ctx))
    if killed_buffer:
        buff = killed_buffer.revive()
        ctx.window.current_webview().setBuffer(buff)


@define_command("copy-current-link")
def copy_current_link(ctx):
    """
    Copy the current link to the clipboard.
    """

    # note the implementation does not rely on the CopyLinkToClipboard action
    # as it does not work fully (e.g, in case a link is set current using an
    # incremental search).
    buffer = ctx.buffer
    minibuff = ctx.minibuffer

    def copy_to_clipboard(url):
        buffer.content_handler.foundCurrentLinkUrl \
                              .disconnect(copy_to_clipboard)
        if url:
            clipboard.set_text(url)
        else:
            minibuff.show_info("No current link url to copy.")

    buffer.content_handler.foundCurrentLinkUrl.connect(copy_to_clipboard)
    buffer.runJavaScript("currentLinkUrl();",
                         QWebEngineScript.ApplicationWorld)


@define_command("copy-current-buffer-url")
def copy_buffer_url(ctx):
    """
    Copy the URL of the current buffer to the clipboard.
    """
    url = str(ctx.buffer.url().toEncoded(), "utf-8")
    clipboard.set_text(url)


@define_command("copy-current-buffer-title")
def copy_buffer_title(ctx):
    """
    Copy the title of the current buffer to the clipboard.
    """
    clipboard.set_text(ctx.buffer.title())


@define_command("print-buffer")
def print_buffer(ctx):
    """
    Opens a dialog to select the printer and prints the current buffer.
    """
    from ..application import WithoutAppEventFilter

    if version.min_qt_version < (5, 8):
        ctx.minibuffer.show_info(
            "print-buffer not supported, qt version >= 5.8 required"
        )
        return

    def notif(ok):
        GLOBAL_OBJECTS.unref(printer)
        ctx.minibuffer.show_info("print successful" if ok
                                 else "failed to print")

    printer = QPrinter()
    dlg = QPrintDialog(printer)
    with WithoutAppEventFilter():
        ok = dlg.exec_() == dlg.Accepted
    if ok:
        # printer must be kept around to avoid a crash.
        # it must be released in the notif callback
        GLOBAL_OBJECTS.ref(printer)
        ctx.minibuffer.show_info("printing...")
        ctx.buffer.print(printer, notif)
