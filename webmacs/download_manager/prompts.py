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

import os

from ..minibuffer.prompt import Prompt, FSModel, PromptTableModel


class DlChooseActionPrompt(Prompt):
    complete_options = {
        "match": Prompt.FuzzyMatch,
        "complete-empty": True,
    }
    value_return_index_data = True

    def __init__(self, path, mimetype):
        Prompt.__init__(self, None)
        self.__actions = [
            ("download", "download file on disk"),
            ("open", "open file with external command"),
        ]
        name = os.path.basename(path)
        if len(name) > 33:
            name = name[:30] + "..."
        self.label = "File {} [{}]: ".format(name, mimetype)

    def completer_model(self):
        return PromptTableModel(self.__actions)

    def enable(self, minibuffer):
        super().enable(minibuffer)
        minibuffer.input().popup().selectRow(0)


class DlOpenActionPrompt(Prompt):
    complete_options = {
        "match": Prompt.FuzzyMatch,
        "complete-empty": True,
    }
    label = "Open file with:"
    value_return_index_data = True

    def __init__(self):
        Prompt.__init__(self, None)

    def completer_model(self):
        return PromptTableModel([[e] for e in list_executables()])


class DlPrompt(Prompt):
    complete_options = {
        "autocomplete": True
    }

    def __init__(self, path, mimetype):
        Prompt.__init__(self, None)
        self.label = "Download file [{}]:".format(mimetype)
        self._dlpath = path

    def completer_model(self):
        # todo, not working
        model = FSModel(self)
        return model

    def enable(self, minibuffer):
        super().enable(minibuffer)
        minibuffer.input().setText(self._dlpath)


def list_executables():
    try:
        paths = os.environ["PATH"].split(os.pathsep)
    except KeyError:
        return []

    executables = []
    for path in paths:
        try:
            for file_ in os.listdir(path):
                if os.access(os.path.join(path, file_), os.X_OK):
                    executables.append(file_)
        except Exception:
            pass

    return executables
