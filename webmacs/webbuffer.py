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

import logging

from PyQt5.QtCore import QUrl, pyqtSlot as Slot, QEventLoop
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineScript
from PyQt5.QtWebChannel import QWebChannel
from collections import namedtuple

from .keymaps import KeyPress, BUFFER_KEYMAP as KEYMAP
from . import current_window, BUFFERS, current_minibuffer, \
    minibuffer_show_info, current_buffer
from .content_handler import WebContentHandler
from .application import app
from .minibuffer.prompt import YesNoPrompt
from .minibuffer import Minibuffer
from .autofill import FormData
from .autofill.prompt import AskPasswordPrompt, SavePasswordPrompt
from .keyboardhandler import send_key_event
from .keymaps.webcontent_edit import KEYMAP as CONTENT_EDIT_KEYMAP
from .keymaps.caret_browsing import KEYMAP as CARET_BROWSING_KEYMAP


# a tuple of QUrl, str to delay loading of a page.
DelayedLoadingUrl = namedtuple("DelayedLoadingUrl", ("url", "title"))


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
    wb.deleteLater()
    Minibuffer.update_rlabel()
    return True


class WebBuffer(QWebEnginePage):
    """
    Represent some web page content.
    """

    KEYMAP_MODE_NORMAL = 1
    KEYMAP_MODE_CONTENT_EDIT = 2
    KEYMAP_MODE_CARET_BROWSING = 3

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
        Minibuffer.update_rlabel()

        self.fullScreenRequested.connect(self._on_full_screen_requested)
        self._content_handler = WebContentHandler(self)
        channel = QWebChannel(self)
        channel.registerObject("contentHandler", self._content_handler)

        self.setWebChannel(channel,
                           QWebEngineScript.ApplicationWorld)

        self.loadFinished.connect(self.finished)
        self.authenticationRequired.connect(self.handle_authentication)
        self.linkHovered.connect(self.on_url_hovered)
        self.titleChanged.connect(self.update_title)
        self.__authentication_data = None
        self.__delay_loading_url = None
        self.__keymap_mode = self.KEYMAP_MODE_NORMAL

        if url:
            if isinstance(url, DelayedLoadingUrl):
                self.__delay_loading_url = url
            else:
                self.load(url)

    def load(self, url):
        if not isinstance(url, QUrl):
            url = QUrl(url)
        self.__delay_loading_url = None
        return QWebEnginePage.load(self, url)

    def delayed_loading_url(self):
        return self.__delay_loading_url

    def url(self):
        if self.__delay_loading_url:
            return self.__delay_loading_url.url
        return QWebEnginePage.url(self)

    def title(self):
        if self.__delay_loading_url:
            return self.__delay_loading_url.title
        return QWebEnginePage.title(self)

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

    def caret_browsing_keymap(self):
        return CARET_BROWSING_KEYMAP

    def active_keymap(self):
        mode = self.__keymap_mode
        if mode == self.KEYMAP_MODE_CONTENT_EDIT:
            return self.content_edit_keymap()
        elif mode == self.KEYMAP_MODE_CARET_BROWSING:
            return self.caret_browsing_keymap()
        return self.keymap()

    def keymap_mode(self):
        return self.__keymap_mode

    def set_keymap_mode(self, enabled):
        self.__keymap_mode = enabled

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
        minibuffer_show_info(msg)

    def on_url_hovered(self, url):
        minibuffer_show_info(url)

    def update_title(self, title=None):
        if self == current_buffer():
            current_window().update_title(
                title if title is not None else self.title()
            )


# alias to create a web buffer
create_buffer = WebBuffer


KEYMAP.define_key("g", "go-to")
KEYMAP.define_key("s", "search-default")
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
KEYMAP.define_key("c", "copy-link")
KEYMAP.define_key("M-w", "webcontent-copy")
KEYMAP.define_key("r", "reload-buffer")
KEYMAP.define_key("R", "reload-buffer-no-cache")
KEYMAP.define_key("h", "visited-links-history")
KEYMAP.define_key("q", "close-buffer")
KEYMAP.define_key("C-x h", "select-buffer-content")
KEYMAP.define_key("C", "caret-browsing-init")


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
