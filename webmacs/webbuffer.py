from PyQt5.QtCore import QUrl, pyqtSlot as Slot, QAbstractTableModel, \
    QModelIndex, Qt
import logging
from PyQt5.QtWebEngineWidgets import QWebEnginePage

from .keymap import Keymap
from .commands import define_command
from .window import current_window
from .minibuffer import Prompt


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

    def __init__(self):
        QWebEnginePage.__init__(self)
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

    def content_edit_keymap(self):
        return CONTENT_EDIT_KEYMAP

    def async_scroll_pos(self, func):
        self.runJavaScript("[window.pageXOffset, window.pageYOffset]", func)

    def set_scroll_pos(self, x=0, y=0):
        self.runJavaScript("window.scrollTo(%d, %d);" % (x, y))

    def scroll_by(self, x=0, y=0):
        self.runJavaScript("window.scrollBy(%d, %d);" % (x, y))

    def scroll_page(self, nb):
        offset = -40 if nb > 0 else 40
        self.runJavaScript("""""
        window.scrollTo(0, window.pageYOffset
                        + (window.innerHeight * %d) + %d);
        """ % (nb, offset))

    def scroll_top(self):
        self.runJavaScript("window.scrollTo(0, 0);")

    def scroll_bottom(self):
        self.runJavaScript("window.scrollTo(0, document.body.scrollHeight);")


class BufferTableModel(QAbstractTableModel):
    def __init__(self):
        QAbstractTableModel.__init__(self)
        self._buffers = BUFFERS[:]

    def rowCount(self, index=QModelIndex()):
        return len(self._buffers)

    def columnCount(self, index=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        buff = index.internalPointer()
        if not buff:
            return

        col = index.column()
        if role == Qt.DisplayRole:
            if col == 0:
                return buff.url().toString()
            else:
                return buff.title()
        elif role == Qt.DecorationRole and col == 0:
            return buff.icon()

    def index(self, row, col, parent=QModelIndex()):
        try:
            return self.createIndex(row, col, self._buffers[row])
        except IndexError:
            return QModelIndex()


class BufferListPrompt(Prompt):
    label = "switch buffer:"
    complete_options = {
        "match": Prompt.FuzzyMatch,
        "complete-empty": True,
    }

    def completer_model(self):
        return BufferTableModel()


@define_command("switch-buffer", prompt=BufferListPrompt)
def switch_buffer(prompt):
    selected = prompt.index()
    if selected.row() >= 0:
        view = current_window().current_web_view()
        view.setBuffer(selected.internalPointer())


@define_command("go-forward")
def go_forward():
    current_buffer().triggerAction(WebBuffer.Forward)


@define_command("go-backward")
def go_backward():
    current_buffer().triggerAction(WebBuffer.Back)


from .isearch import ISearchPrompt  # noqa


@define_command("i-search-forward", prompt=ISearchPrompt)
def i_search_forward(prompt):
    print("scroll pos: ", prompt.page_scroll_pos)


@define_command("scroll-down")
def scroll_down():
    current_buffer().scroll_by(y=20)


@define_command("scroll-up")
def scroll_up():
    current_buffer().scroll_by(y=-20)


@define_command("scroll-page-down")
def scroll_page_down():
    current_buffer().scroll_page(1)


@define_command("scroll-page-up")
def scroll_page_up():
    current_buffer().scroll_page(-1)


@define_command("scroll-top")
def scroll_top():
    current_buffer().scroll_top()


@define_command("scroll-bottom")
def scroll_bottom():
    current_buffer().scroll_bottom()


KEYMAP.define_key("g", "go-to")
KEYMAP.define_key("S-f", "go-forward")
KEYMAP.define_key("S-b", "go-backward")
KEYMAP.define_key("C-s", "i-search-forward")
KEYMAP.define_key("C-n", "scroll-down")
KEYMAP.define_key("C-p", "scroll-up")
KEYMAP.define_key("C-v", "scroll-page-down")
KEYMAP.define_key("M-v", "scroll-page-up")
KEYMAP.define_key("M->", "scroll-bottom")
KEYMAP.define_key("M-<", "scroll-top")


@KEYMAP.define_key("f")
def f():
    from PyQt5.QtWebEngineWidgets import QWebEngineScript
    selector = "a[href], input:not([hidden]), textarea:not([hidden])"
    current_buffer().runJavaScript(
        "hints.selectBrowserObjects(%r);" % selector,
        QWebEngineScript.ApplicationWorld)

from .webcontent_edit_keymap import KEYMAP as CONTENT_EDIT_KEYMAP
