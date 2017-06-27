from PyQt5.QtCore import QStringListModel

from . import define_command, COMMANDS
from ..minibuffer import Prompt
from ..application import Application
from ..window import current_window


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
