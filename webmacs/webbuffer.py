import logging

from PyQt5.QtCore import QUrl, pyqtSlot as Slot, QEventLoop
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineScript
from PyQt5.QtWebChannel import QWebChannel

from .keymaps import Keymap, KeyPress
from . import current_window, BUFFERS, current_minibuffer, \
    minibuffer_show_info, current_buffer
from .content_handler import WebContentHandler
from .application import app
from .minibuffer.prompt import YesNoPrompt
from .autofill import FormData
from .autofill.prompt import AskPasswordPrompt, SavePasswordPrompt
from .keyboardhandler import send_key_event
from .webcontent_edit_keymap import KEYMAP as CONTENT_EDIT_KEYMAP


KEYMAP = Keymap("webbuffer")


def create_buffer(url=None):
    return WebBuffer(url)


def close_buffer(wb, keep_one=True):
    if keep_one and len(BUFFERS) < 2:
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

    app().download_manager().detach_buffer(wb)
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
        # put the most recent buffer at the beginning of the BUFFERS list
        BUFFERS.insert(0, self)

        self.fullScreenRequested.connect(self._on_full_screen_requested)
        self._content_handler = WebContentHandler(self)
        channel = QWebChannel(self)
        channel.registerObject("contentHandler", self._content_handler)

        self.setWebChannel(channel,
                           QWebEngineScript.ApplicationWorld)

        self.loadFinished.connect(self.finished)
        self.authenticationRequired.connect(self.handle_authentication)
        self.linkHovered.connect(self.on_url_hovered)
        self.titleChanged.connect(self.on_title_changed)
        self.__authentication_data = None

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
        if view.request_fullscreen(request.toggleOn()):
            request.accept()

    def createWindow(self, type):
        buffer = create_buffer()
        self.view().setBuffer(buffer)
        return buffer

    def finished(self):
        url = self.url()
        if url.isValid() and not url.scheme() == "webmacs":
            app().visitedlinks().visit(url.toString(), self.title())

        autofill = app().autofill()
        if self.__authentication_data:
            # save authentication data
            sprompt = SavePasswordPrompt(autofill, self,
                                         self.__authentication_data)
            self.__authentication_data = None
            current_minibuffer().do_prompt(sprompt)
        else:
            autofill.complete_buffer(self, url)

        if url.scheme() == "webmacs" and url.authority() == "downloads":
            app().download_manager().attach_buffer(self)
        else:
            app().download_manager().detach_buffer(self)

    def handle_authentication(self, url, authenticator):
        autofill = app().autofill()
        passwords = autofill.auth_passwords_for_url(url)
        if passwords:
            data = passwords[0]
            authenticator.setUser(data.username)
            authenticator.setPassword(data.password)
            return

        # ask authentication credentials
        loop = QEventLoop()
        prompt = AskPasswordPrompt(autofill, self)
        current_minibuffer().do_prompt(prompt)

        def save_auth():
            data = self.__authentication_data = FormData(url, prompt.username,
                                                         prompt.password, None)
            authenticator.setUser(data.username)
            authenticator.setPassword(data.password)
            loop.quit()

        prompt.closed.connect(save_auth)

        loop.exec_()

    def certificateError(self, error):
        url = "{}:{}".format(error.url().host(), error.url().port(80))
        db = app().ignored_certs()
        if db.is_ignored(url):
            return True

        loop = QEventLoop()
        prompt = YesNoPrompt("[certificate error] {} - ignore ? "
                             .format(error.errorDescription()))
        current_minibuffer().do_prompt(prompt)

        prompt.closed.connect(loop.quit)
        loop.exec_()
        if prompt.yes:
            db.ignore(url)
        return prompt.yes

    def javaScriptConfirm(self, url, msg):
        loop = QEventLoop()
        prompt = YesNoPrompt("[js-confirm] {} ".format(msg))
        current_minibuffer().do_prompt(prompt)

        prompt.closed.connect(loop.quit)
        loop.exec_()
        return prompt.yes

    def javaScriptAlert(self, url, msg):
        msg = "[js-alert] {}".format(msg)
        app().minibuffer_show_info(msg)

    def on_url_hovered(self, url):
        minibuffer_show_info(url)

    def on_title_changed(self, title):
        current_window().setWindowTitle("{} - Webmacs".format(title))


KEYMAP.define_key("g", "go-to")
KEYMAP.define_key("G", "go-to-selected-url")
KEYMAP.define_key("b", "buffer-history")
KEYMAP.define_key("F", "go-forward")
KEYMAP.define_key("B", "go-backward")
KEYMAP.define_key("C-s", "i-search-forward")
KEYMAP.define_key("C-r", "i-search-backward")
KEYMAP.define_key("C-v", "scroll-page-down")
KEYMAP.define_key("M-v", "scroll-page-up")
KEYMAP.define_key("M->", "scroll-bottom")
KEYMAP.define_key("M-<", "scroll-top")
KEYMAP.define_key("f", "follow")
KEYMAP.define_key("M-w", "webcontent-copy")
KEYMAP.define_key("r", "reload-buffer")
KEYMAP.define_key("R", "reload-buffer-no-cache")
KEYMAP.define_key("h", "visited-links-history")
KEYMAP.define_key("q", "close-buffer")


@KEYMAP.define_key("C-n")
@KEYMAP.define_key("n")
def send_down():
    send_key_event(KeyPress.from_str("Down"))


@KEYMAP.define_key("C-p")
@KEYMAP.define_key("p")
def send_up():
    send_key_event(KeyPress.from_str("Up"))


@KEYMAP.define_key("C-f")
def send_right():
    send_key_event(KeyPress.from_str("Right"))


@KEYMAP.define_key("C-b")
def send_left():
    send_key_event(KeyPress.from_str("Left"))
