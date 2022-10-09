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

import time

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QWidget
from PyQt6.QtCore import QEvent

from .keyboardhandler import local_keymap, set_local_keymap, \
    LOCAL_KEYMAP_SETTER
from . import windows, variables


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
    callbacks=(_update_stylesheets,),
    type=variables.String(),
)


class WebView(QFrame):
    def __init__(self, window):
        QFrame.__init__(self)
        self.main_window = window
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.setStyleSheet(webview_stylesheet.value)

    def _attach_view(self, view):
        if self.layout().count() == 0:
            self.layout().addWidget(view)

    def _detach_view(self):
        if self.layout().count() > 0:
            it = self.layout().takeAt(0)
            it.widget().setParent(None)

    def setBuffer(self, buffer, update_last_use=True):
        otherviews = [w for w in self.main_window.webviews()
                      if w != self]
        for v in otherviews:
            # this prevent multi views from being scrolled to the
            # right; to reproduce, C-x 3, C-x o, then C-x f and open
            # something
            iv = v.internal_view()
            if iv:
                iv.setFocus()

        self._detach_view()

        if buffer is None:
            self.main_window.update_title()
            return

        if buffer._internal_view is None:
            buffer._internal_view = InternalWebView(self)
            buffer._internal_view.setPage(buffer)

        self._attach_view(buffer._internal_view)

        url = buffer.delayed_loading_url()
        if url:
            buffer.load(url.url)
        self.main_window.update_title()
        LOCAL_KEYMAP_SETTER.buffer_opened_in_view(buffer)
        # mark the buffer to be the most recently opened
        if update_last_use:
            buffer.last_use = time.time()

        if self.main_window.current_webview() == self:
            # keyboard focus is lost without that.
            buffer._internal_view.setFocus()
            self.show_focused(True)

    def buffer(self):
        if self.internal_view():
            return self.internal_view().page()

    def show_focused(self, active):
        self.setProperty("current", active)
        self.setProperty("single",
                         len(self.main_window.webviews()) == 1)
        # force the style to be taken into account
        self.setStyle(self.style())

    def internal_view(self):
        if self.layout().count() > 0:
            return self.layout().itemAt(0).widget()


class InternalWebView(QWebEngineView):
    """Do not instantiate that class directly"""
    def __init__(self, view):
        QWebEngineView.__init__(self)
        self._view = view
        self._fullscreen_state = None

    def view(self):
        return self._view

    def event(self, evt):
        if evt.type() == QEvent.Type.ChildAdded:
            obj = evt.child()
            if isinstance(obj, QWidget):
                obj.installEventFilter(self)
        return QWebEngineView.event(self, evt)

    def eventFilter(self, obj, evt):
        view = self.view()

        t = evt.type()
        if t == QEvent.Type.MouseButtonPress:
            if view != view.main_window.current_webview():
                view.main_window.set_current_webview(view)
        elif t == QEvent.Type.FocusIn:
            if self.isEnabled():  # disabled when there is a full-screen window
                LOCAL_KEYMAP_SETTER.view_focus_changed(view, True)
        elif t == QEvent.Type.FocusOut:
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
        self.view._detach_view()
        # show fullscreen on the right place.
        screen = self.view.screen()
        self.internal_view.showFullScreen()
        self.internal_view.setGeometry(screen.geometry())
        self.view.main_window.fullscreen_window = self

    def restore(self):
        set_local_keymap(self.keymap)
        self.internal_view.showNormal()
        self.view._attach_view(self.internal_view)
        self.view.main_window.fullscreen_window = None
