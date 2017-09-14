import json

from PyQt5.QtCore import QObject, pyqtSlot as Slot, pyqtSignal as Signal, \
    QUrl

from .window import current_window
from .keyboardhandler import LOCAL_KEYMAP_SETTER
from .minibuffer import current_minibuffer
from .minibuffer.prompt import YesNoPrompt
from .autofill import FormData


class SavePasswordPrompt(YesNoPrompt):
    def __init__(self, parent, formdata):
        YesNoPrompt.__init__(self, "Save password ?", parent)
        self.formdata = formdata
        self.closed.connect(self.__on_closed)

    def __on_closed(self):
        self.deleteLater()
        print("closed!")


class WebContentHandler(QObject):
    """
    Interface to communicate with the javascript side in the web pages.
    """
    browserObjectActivated = Signal(dict)

    def __init__(self, buff):
        QObject.__init__(self)
        self.buffer = buff

    @Slot(bool)
    def onTextFocus(self, enabled):
        win = current_window()
        LOCAL_KEYMAP_SETTER.web_content_edit_focus_changed(win, enabled)

    @Slot(str)
    def _browserObjectActivated(self, obj):
        # It is hard to pass dict objects from javascript, so a string is used
        # and decoded here.
        self.browserObjectActivated.emit(json.loads(obj))

    @Slot(str)
    def onBufferFocus(self):
        if self.buffer and self.buffer.view():
            self.buffer.view().set_current()

    @Slot(str)
    def copyToClipboard(self, text):
        from .application import Application

        Application.INSTANCE.clipboard().setText(text)

    @Slot(str, str, str, str)
    def autoFillFormSubmitted(self, url, username, password, data):
        print(url, username, password, data)
        formdata = FormData(url=QUrl(url), username=username,
                            password=password, data=data)
        prompt = SavePasswordPrompt(self.buffer, formdata)
        current_minibuffer().do_prompt(prompt)
