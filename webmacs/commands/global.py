from PyQt5.QtCore import QStringListModel, QModelIndex
import itertools

from . import define_command, COMMANDS
from ..minibuffer import Prompt, KEYMAP
from ..minibuffer.prompt import PromptTableModel
from ..application import app
from ..window import current_window
from ..webbuffer import create_buffer, BUFFERS, current_minibuffer
from ..keymaps import Keymap


class CommandsListPrompt(Prompt):
    label = "M-x: "
    complete_options = {
        "match": Prompt.FuzzyMatch,
        "complete-empty": True,
    }

    def validate(self, name):
        return name

    def completer_model(self):
        model = QStringListModel(self)
        model.setStringList(sorted(k for k, v in COMMANDS.items()
                                   if v.visible))
        return model


@define_command("quit")
def quit():
    app().quit()


@define_command("M-x", prompt=CommandsListPrompt, visible=False)
def commands(prompt):
    try:
        COMMANDS[prompt.value()]()
    except KeyError:
        pass


@define_command("toggle-fullscreen")
def toggle_fullscreen():
    win = current_window()
    if not win:
        return
    if win.isFullScreen():
        win.showNormal()
    else:
        win.showFullScreen()


@define_command("toggle-maximized")
def toggle_maximised():
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
    win = current_window()
    view = win.create_webview_on_right()
    view.setBuffer(_get_or_create_buffer(win))
    view.set_current()


@define_command("split-view-bottom")
def split_window_bottom():
    win = current_window()
    view = win.create_webview_on_bottom()
    view.setBuffer(_get_or_create_buffer(win))
    view.set_current()


@define_command("other-view")
def other_view():
    win = current_window()
    win.other_view()


@define_command("close-view")
def close_view():
    window = current_window()
    window.close_view(window.current_web_view())


@define_command("maximise-view")
def maximise_view():
    win = current_window()
    win.close_other_views()


@define_command("toggle-ad-block")
def toggle_ad_block():
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

    def completer_model(self):
        return VisitedLinksModel(self)


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
    index = prompt.index()
    if index.isValid():
        url = index.internalPointer()
        current_window().current_web_view().buffer().load(url)
