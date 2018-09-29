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
from .. import url_opener


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


class Opener(object):
    CURRENT_BUFFER = 1
    NEW_BUFFER = 2

    def __init__(self, prompt_ctor):
        self.prompt_ctor = prompt_ctor

    def prompt_open(self, method, ctx):
        prompt = self.prompt_ctor(ctx)
        if method == self.NEW_BUFFER:
            prompt.label += " (new buffer)"
        return prompt

    def open(self, method, ctx, prompt, url):
        opts = {}
        if method == self.NEW_BUFFER:
            opts["new_buffer"] = True
        url_opener.url_open(ctx, url, **opts)

    def closed(self, method, ctx, prompt):
        pass

    def run(self, method, ctx):
        prompt = self.prompt_open(method, ctx)
        url = ctx.minibuffer.do_prompt(prompt)
        if url:
            self.open(method, ctx, prompt, url)
        self.closed(method, ctx, prompt)


def register_prompt_opener_commands(name, opener, doc):
    if not isinstance(opener, Opener):
        opener = Opener(opener)

    @define_command(name + "-new-buffer")
    def open_new_buffer(ctx):
        opener.run(Opener.NEW_BUFFER, ctx)

    @define_command(name)
    def open(ctx):
        if ctx.current_prefix_arg == (4,):
            return open_new_buffer(ctx)

        opener.run(Opener.CURRENT_BUFFER, ctx)

    open.__name__ = name.replace("-", "_")
    open_new_buffer.__name__ = open.__name__ + "_new_buffer"

    open.__doc__ = doc + "."
    open_new_buffer.__doc__ = doc + " in a new buffer."
