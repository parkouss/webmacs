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

from PyQt5.QtCore import QStringListModel

from ..application import app
from ..minibuffer import Prompt
from ..ipc import IpcServer
from ..minibuffer.prompt import PromptHistory
from . import define_command


class InstancesListPrompt(Prompt):
    label = "webmacs instances: "
    complete_options = {
        "match": Prompt.FuzzyMatch,
    }
    history = PromptHistory()
    exclude_self_instance = True

    def __init__(self, ctx):
        super().__init__(ctx)
        instances = IpcServer.list_all_instances(check=False)
        if self.exclude_self_instance:
            current = app().instance_name
            instances = [i for i in instances if i != current]
        self.instances = instances

    def completer_model(self):
        model = QStringListModel(self)
        model.setStringList(self.instances)
        return model


class OpenInInstancePrompt(InstancesListPrompt):
    label = "open in instance: "


@define_command("raise-instance")
def raise_instance(ctx):
    """
    Raise the current window of the selected instance.
    """
    prompt = InstancesListPrompt(ctx)
    if not prompt.instances:
        ctx.minibuffer.show_info("There is only one instance running: %s"
                                 % app().instance_name)
    else:
        value = ctx.minibuffer.do_prompt(prompt)
        if value:
            IpcServer.instance_send(value, {})


@define_command("current-instance")
def current_instance(ctx):
    """
    Show the current instance name.
    """
    ctx.minibuffer.show_info("Current instance name: %s" % app().instance_name)
