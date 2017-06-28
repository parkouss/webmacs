import logging

from PyQt5.QtCore import QUrl, pyqtSlot as Slot
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineScript

from .keymaps import Keymap
from .window import current_window


BUFFERS = []
ID_2_BUFFERS = {}
KEYMAP = Keymap("webbuffer")


def current_buffer():
    return current_window().current_web_view().buffer()


def buffers():
    return BUFFERS


def buffer_for_id(id):
    return ID_2_BUFFERS.get(id)


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
        bid = str(id(self))
        ID_2_BUFFERS[bid] = self
        self.destroyed.connect(self._on_destroyed)

        # register the buffer id
        script = QWebEngineScript()
        script.setInjectionPoint(QWebEngineScript.DocumentCreation)
        script.setSourceCode("webbuffer_id = %r;" % bid)
        script.setWorldId(QWebEngineScript.ApplicationWorld)
        self.scripts().insert(script)

    @Slot()
    def _on_destroyed(self):
        BUFFERS.remove(self)
        del ID_2_BUFFERS[id(self)]

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

    def start_select_browser_objects(self, selector):
        current_buffer().runJavaScript(
            "hints.selectBrowserObjects(%r);" % selector,
            QWebEngineScript.ApplicationWorld)

    def stop_select_browser_objects(self):
        current_buffer().runJavaScript(
            "hints.clearBrowserObjects();",
            QWebEngineScript.ApplicationWorld)

    def select_nex_browser_object(self, forward=True):
        current_buffer().runJavaScript(
            "hints.activateNextHint(%s);" % ("false" if forward else "true",),
            QWebEngineScript.ApplicationWorld)

    def filter_browser_objects(self, text):
        current_buffer().runJavaScript(
            "hints.filterSelection(%r);" % text,
            QWebEngineScript.ApplicationWorld)

    def focus_active_browser_object(self):
        current_buffer().runJavaScript(
            "if (hints.activeHint) {"
            "   hints.activeHint.obj.focus();"
            "   hints.activeHint.obj.click();"
            "   true;"
            " } else {false}",
            QWebEngineScript.ApplicationWorld)

    def select_visible_hint(self, hint_id):
        current_buffer().runJavaScript(
            "hints.selectVisibleHint(%r);" % hint_id,
            QWebEngineScript.ApplicationWorld)


KEYMAP.define_key("g", "go-to")
KEYMAP.define_key("b", "buffer-history")
KEYMAP.define_key("S-f", "go-forward")
KEYMAP.define_key("S-b", "go-backward")
KEYMAP.define_key("C-s", "i-search")
KEYMAP.define_key("C-r", "i-search")
KEYMAP.define_key("C-n", "scroll-down")
KEYMAP.define_key("C-p", "scroll-up")
KEYMAP.define_key("C-v", "scroll-page-down")
KEYMAP.define_key("M-v", "scroll-page-up")
KEYMAP.define_key("M->", "scroll-bottom")
KEYMAP.define_key("M-<", "scroll-top")
KEYMAP.define_key("f", "follow")
KEYMAP.define_key("M-w", "webcontent-copy")


from .webcontent_edit_keymap import KEYMAP as CONTENT_EDIT_KEYMAP
