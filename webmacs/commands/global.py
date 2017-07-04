from PyQt5.QtCore import QStringListModel
import itertools

from . import define_command, COMMANDS
from ..minibuffer import Prompt
from ..application import Application
from ..window import current_window
from ..webbuffer import create_buffer, BUFFERS


class CommandsListPrompt(Prompt):
    label = "M-x: "
    complete_options = {
        "match": Prompt.FuzzyMatch,
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
    Application.INSTANCE.quit()


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
    views = win.webviews()
    index = views.index(win.current_web_view())
    index = index + 1
    if index >= len(views):
        index = 0
    views[index].set_current()


@define_command("close-view")
def close_view():
    view = current_window().current_web_view()
    other_view()
    current_window().delete_webview(view)


@define_command("maximise-view")
def maximise_view():
    win = current_window()
    view = win.current_web_view()
    for other in win.webviews():
        if view != other:
            win.delete_webview(other)


@define_command("toggle-ad-block")
def toggle_ad_block():
    from .webbuffer import reload_buffer_no_cache

    Application.INSTANCE.url_interceptor().toggle_use_adblock()
    reload_buffer_no_cache()


class VisitedLinksPrompt(Prompt):
    label = "Find url from visited links:"
    complete_options = {
        "match": Prompt.FuzzyMatch,
    }

    def completer_model(self):
        model = QStringListModel(self)
        model.setStringList(Application.INSTANCE.visitedlinks().visited_urls())
        return model


@define_command("visited-links-history", prompt=VisitedLinksPrompt)
def visited_links_history(prompt):
    index = prompt.index()
    url = index.model().data(index)
    current_window().current_web_view().buffer().load(url)
