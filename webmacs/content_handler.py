import json

from PyQt5.QtCore import QObject, pyqtSlot as Slot, pyqtSignal as Signal

from .window import current_window
from .keyboardhandler import LOCAL_KEYMAP_SETTER
from .minibuffer import YesNoPrompt, current_minibuffer


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
        prompt = YesNoPrompt("Save password ?",
                             parent=self.buffer)
        prompt.closed.connect(prompt.deleteLater)
        current_minibuffer().do_prompt(prompt)
