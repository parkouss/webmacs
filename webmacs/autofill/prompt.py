from ..minibuffer.prompt import YesNoPrompt


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
