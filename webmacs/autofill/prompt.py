from ..minibuffer.prompt import YesNoPrompt, Prompt
from ..keyboardhandler import set_global_keymap_enabled


class SavePasswordPrompt(YesNoPrompt):
    def __init__(self, autofill, buffer, formdata):
        YesNoPrompt.__init__(self, "Save password ?", buffer)
        self.buffer = buffer
        self.autofill = autofill
        self.formdata = formdata
        self.closed.connect(self.__on_closed)

    def __on_closed(self):
        self.deleteLater()
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
