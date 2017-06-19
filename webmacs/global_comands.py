from .commands import define_command, CommandsListPrompt, COMMANDS
from .application import Application
from .keymap import global_key_map
from .window import current_window


def register_global_commands():
    keymap = global_key_map()

    @define_command("quit")
    def quit():
        Application.INSTANCE.quit()

    @define_command("M-x", prompt=CommandsListPrompt, visible=False)
    def commands(name):
        try:
            COMMANDS[name]()
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

    keymap.define_key("C-x C-c", "quit")
    keymap.define_key("M-x", "M-x")
