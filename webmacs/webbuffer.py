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
import time
import json

from PyQt6.QtCore import QUrl, pyqtSlot as Slot
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineScript
from PyQt6.QtWebChannel import QWebChannel
from collections import namedtuple

from . import hooks, variables, windows
from . import BUFFERS, current_minibuffer, minibuffer_show_info, \
    current_buffer, call_later, current_window, recent_buffers
from .content_handler import WebContentHandler
from .application import app
from .minibuffer.prompt import YesNoPrompt, AskPasswordPrompt
from .password_manager import PasswordManagerNotReady
from .keyboardhandler import LOCAL_KEYMAP_SETTER
from .mode import get_mode, Mode, get_auto_modename_for_url


close_buffer_close_window = variables.define_variable(
    "close-buffer-close-window",
    "Policy to close a window when the last available buffer is closed."
    " If never, closing a buffer will never close a window."
    " If all, closing a buffer can close a window, even the last one ("
    " and so it will exit the application). Finally, all-but-last is like"
    " all but the last window will never be closed.",
    "never",
    type=variables.String(choices=("never", "all", "all-but-last")),
)


# a tuple of QUrl, str to delay loading of a page.
DelayedLoadingUrl = namedtuple("DelayedLoadingUrl", ("url", "title"))


def close_buffer(wb):
    view = wb.view()
    if view:
        # buffer is currently visible, search for a buffer that is not visible
        # yet to put it in the view
        invisibles = [b for b in recent_buffers() if not b.view()]
        if not invisibles:
            if len(view.main_window.webviews()) > 1:
                # we can close the current view if it is not alone
                view.main_window.close_view(view)
            else:
                close_window = close_buffer_close_window.value
                if close_window == "never":
                    # never close the buffer, nor the window
                    return
                elif len(windows()) == 1:
                    # if only one window left and policy is all, quit the app
                    if close_window == "all":
                        app().quit()
                    return
                else:
                    # close both the window and the buffer
                    view.setBuffer(None)
                    view.main_window.close()
        else:
            # associate the first buffer that does not have any view yet
            view.setBuffer(invisibles[0])

    internal_view = wb.internal_view()
    if internal_view:
        # remove the associated internal page view (might be causing a crash
        # from when calling ~QWebEnginePage())
        # wb.setView(None)
        internal_view.detach()
        internal_view.deleteLater()

    # clear the web channel. Might be causing a crash when calling
    # ~QWebEnginePage()
    wb.webChannel().deleteLater()
    wb.setWebChannel(None)

    BUFFERS.remove(wb)
    wb.deleteLater()
    hooks.webbuffer_closed(wb)
    return True


