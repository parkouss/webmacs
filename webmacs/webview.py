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

from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QWidget
from PyQt5.QtCore import QEvent

from .keymaps import Keymap
from .keyboardhandler import local_keymap, set_local_keymap, KEY_EATER
from . import BUFFERS
from .application import app


class WebViewContainer(QFrame):
    def __init__(self, view):
        QFrame.__init__(self)
        self._view = view
        layout = QVBoxLayout()
        layout.addWidget(view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

    def show_focused(self, active):
        self.setProperty("current", active)
        # force the style to be taken into account
        self.setStyle(self.style())

    def view(self):
        return self._view


class WebView(QWebEngineView):
    """Do not instantiate that class directly"""
    def __init__(self, window, with_container=True):
        QWebEngineView.__init__(self)
        self.window = window  # todo fix this accessor
        if with_container:
            self._container = WebViewContainer(self)
        else:
            self._container = None

    def event(self, evt):
        if evt.type() == QEvent.ChildAdded:
            obj = evt.child()
            if isinstance(obj, QWidget):
                obj.installEventFilter(self)
        return QWebEngineView.event(self, evt)

    def eventFilter(self, obj, evt):
        t = evt.type()
        if t == QEvent.KeyPress:
            return KEY_EATER.event_filter(obj, evt)
        elif t == QEvent.MouseButtonPress:
            if self != self.window.current_web_view():
                self.set_current()
        return False

    def container(self):
        return self._container

    def setBuffer(self, buffer):
        self.setPage(buffer)
        buffer.update_title()
        url = buffer.delayed_loading_url()
        if url:
            buffer.load(url.url)
        set_local_keymap(buffer.active_keymap())
        # move the buffer so it becomes the most recently opened
        if buffer != BUFFERS[0]:
            BUFFERS.remove(buffer)
            BUFFERS.insert(0, buffer)

    def buffer(self):
        return self.page()

    def keymap(self):
        return self.buffer().keymap()

    def set_current(self):
        self.window._change_current_webview(self)
        self.setFocus()
        self.buffer().update_title()

    def request_fullscreen(self, toggle_on):
        w = self.window

        if toggle_on:
            if w.fullscreen_window:
                return
            w.fullscreen_window = FullScreenWindow(self.window)
            w.fullscreen_window.enable(self)
            return True
        else:
            if not w.fullscreen_window:
                return
            w.fullscreen_window.disable()
            w.fullscreen_window = None
            return True


FULLSCREEN_KEYMAP = Keymap("fullscreen")


@FULLSCREEN_KEYMAP.define_key("C-g")
@FULLSCREEN_KEYMAP.define_key("Esc")
def exit_full_screen():
    from .window import current_window
    fw = current_window().fullscreen_window
    if fw:
        fw.triggerPageAction(QWebEnginePage.ExitFullScreen)


class FullScreenWindow(WebView):
    def __init__(self, window):
        WebView.__init__(self, window, with_container=False)
        self._other_view = None
        self._other_keymap = None

    def enable(self, webview):
        self._other_view = webview
        self.setPage(webview.page())
        self._other_keymap = local_keymap()
        set_local_keymap(self.keymap())
        # show fullscreen on the right place.
        screen = app().screens()[app().desktop().screenNumber(webview)]
        self.showFullScreen()
        self.setGeometry(screen.geometry())

    def disable(self):
        self._other_view.setPage(self.page())
        self.close()
        self.deleteLater()
        set_local_keymap(self._other_keymap)
        self._other_keymap = None

    def keymap(self):
        return FULLSCREEN_KEYMAP

    def set_current(self):
        pass
