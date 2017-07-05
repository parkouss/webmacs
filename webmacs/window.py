from PyQt5.QtWidgets import QWidget, QGridLayout, QVBoxLayout
from PyQt5.QtCore import QEvent, QObject

from .webview import WebView
from .minibuffer import Minibuffer
from . import hooks


class WindowsHandler(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.windows = []
        self.current_window = None

    def register_window(self, window):
        window.installEventFilter(self)
        self.windows.append(window)

    def eventFilter(self, window, event):
        t = event.type()
        if t == QEvent.WindowActivate:
            self.current_window = window
        elif t == QEvent.Close:
            self.windows.remove(window)
            if window == self.current_window:
                self.current_window = None

        return QObject.eventFilter(self, window, event)


HANDLER = WindowsHandler()


def remove_layout_spaces(layout):
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)


def windows():
    """
    Returns the window list.

    Do not modify this list.
    """
    return HANDLER.windows


def current_window():
    """
    Returns the currently activated window.
    """
    return HANDLER.current_window


class Window(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self._layout = QVBoxLayout()
        remove_layout_spaces(self._layout)
        self.setLayout(self._layout)

        self._central_widget = QWidget()
        self._layout.addWidget(self._central_widget)
        self._webviews_layout = QGridLayout()
        remove_layout_spaces(self._webviews_layout)
        self._central_widget.setLayout(self._webviews_layout)

        self._minibuffer = Minibuffer(self)
        self._layout.addWidget(self._minibuffer)

        self._webviews = []

        # create the main view
        view = self._create_webview()
        self._current_web_view = view
        self._webviews_layout.addWidget(view.container())

        HANDLER.register_window(self)

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

    def _currentPosition(self):
        for row in range(self._webviews_layout.rowCount()):
            for col in range(self._webviews_layout.columnCount()):
                item = self._webviews_layout.itemAtPosition(row, col)
                if item and item.widget().view() == self._current_web_view:
                    return (row, col)

    def create_webview_on_right(self):
        row, col = self._currentPosition()
        view = self._create_webview()
        self._webviews_layout.addWidget(view.container(), row, col + 1, -1, 1)
        return view

    def create_webview_on_bottom(self):
        row, col = self._currentPosition()
        view = self._create_webview()
        self._webviews_layout.addWidget(view.container(), row + 1, col, 1, -1)
        return view

    def delete_webview(self, webview):
        container = webview.container()
        if len(self._webviews) <= 1:
            return False
        index = self._webviews_layout.indexOf(container)
        if index == -1:
            return
        self._webviews.remove(webview)
        hooks.webview_closed.call(webview)
        self._webviews_layout.removeWidget(container)
        webview.deleteLater()
        return True

    def minibuffer(self):
        return self._minibuffer

    def paintEvent(self, _):
        # to allow custom styling from stylesheet
        from PyQt5.QtWidgets import QStyleOption, QStyle
        from PyQt5.QtGui import QPainter
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)
