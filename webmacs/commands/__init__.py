from PyQt5.QtCore import QObject, pyqtSlot as Slot

COMMANDS = {}


class CommandExecutor(QObject):
    """
    Internal object to execute commands when a prompt is used.
    """
    def __init__(self, cmd, prompt):
        QObject.__init__(self, prompt)
        self.cmd = cmd
        self.prompt = prompt

    @Slot()
    def call(self):
        self.cmd(self.prompt)


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
            prompt.finished.connect(executor.call)
            current_minibuffer().do_prompt(prompt)
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


from ..minibuffer import current_minibuffer, Prompt  # noqa

