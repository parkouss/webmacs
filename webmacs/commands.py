from PyQt5.QtCore import QObject, pyqtSlot as Slot, QStringListModel
from .minibuffer import Prompt, current_minibuffer

COMMANDS = {}


class CommandExecutor(QObject):
    """
    Internal object to execute commands when a prompt is used.
    """
    def __init__(self, cmd, parent=None):
        QObject.__init__(self, parent)
        self.cmd = cmd

    @Slot(object)
    def call(self, value):
        self.cmd(value)


class InteractiveCommand(object):
    """
    A command to interact with the system.

    A prompt class can be given to get an argument using the minibuffer prompt.

    :param binding: a callable to run when invoking the command.
    :param prompt: a Prompt derived class
    :param visible: whether or not to list the command using M-x
    """
    __slots__ = ("binding", "prompt", "visible")

    def __init__(self, binding, prompt=None, visible=True):
        self.binding = binding
        self.prompt = prompt
        self.visible = visible
        if prompt is not None:
            assert issubclass(prompt, Prompt), \
                "prompt should be a Prompt subclass"

    def __call__(self):
        if self.prompt:
            prompt = self.prompt()
            # executor will be destroyed with its parent, the prompt
            executor = CommandExecutor(self.binding, prompt)
            prompt.got_value.connect(executor.call)
            current_minibuffer().prompt(prompt)
        else:
            self.binding()


def define_command(name, binding=None, **args):
    """
    Register an interactive command.
    """
    command = InteractiveCommand(binding, **args)
    COMMANDS[name] = command
    if binding is None:
        def wrapper(func):
            command.binding = func
            return func
        return wrapper


class CommandsListPrompt(Prompt):
    label = "M-x: "

    def validate(self, name):
        return name

    def completer_model(self):
        model = QStringListModel(self)
        model.setStringList(sorted(k for k, v in COMMANDS.items()
                                   if v.visible))
        return model
