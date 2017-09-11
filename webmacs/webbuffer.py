import logging

from PyQt5.QtCore import QUrl, pyqtSlot as Slot
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineScript
from PyQt5.QtWebChannel import QWebChannel

from .keymaps import Keymap
from .window import current_window
from .webview import FullScreenWindow
from .content_handler import WebContentHandler


BUFFERS = []
KEYMAP = Keymap("webbuffer")


def current_buffer():
    return current_window().current_web_view().buffer()


def buffers():
    return BUFFERS


def create_buffer(url=None):
    return WebBuffer(url)


def close_buffer(wb):
    if len(BUFFERS) < 2:
        return  # can't close if there is only one buffer left

    if wb.view():
        # buffer is currently visible, search for a buffer that is not visible
        # yet to put it in the view
        invisibles = [b for b in BUFFERS if not b.view()]
        if not invisibles:
            # all buffers have views, so close the view of our buffer first
            current_window().close_view(wb.view())
        else:
            # associate the first buffer that does not have any view yet
            wb.view().setBuffer(invisibles[0])

    BUFFERS.remove(wb)
    return True


class WebBuffer(QWebEnginePage):
    """
    Represent some web page content.
    """

    LOGGER = logging.getLogger("webcontent")
    JSLEVEL2LOGGING = {
        QWebEnginePage.InfoMessageLevel: logging.INFO,
        QWebEnginePage.WarningMessageLevel: logging.WARNING,
        QWebEnginePage.ErrorMessageLevel: logging.ERROR,
    }

    def __init__(self, url=None):
        QWebEnginePage.__init__(self)
        BUFFERS.append(self)

        self.fullScreenRequested.connect(self._on_full_screen_requested)
        self._content_handler = WebContentHandler(self)
        channel = QWebChannel(self)
        channel.registerObject("contentHandler", self._content_handler)

        self.setWebChannel(channel,
                           QWebEngineScript.ApplicationWorld)

        if url:
            self.load(url)

    def load(self, url):
        if not isinstance(url, QUrl):
            url = QUrl(url)
        return QWebEnginePage.load(self, url)

    @property
    def content_handler(self):
        return self._content_handler

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
            "   clickLike(hints.activeHint.obj);"
            "   true;"
            " } else {false}",
            QWebEngineScript.ApplicationWorld)

    def select_visible_hint(self, hint_id):
        current_buffer().runJavaScript(
            "hints.selectVisibleHint(%r);" % hint_id,
            QWebEngineScript.ApplicationWorld)

    @Slot("QWebEngineFullScreenRequest")
    def _on_full_screen_requested(self, request):
        view = self.view()
        if not view:
            return
        fsw = view.window.fullscreen_window

        if request.toggleOn():
            if fsw:
                return
            request.accept()
            view.window.fullscreen_window = FullScreenWindow(view.window)
            view.window.fullscreen_window.enable(view)
        else:
            if not fsw:
                return
            request.accept()
            fsw.disable()
            view.window.fullscreen_window = None

    def createWindow(self, type):
        buffer = create_buffer()
        self.view().setBuffer(buffer)
        return buffer


KEYMAP.define_key("g", "go-to")
KEYMAP.define_key("S-g", "go-to-selected-url")
KEYMAP.define_key("b", "buffer-history")
KEYMAP.define_key("S-f", "go-forward")
KEYMAP.define_key("S-b", "go-backward")
KEYMAP.define_key("C-s", "i-search-forward")
KEYMAP.define_key("C-r", "i-search-backward")
KEYMAP.define_key("C-n", "scroll-down")
KEYMAP.define_key("C-p", "scroll-up")
KEYMAP.define_key("n", "scroll-down")
KEYMAP.define_key("p", "scroll-up")
KEYMAP.define_key("C-v", "scroll-page-down")
KEYMAP.define_key("M-v", "scroll-page-up")
KEYMAP.define_key("M->", "scroll-bottom")
KEYMAP.define_key("M-<", "scroll-top")
KEYMAP.define_key("f", "follow")
KEYMAP.define_key("M-w", "webcontent-copy")
KEYMAP.define_key("r", "reload-buffer")
KEYMAP.define_key("S-r", "reload-buffer-no-cache")
KEYMAP.define_key("h", "visited-links-history")
KEYMAP.define_key("q", "close-buffer")


from .webcontent_edit_keymap import KEYMAP as CONTENT_EDIT_KEYMAP
