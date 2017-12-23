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

from PyQt5.QtCore import QStringListModel, QModelIndex
import itertools

from . import define_command, COMMANDS
from ..minibuffer import Prompt, KEYMAP
from ..minibuffer.prompt import PromptTableModel, PromptHistory
from ..application import app
from ..webbuffer import create_buffer
from ..keymaps import Keymap
from ..keyboardhandler import current_prefix_arg
from .. import current_minibuffer, BUFFERS, current_window, current_buffer


class CommandsListPrompt(Prompt):
    label = "M-x: "
    complete_options = {
        "match": Prompt.FuzzyMatch,
        "complete-empty": True,
    }
    history = PromptHistory()

    def validate(self, name):
        return name

    def completer_model(self):
        model = QStringListModel(self)
        model.setStringList(sorted(k for k, v in COMMANDS.items()
                                   if v.visible))
        return model


@define_command("quit")
def quit():
    """
    Quit the application.
    """
    app().quit()


@define_command("M-x", prompt=CommandsListPrompt, visible=False)
def commands(prompt):
    """
    Prompt for a command name to execute.
    """
    try:
        COMMANDS[prompt.value()]()
    except KeyError:
        pass


@define_command("toggle-fullscreen")
def toggle_fullscreen():
    """
    Toggle fullscreen state of the current window.
    """
    win = current_window()
    if not win:
        return
    if win.isFullScreen():
        win.showNormal()
    else:
        win.showFullScreen()


@define_command("toggle-maximized")
def toggle_maximised():
    """
    Toggle maximised state of the current window.
    """
    win = current_window()
    if not win:
        return
    if win.isMaximized():
        win.showNormal()
    else:
        win.showMaximized()


def _get_or_create_buffer(win):
    current_buffer = win.current_web_view().buffer()

    if len(BUFFERS) >= len(win.webviews()) and current_buffer in BUFFERS:
        buffers = itertools.cycle(BUFFERS)
        while True:
            if next(buffers) == current_buffer:
                return next(buffers)

    return create_buffer(url=current_buffer.url())


@define_command("split-view-right")
def split_window_right():
    """
    Create a new view on right of the current one.
    """
    win = current_window()
    view = win.create_webview_on_right()
    view.setBuffer(_get_or_create_buffer(win))
    view.set_current()


@define_command("split-view-bottom")
def split_window_bottom():
    """
    Create a new view below the current one.
    """
    win = current_window()
    view = win.create_webview_on_bottom()
    view.setBuffer(_get_or_create_buffer(win))
    view.set_current()


@define_command("other-view")
def other_view():
    """
    Focus on the next view.
    """
    win = current_window()
    win.other_view()


@define_command("close-view")
def close_view():
    """
    Close the current view.
    """
    window = current_window()
    window.close_view(window.current_web_view())


@define_command("maximise-view")
def maximise_view():
    """
    Close all the views in the current window except the current one.
    """
    win = current_window()
    win.close_other_views()


@define_command("toggle-ad-block")
def toggle_ad_block():
    """
    Toggle ad blocking on or off.
    """
    from .webbuffer import reload_buffer_no_cache

    app().url_interceptor().toggle_use_adblock()
    reload_buffer_no_cache()


class VisitedLinksModel(PromptTableModel):
    def __init__(self, parent):
        visitedlinks = app().visitedlinks()
        PromptTableModel.__init__(self, visitedlinks.visited_urls())
        self.visitedlinks = visitedlinks

    def remove_history_entry(self, index):
        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        self.visitedlinks.remove(self._data.pop(index.row())[0])
        self.endRemoveRows()


VISITEDLINKS_KEYMAP = Keymap("visited-links-list", parent=KEYMAP)


class VisitedLinksPrompt(Prompt):
    label = "Find url from visited links:"
    complete_options = {
        "match": Prompt.FuzzyMatch,
        "complete-empty": True,
    }
    keymap = VISITEDLINKS_KEYMAP

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        self.new_buffer = current_prefix_arg() == (4,)
        if self.new_buffer:
            minibuffer.label.setText(minibuffer.label.text() + " (new buffer)")

    def completer_model(self):
        return VisitedLinksModel(self)

    def get_buffer(self):
        if self.new_buffer:
            buf = create_buffer()
            view = current_window().current_web_view()
            view.setBuffer(buf)
        else:
            buf = current_buffer()
        return buf


@VISITEDLINKS_KEYMAP.define_key("C-k")
def visited_links_remove_entry():
    pinput = current_minibuffer().input()

    selection = pinput.popup().selectionModel().currentIndex()
    if not selection.isValid():
        return

    selection = selection.model().mapToSource(selection)
    pinput.completer_model().remove_history_entry(selection)


@define_command("visited-links-history", prompt=VisitedLinksPrompt)
def visited_links_history(prompt):
    """
    Prompt to open a link previously visited.
    """
    index = prompt.index()
    if index.isValid():
        url = index.internalPointer()
        prompt.get_buffer().load(url)
