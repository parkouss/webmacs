from PyQt5.QtCore import QStringListModel

from . import define_command, COMMANDS
from ..minibuffer import Prompt
from ..application import Application
from ..window import current_window
from ..webbuffer import WebBuffer


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


@define_command("split-view-right")
def split_window_right():
    win = current_window()
    current_buffer = win.current_web_view().buffer()
    view = win.create_webview_on_right()
    buffer = WebBuffer()
    buffer.load(current_buffer.url())
    view.setBuffer(buffer)
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