class WebBuffer(QWebEnginePage):
    """
    Represent some web page content.
    """

    LOGGER = logging.getLogger("webcontent")
    JSMessageLevel = QWebEnginePage.JavaScriptConsoleMessageLevel
    JSLEVEL2LOGGING = {
        JSMessageLevel.InfoMessageLevel: logging.INFO,
        JSMessageLevel.WarningMessageLevel: logging.WARNING,
        JSMessageLevel.ErrorMessageLevel: logging.ERROR,
    }

    def __init__(self, url=None):
        """
        Create a webbuffer.

        :param url: the url to use for the buffer. Must be an instance of QUrl,
            an str or None to not load any url.
        """
        QWebEnginePage.__init__(self, app().profile.q_profile, None)
        self.last_use = time.time()
        cb = current_buffer()
        if cb:
            BUFFERS.insert(BUFFERS.index(cb) + 1, self)
        else:
            BUFFERS.append(self)
        hooks.webbuffer_created(self)

        self.fullScreenRequested.connect(self._on_full_screen_requested)
        self.featurePermissionRequested.connect(self._on_feature_requested)
        self._content_handler = WebContentHandler(self)
        channel = QWebChannel(self)
        channel.registerObject("contentHandler", self._content_handler)

        self.setWebChannel(channel,
                           QWebEngineScript.ScriptWorldId.ApplicationWorld)

        self.loadFinished.connect(self.finished)
        self.authenticationRequired.connect(self.handle_authentication)
        self.linkHovered.connect(self.on_url_hovered)
        self.titleChanged.connect(self.update_title)
        self.__delay_loading_url = None
        self.__keymap_mode = Mode.KEYMAP_NORMAL
        self.__mode = get_mode("standard-mode")
        self.__text_edit_mark = False
        self._internal_view = None

        if url:
            if isinstance(url, DelayedLoadingUrl):
                self.__delay_loading_url = url
            else:
                self.load(url)

    def internal_view(self):
        return self._internal_view

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

    def start_select_browser_objects(self, selector, method="filter",
                                     method_options=None):
        self.runJavaScript(
            "hints.selectBrowserObjects(%r, %r, %r);"
            % (selector, method, json.dumps(method_options)),
            QWebEngineScript.ScriptWorldId.ApplicationWorld)

    def stop_select_browser_objects(self):
        self.runJavaScript(
            "hints.clearBrowserObjects();",
            QWebEngineScript.ScriptWorldId.ApplicationWorld)

    def select_nex_browser_object(self, forward=True):
        self.runJavaScript(
            "hints.activateNextHint(%s);" % ("false" if forward else "true",),
            QWebEngineScript.ScriptWorldId.ApplicationWorld)

    def filter_browser_objects(self, text):
        self.runJavaScript(
            "hints.filterSelection(%r);" % text,
            QWebEngineScript.ScriptWorldId.ApplicationWorld)

    def focus_active_browser_object(self):
        self.runJavaScript(
            "hints.followCurrentLink();",
            QWebEngineScript.ScriptWorldId.ApplicationWorld)

    def select_visible_hint(self, hint_id):
        self.runJavaScript(
            "hints.selectVisibleHint(%r);" % hint_id,
            QWebEngineScript.ScriptWorldId.ApplicationWorld)

    @Slot("QWebEngineFullScreenRequest")
    def _on_full_screen_requested(self, request):
        internal_view = self.internal_view()
        if not internal_view:
            return
        if internal_view.request_fullscreen(request.toggleOn()):
            request.accept()

    @Slot(QUrl, QWebEnginePage.Feature)
    def _on_feature_requested(self, url, feature):
        permission_db = app().features()

        permission = permission_db.get_permission(url.host(), feature)

        if permission == QWebEnginePage.PermissionPolicy.PermissionUnknown:
            prompt = YesNoPrompt("Allow enabling feature {} for {}?"
                                 .format(feature.name, url.toString()),
                                 always=True,
                                 never=True)
            answer = current_minibuffer().do_prompt(prompt, flash=True)

            if answer in (YesNoPrompt.YES, YesNoPrompt.ALWAYS):
                permission = QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
            elif answer in (YesNoPrompt.NO, YesNoPrompt.NEVER):
                permission = QWebEnginePage.PermissionPolicy.PermissionDeniedByUser
            else:
                permission = QWebEnginePage.PermissionPolicy.PermissionUnknown

            if answer in (YesNoPrompt.ALWAYS, YesNoPrompt.NEVER):
                permission_db.set_permission(url.host(), feature, permission)

        self.setFeaturePermission(url, feature, permission)

    def createWindow(self, type):
        buffer = create_buffer()
        view = self.view()
        if view is None:
            view = current_window().current_webview()

        def open_in_view():
            view.setBuffer(buffer)

        call_later(open_in_view)
        return buffer

    def finished(self):
        url = self.url()
        if url.isValid() and not url.scheme() == "webmacs":
            app().visitedlinks().visit(url.toString(), self.title())

        self.set_mode(get_auto_modename_for_url(self.url().toString()))

        hooks.webbuffer_load_finished(self)

        # We lose the keyboard focus without that with Qt 5.11. Though it
        # happens quite randomly, but a combination of follow, go back, google
        # something and the issue happens. I was not seeing this with Qt5.9.
        view = self.view()
        if view and not LOCAL_KEYMAP_SETTER.enabled_minibuffer \
           and view.main_window.current_webview() == view:

            view.internal_view().setFocus()

    def handle_authentication(self, url, authenticator):
        password_manager = app().profile.password_manager
        try:
            credential = password_manager.credential_for_url(url.toString())
        except PasswordManagerNotReady:
            credential = None

        if credential:
            authenticator.setUser(credential.username)
            authenticator.setPassword(credential.password)
            return

        # ask authentication credentials
        prompt = AskPasswordPrompt(self)
        current_minibuffer().do_prompt(prompt, flash=True)

        authenticator.setUser(prompt.username)
        authenticator.setPassword(prompt.password)

    def certificateError(self, error):
        url = "{}:{}".format(error.url().host(), error.url().port(80))
        db = app().ignored_certs()
        if db.is_ignored(url):
            return True

        prompt = YesNoPrompt("[certificate error] {} - ignore ? "
                             .format(error.errorDescription()), always=True)
        current_minibuffer().do_prompt(prompt, flash=True)

        if prompt.value() == YesNoPrompt.ALWAYS:
            db.ignore(url)
        return prompt.value() in (YesNoPrompt.ALWAYS, YesNoPrompt.YES)

    def javaScriptConfirm(self, url, msg):
        return current_minibuffer().do_prompt(
            YesNoPrompt("[js-confirm] {} ".format(msg)),
            flash=True,
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
            mw = self.main_window()
            if mw is not None:
                mw.update_title(
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
