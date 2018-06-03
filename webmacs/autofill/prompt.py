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

from ..minibuffer.prompt import YesNoNeverPrompt, Prompt
from ..keyboardhandler import set_global_keymap_enabled


class SavePasswordPrompt(YesNoNeverPrompt):
    def __init__(self, autofill, buffer, formdata):
        YesNoNeverPrompt.__init__(self, "Save password ?", buffer)
        self.buffer = buffer
        self.autofill = autofill
        self.formdata = formdata
        self.closed.connect(self.__on_closed)

    def __on_closed(self):
        # late import to avoid cyclic dependencies
        from . import FormData
        self.deleteLater()
        if self.never:
            # save the form with no password or data
            self.formdata = FormData(
                url=self.formdata.url, username=self.formdata.username, password=None, data=None)
            self.autofill.add_form_entry(self.buffer.url(), self.formdata)
        if self.yes:
            self.autofill.add_form_entry(self.buffer.url(), self.formdata)


class AskPasswordPrompt(Prompt):
    def __init__(self, autofill, buffer):
        Prompt.__init__(self)
        self.autofill = autofill
        self.buffer = buffer
        self.username, self.password = "", ""
        self.label = "username: "
        set_global_keymap_enabled(False)

    def _on_edition_finished(self):
        input = self.minibuffer.input()
        if not self.username:
            self.username = input.text()
            input.clear()
            input.setEchoMode(input.Password)
            self.minibuffer.label.setText("password: ")
        else:
            self.password = input.text()
            Prompt._on_edition_finished(self)
            set_global_keymap_enabled(True)
