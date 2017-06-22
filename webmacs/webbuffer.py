from PyQt5.QtCore import QUrl, pyqtSlot as Slot
import logging
from PyQt5.QtWebEngineWidgets import QWebEnginePage

from .keymap import Keymap
from .commands import define_command
from .window import current_window
from .minibuffer import Prompt, PromptTableModel


BUFFERS = []
KEYMAP = Keymap("webbuffer")


def current_buffer():
    return current_window().current_web_view().buffer()


def buffers():
    return BUFFERS


class WebBuffer(QWebEnginePage):
    """
    Represent some web page content.

    Note a parent is required, else a segmentation fault may happen when the
    application closes.
    """

    LOGGER = logging.getLogger("webcontent")
    JSLEVEL2LOGGING = {
        QWebEnginePage.InfoMessageLevel: logging.INFO,
        QWebEnginePage.WarningMessageLevel: logging.WARNING,
        QWebEnginePage.ErrorMessageLevel: logging.ERROR,
    }

    def __init__(self, parent):
        QWebEnginePage.__init__(self, parent)
        BUFFERS.append(self)
        self.destroyed.connect(self._on_destroyed)

    @Slot()
    def _on_destroyed(self):
        BUFFERS.remove(self)

    def load(self, url):
        if not isinstance(url, QUrl):
            url = QUrl(url)
        return QWebEnginePage.load(self, url)

    def javaScriptConsoleMessage(self, level, message, lineno, source):
        logger = self.LOGGER
        # small speed improvement, avoid to log if unnecessary
        if logger.level < logging.CRITICAL:
            level = self.JSLEVEL2LOGGING.get(level, logging.ERROR)
            logger.log(level, message, extra={"url": self.url().toString()})

    def keymap(self):
        return KEYMAP


class BufferListPrompt(Prompt):
    label = "switch buffer:"
    complete_options = {
        "match": Prompt.FuzzyMatch,
    }

    def completer_model(self):
        blist = []
        for buf in BUFFERS:
            blist.append((buf.url(), buf.title()))
        return PromptTableModel(blist)


@define_command("switch-buffer", prompt=BufferListPrompt)
def switch_buffer(value):
    print(value)


@define_command("go-forward")
def go_forward():
    current_buffer().triggerAction(WebBuffer.Forward)


@define_command("go-backward")
def go_backward():
    current_buffer().triggerAction(WebBuffer.Back)


KEYMAP.define_key("g", "go-to")
KEYMAP.define_key("S-f", "go-forward")
KEYMAP.define_key("S-b", "go-backward")
