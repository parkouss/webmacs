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

from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QWidget
from PyQt5.QtCore import QEvent

from .keyboardhandler import local_keymap, set_local_keymap, KEY_EATER, \
    LOCAL_KEYMAP_SETTER
from . import BUFFERS, windows, variables
from .application import app


def _update_stylesheets(var):
    for w in windows():
        for view in w.webviews():
            c = view.container()
            if c:
                c.setStyleSheet(var.value)


webview_container_stylesheet = variables.define_variable(
    "webview-container-stylesheet",
    "stylesheet associated to the webview containers.",
    """\
[single=false][current=true] {
    border-top: 1px solid black;
    padding: 1px;
    background-color: red;
}
[single=false][current=false] {
    border-top: 1px solid white;
    padding: 1px;
}\
""",
    callbacks=(_update_stylesheets,)
)


class WebView(QFrame):
    def __init__(self, window):
        QFrame.__init__(self)
        self.main_window = window
        self._internal_view = None
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.setStyleSheet(webview_container_stylesheet.value)

    def setBuffer(self, buffer):
        if self._internal_view:
            self._internal_view.detach()

        internal_view = buffer.view()
        if not internal_view:
            internal_view = InternalWebView()
            internal_view.setPage(buffer)

        internal_view.attach(self)
        self._internal_view = internal_view

        buffer.update_title()
        url = buffer.delayed_loading_url()
        if url:
            buffer.load(url.url)
        LOCAL_KEYMAP_SETTER.buffer_opened_in_view(buffer)
        # move the buffer so it becomes the most recently opened
        if buffer != BUFFERS[0]:
            BUFFERS.remove(buffer)
            BUFFERS.insert(0, buffer)

        if self.main_window.current_web_view() == self:
            # keyboard focus is lost without that.
            internal_view.setFocus()
            self.show_focused(True)

    def buffer(self):
        if self._internal_view:
            return self._internal_view.page()

    def show_focused(self, active):
        self.setProperty("current", active)
        self.setProperty("single",
                         len(self.main_window.webviews()) == 1)
        # force the style to be taken into account
        self.setStyle(self.style())

    def internal_view(self):
        return self._internal_view

    def set_current(self):
        self.main_window._change_current_webview(self)
        # self._internal_view.setFocus()
        self.buffer().update_title()


class InternalWebView(QWebEngineView):
    """Do not instantiate that class directly"""
    def __init__(self):
        QWebEngineView.__init__(self)
        self._viewport = None
        self._view = None

    def view(self):
        return self._view

    def attach(self, view):
        self._view = view
        view.layout().addWidget(self)

    def detach(self):
        if self._view:
            self._view.layout().removeWidget(self)
            self.setParent(None)
            self._view = None

    def event(self, evt):
        if evt.type() == QEvent.ChildAdded:
            obj = evt.child()
            if isinstance(obj, QWidget):
                if self._viewport:
                    try:
                        self._viewport.removeEventFilter(self)
                    except RuntimeError:
                        pass
                obj.installEventFilter(self)
                self._viewport = obj
        return QWebEngineView.event(self, evt)

    def eventFilter(self, obj, evt):
        t = evt.type()
        if t == QEvent.KeyPress:
            return KEY_EATER.event_filter(obj, evt)
        elif t == QEvent.ShortcutOverride:
            # disable automatic shortcuts in browser, like C-a
            return True
        elif t == QEvent.MouseButtonPress:
            if self != self._view.main_window.current_web_view():
                self._view.set_current()
        elif t == QEvent.FocusIn:
            if self.isEnabled():  # disabled when there is a full-screen window
                LOCAL_KEYMAP_SETTER.view_focus_changed(self._view, True)
        elif t == QEvent.FocusOut:
            if self.isEnabled():  # disabled when there is a full-screen window
                LOCAL_KEYMAP_SETTER.view_focus_changed(self._view, False)
        return False

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


class FullScreenWindow(WebView):
    def __init__(self, window):
        WebView.__init__(self, window, with_container=False)
        self._other_view = None
        self._other_keymap = None

    def eventFilter(self, obj, evt):
        t = evt.type()
        if t == QEvent.KeyPress:
            return KEY_EATER.event_filter(obj, evt)
        elif t == QEvent.ShortcutOverride:
            # disable automatic shortcuts in browser, like C-a
            return True
        return False

    def enable(self, webview):
        self._other_view = webview
        webview.setEnabled(False)
        buff = webview.buffer()
        self.setBuffer(buff)
        self._other_keymap = local_keymap()
        set_local_keymap(buff.mode.fullscreen_keymap())
        # show fullscreen on the right place.
        screen = app().screens()[app().desktop().screenNumber(webview)]
        self.showFullScreen()
        self.setGeometry(screen.geometry())

    def disable(self):
        self._other_view.setEnabled(True)
        self._other_view.setBuffer(self.buffer())
        self.close()
        self.deleteLater()
        set_local_keymap(self._other_keymap)
        self._other_keymap = None
