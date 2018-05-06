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

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QRect

from .minibuffer import Minibuffer
from .egrid import ViewGridLayout
from . import WINDOWS_HANDLER


def remove_layout_spaces(layout):
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)


class Window(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self._layout = QVBoxLayout()
        remove_layout_spaces(self._layout)
        self.setLayout(self._layout)

        self._central_widget = QWidget()
        self._layout.addWidget(self._central_widget)
        self._webviews_layout = ViewGridLayout(self)
        remove_layout_spaces(self._webviews_layout)
        self._central_widget.setLayout(self._webviews_layout)

        self._minibuffer = Minibuffer(self)
        self._layout.addWidget(self._minibuffer)

        self.fullscreen_window = None
        self.quit_if_last_closed = True

        WINDOWS_HANDLER.register_window(self)

    def _change_current_webview(self, webview):
        self.current_webview().show_focused(False)
        if len(self.webviews()) > 1:
            webview.show_focused(True)
        self._webviews_layout.set_current_view(webview)

    def current_webview(self):
        return self._webviews_layout.current_view()

    def webviews(self):
        return self._webviews_layout.views()

    def create_webview_on_right(self):
        return self._webviews_layout.split_view(ViewGridLayout.VERTICAL)

    def create_webview_on_bottom(self):
        return self._webviews_layout.split_view(ViewGridLayout.HORIZONTAL)

    def _delete_webview(self, webview):
        self._webviews_layout.removeWidget(webview)
        webview.deleteLater()

    def minibuffer(self):
        return self._minibuffer

    def other_view(self):
        """switch to the next view"""
        views = self.webviews()
        index = views.index(self.current_webview())
        index = index + 1
        if index >= len(views):
            index = 0
        views[index].set_current()

    def close_view(self, view):
        """close the given view"""
        views = self.webviews()
        if len(views) == 1:
            return  # can't delete a single view

        if view == self.current_webview():
            self.other_view()

        self._delete_webview(view)

        # do not show the window focused if there is one left
        if len(self.webviews()) == 1:
            self.current_webview().show_focused(True)

    def close_other_views(self):
        """close all views but the current one"""
        view = self.current_webview()
        # to remove more than one item correctly, the iteration must
        # be done on a shallow copy of the list
        for other in list(self.webviews()):
            if view != other:
                self._delete_webview(other)

        # do not show the window focused if there is one left
        if len(self.webviews()) == 1:
            self.current_webview().show_focused(False)

    def update_title(self, title):
        if title:
            self.setWindowTitle("{} - Webmacs".format(title))
        else:
            self.setWindowTitle("Webmacs")

    def dump_state(self):
        return {
            "geometry": self.geometry().getRect(),
            "window-state": int(self.windowState()),
            "view-layout": self._webviews_layout.dump_state(),
        }

    def restore_state(self, data, version):
        self.setGeometry(QRect(*data["geometry"]))
        self.setWindowState(Qt.WindowStates(data["window-state"]))
        self._webviews_layout.restore_state(data["view-layout"])
