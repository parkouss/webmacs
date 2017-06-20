from PyQt5.QtWidgets import QWidget, QGridLayout, QVBoxLayout
from PyQt5.QtCore import QEvent, QObject

from .webview import WebView
from .minibuffer import Minibuffer
from .keyboardhandler import KeyboardEventFilterHandler


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

        from .webbuffer import KEYMAP
        self.keyboard_handler = KeyboardEventFilterHandler([KEYMAP])

        self._webviews = []

        # create the main view
        view = self._create_webview()
        self._current_web_view = view
        self._webviews_layout.addWidget(view)

        HANDLER.register_window(self)

    def _create_webview(self):
        view = WebView(self)
        self._webviews.append(view)
        return view

    def current_web_view(self):
        return self._current_web_view

    def _currentPosition(self):
        for row in range(self._webviews_layout.rowCount()):
            for col in range(self._webviews_layout.columnCount()):
                item = self._webviews_layout.itemAtPosition(row, col)
                if item.widget() == self._current_web_view:
                    return (row, col)

    def createViewOnRight(self):
        row, col = self._currentPosition()
        view = self._create_webview()
        self._webviews_layout.addWidget(view, row, col + 1)
        return view

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
