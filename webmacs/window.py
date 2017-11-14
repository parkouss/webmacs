from PyQt5.QtWidgets import QWidget, QVBoxLayout

from .webview import WebView
from .minibuffer import Minibuffer
from .egrid import EGridLayout
from . import hooks, WINDOWS_HANDLER


def remove_layout_spaces(layout):
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)


class Window(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self._layout = QVBoxLayout()
        remove_layout_spaces(self._layout)
        self.setLayout(self._layout)

        self._webviews = []
        view = self._create_webview()
        self._central_widget = QWidget()
        self._layout.addWidget(self._central_widget)
        self._webviews_layout = EGridLayout(view.container())
        remove_layout_spaces(self._webviews_layout)
        self._central_widget.setLayout(self._webviews_layout)

        self._minibuffer = Minibuffer(self)
        self._layout.addWidget(self._minibuffer)

        self._current_web_view = view
        self.fullscreen_window = None

        WINDOWS_HANDLER.register_window(self)

    def _change_current_webview(self, webview):
        self._current_web_view.container().show_focused(False)
        if len(self._webviews) > 1:
            webview.container().show_focused(True)
        self._current_web_view = webview

    def _create_webview(self):
        view = WebView(self)
        self._webviews.append(view)
        hooks.webview_created.call(view)
        return view

    def current_web_view(self):
        return self._current_web_view

    def webviews(self):
        return self._webviews

    def create_webview_on_right(self):
        view = self._create_webview()
        self._webviews_layout.insert_widget_right(
            self._current_web_view.container(),
            view.container()
            )
        return view

    def create_webview_on_bottom(self):
        view = self._create_webview()
        self._webviews_layout.insert_widget_bottom(
            self._current_web_view.container(),
            view.container()
            )
        return view

    def _delete_webview(self, webview):
        container = webview.container()
        if len(self._webviews) <= 1:
            return False
        self._webviews_layout.removeWidget(container)
        self._webviews.remove(webview)
        hooks.webview_closed.call(webview)
        webview.deleteLater()
        return True

    def minibuffer(self):
        return self._minibuffer

    def other_view(self):
        """switch to the next view"""
        views = self.webviews()
        index = views.index(self.current_web_view())
        index = index + 1
        if index >= len(views):
            index = 0
        views[index].set_current()

    def close_view(self, view):
        """close the given view"""
        views = self.webviews()
        if len(views) == 1:
            return  # can't delete a single view

        if view == self.current_web_view():
            self.other_view()

        self._delete_webview(view)

    def close_other_views(self):
        """close all views but the current one"""
        view = self.current_web_view()
        for other in self.webviews():
            if view != other:
                self._delete_webview(other)
