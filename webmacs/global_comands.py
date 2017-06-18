from .commands import define_command, CommandsListPrompt, COMMANDS
from .application import Application
from .keymap import global_key_map


def register_global_commands():
    keymap = global_key_map()

    @define_command("quit")
    def quit():
        Application.INSTANCE.quit()

    @define_command("M-x", prompt=CommandsListPrompt, visible=False)
    def commands(name):
        COMMANDS[name]()

    keymap.define_key("C-x C-c", "quit")
    keymap.define_key("M-x", "M-x")
