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

from ..minibuffer import Prompt
from .. import COMMANDS


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

    def __call__(self, ctx):
        if self.prompt:
            prompt = self.prompt(ctx)

            def call():
                ctx.prompt = prompt
                try:
                    self.binding(ctx)
                finally:
                    # to avoid reference cycle
                    ctx.prompt = None

            prompt.finished.connect(call)
            ctx.minibuffer.do_prompt(prompt)
        else:
            self.binding(ctx)


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
