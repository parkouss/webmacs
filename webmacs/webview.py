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
            view.setStyleSheet(var.value)


webview_stylesheet = variables.define_variable(
    "webview-stylesheet",
    "stylesheet associated to the webviews.",
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
        self.setStyleSheet(webview_stylesheet.value)

    def setBuffer(self, buffer):
        otherviews = [w for w in self.main_window.webviews()
                      if w != self]
        for v in otherviews:
            # this prevent multi views from being scrolled to the
            # right; to reproduce, C-x 3, C-x o, then C-x f and open
            # something
            iv = v.internal_view()
            if iv:
                pass
                iv.setFocus()

        if self._internal_view:
            self._internal_view.detach()

        if buffer is None:
            self._internal_view = None
            return

        internal_view = buffer.internal_view()
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

        if self.main_window.current_webview() == self:
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
        self._internal_view.setFocus()
        self.buffer().update_title()


class InternalWebView(QWebEngineView):
    """Do not instantiate that class directly"""
    def __init__(self):
        QWebEngineView.__init__(self)
        self._viewport = None
        self._view = None
        self._fullscreen_state = None

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
                obj.installEventFilter(self)
        return QWebEngineView.event(self, evt)

    def eventFilter(self, obj, evt):
        t = evt.type()
        if t == QEvent.KeyPress:
            return KEY_EATER.event_filter(obj, evt)

        view = self._view
        if not view:
            return False

        if t == QEvent.ShortcutOverride:
            # disable automatic shortcuts in browser, like C-a
            return True
        elif t == QEvent.MouseButtonPress:
            if view != view.main_window.current_webview():
                view.set_current()
        elif t == QEvent.FocusIn:
            if self.isEnabled():  # disabled when there is a full-screen window
                LOCAL_KEYMAP_SETTER.view_focus_changed(view, True)
        elif t == QEvent.FocusOut:
            if self.isEnabled():  # disabled when there is a full-screen window
                LOCAL_KEYMAP_SETTER.view_focus_changed(view, False)
        return False

    def request_fullscreen(self, toggle_on):
        if toggle_on:
            if self._fullscreen_state:
                return
            self._fullscreen_state = FullScreenState(self)
            return True
        else:
            if not self._fullscreen_state:
                return
            self._fullscreen_state.restore()
            self._fullscreen_state = None
            return True


class FullScreenState(object):
    def __init__(self, internal_view):
        self.view = internal_view.view()
        self.internal_view = internal_view
        self.keymap = local_keymap()

        set_local_keymap(self.view.buffer().mode.fullscreen_keymap())
        self.internal_view.detach()
        # show fullscreen on the right place.
        screen = app().screens()[app().desktop().screenNumber(self.view)]
        self.internal_view.showFullScreen()
        self.internal_view.setGeometry(screen.geometry())
        self.view.main_window.fullscreen_window = self

    def restore(self):
        set_local_keymap(self.keymap)
        self.internal_view.showNormal()
        self.internal_view.attach(self.view)
        self.view.main_window.fullscreen_window = None
