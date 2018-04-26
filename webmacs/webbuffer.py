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

from PyQt5.QtCore import QUrl, pyqtSlot as Slot
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineScript
from PyQt5.QtWebChannel import QWebChannel
from collections import namedtuple

from .keymaps import BUFFER_KEYMAP as KEYMAP
from . import hooks
from . import BUFFERS, current_minibuffer, minibuffer_show_info, current_buffer
from .content_handler import WebContentHandler
from .application import app
from .minibuffer.prompt import YesNoPrompt
from .autofill import FormData
from .autofill.prompt import AskPasswordPrompt, SavePasswordPrompt
from .keyboardhandler import LOCAL_KEYMAP_SETTER
from .mode import get_mode, Mode, get_auto_modename_for_url


# a tuple of QUrl, str to delay loading of a page.
DelayedLoadingUrl = namedtuple("DelayedLoadingUrl", ("url", "title"))


def close_buffer(wb, keep_one=True):
    if keep_one and len(BUFFERS) < 2:
        return  # can't close if there is only one buffer left

    view = wb.view()
    if view:
        # buffer is currently visible, search for a buffer that is not visible
        # yet to put it in the view
        invisibles = [b for b in BUFFERS if not b.view()]
        if not invisibles:
            # all buffers have views, so close the view of our buffer first
            view.main_window.close_view(view)
        else:
            # associate the first buffer that does not have any view yet
            view.setBuffer(invisibles[0])

    internal_view = wb.internal_view()
    if internal_view:
        internal_view.deleteLater()

    app().download_manager().detach_buffer(wb)
    BUFFERS.remove(wb)
    wb.deleteLater()
    hooks.webbuffer_closed(wb)
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
        hooks.webbuffer_created(self)

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
        self.__keymap_mode = Mode.KEYMAP_NORMAL
        self.__mode = get_mode("standard-mode")
        self.__text_edit_mark = False

        if url:
            if isinstance(url, DelayedLoadingUrl):
                self.__delay_loading_url = url
            else:
                self.load(url)

    def internal_view(self):
        return QWebEnginePage.view(self)

    def view(self):
        iv = self.internal_view()
        if iv:
            return iv.view()

    @property
    def mode(self):
        return self.__mode

    @property
    def text_edit_mark(self):
        return self.__text_edit_mark

    def set_text_edit_mark(self, on):
        self.__text_edit_mark = on

    def set_mode(self, modename):
        if self.__mode.name == modename:
            return
        old_mode = self.__mode
        self.__mode = get_mode(modename)
        LOCAL_KEYMAP_SETTER.buffer_mode_changed(self, old_mode)

    def load(self, url):
        if not isinstance(url, QUrl):
            url = QUrl.fromUserInput(url)
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

    def active_keymap(self):
        return self.mode.keymap_for_mode(self.__keymap_mode)

    @property
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
        internal_view = self.internal_view()
        if not internal_view:
            return
        if internal_view.request_fullscreen(request.toggleOn()):
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

        self.set_mode(get_auto_modename_for_url(self.url().toString()))

    def handle_authentication(self, url, authenticator):
        autofill = app().autofill()
        passwords = autofill.auth_passwords_for_url(url)
        if passwords:
            data = passwords[0]
            authenticator.setUser(data.username)
            authenticator.setPassword(data.password)
            return

        # ask authentication credentials
        prompt = AskPasswordPrompt(autofill, self)
        current_minibuffer().do_prompt(prompt)

        data = self.__authentication_data = FormData(url, prompt.username,
                                                     prompt.password, None)
        authenticator.setUser(data.username)
        authenticator.setPassword(data.password)

    def certificateError(self, error):
        url = "{}:{}".format(error.url().host(), error.url().port(80))
        db = app().ignored_certs()
        if db.is_ignored(url):
            return True

        prompt = YesNoPrompt("[certificate error] {} - ignore ? "
                             .format(error.errorDescription()))
        current_minibuffer().do_prompt(prompt)

        if prompt.yes:
            db.ignore(url)
        return prompt.yes

    def javaScriptConfirm(self, url, msg):
        return current_minibuffer().do_prompt(
            YesNoPrompt("[js-confirm] {} ".format(msg))
        )

    def javaScriptAlert(self, url, msg):
        msg = "[js-alert] {}".format(msg)
        minibuffer_show_info(msg)

    def on_url_hovered(self, url):
        minibuffer_show_info(url)

    def main_window(self):
        view = self.view()
        if view:
            return view.main_window

    def update_title(self, title=None):
        if self == current_buffer():
            self.main_window().update_title(
                title if title is not None else self.title()
            )

    def _incr_zoom(self, forward):
        # Zooming constants
        ZOOM_MIN = 25
        ZOOM_MAX = 500
        ZOOM_INC = 25

        zoom = self.zoomFactor()*100
        # We need to round up because the zoom factor is stored as a float
        self.set_zoom(round(min(ZOOM_MAX, max(ZOOM_MIN, zoom +
                                              (ZOOM_INC if forward
                                               else -ZOOM_INC)))))

    def set_zoom(self, zoom_factor):

        if zoom_factor is not None:
            self.setZoomFactor(zoom_factor/100)
            minibuffer_show_info("Zoom level: %d%%" % (zoom_factor))

    def zoom_in(self):
        self._incr_zoom(True)

    def zoom_out(self):
        self._incr_zoom(False)

    def zoom_normal(self):
        self.set_zoom(100)


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
KEYMAP.define_key("m", "bookmark-open")
KEYMAP.define_key("M", "bookmark-add")
KEYMAP.define_key("C-+", "text-zoom-in")
KEYMAP.define_key("C--", "text-zoom-out")
KEYMAP.define_key("C-=", "text-zoom-reset")
KEYMAP.define_key("+", "zoom-in")
KEYMAP.define_key("-", "zoom-out")
KEYMAP.define_key("0", "zoom-normal")
KEYMAP.define_key("C-n", "send-key-down")
KEYMAP.define_key("n", "send-key-down")
KEYMAP.define_key("C-p", "send-key-up")
KEYMAP.define_key("p", "send-key-up")
KEYMAP.define_key("C-f", "send-key-right")
KEYMAP.define_key("C-b", "send-key-left")
KEYMAP.define_key("C-g", "buffer-unselect")
