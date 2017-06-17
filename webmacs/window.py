from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtCore import QEvent, QObject

from .webview import WebView
from .keymap import KeyPress, current_global_map


class KeyboardHandler(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.keypresses = []

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.KeyPress):
            key = KeyPress.from_qevent(event)
            if key is None:
                return True
            if self.handle_keypress(key):
                return True

        return QObject.eventFilter(self, obj, event)

    def handle_keypress(self, keypress):
        self.keypresses.append(keypress)
        result = current_global_map().lookup(self.keypresses)

        if result is None:
            self.keypresses = []
            return False
        if not result.complete:
            return True
        else:
            self.keypresses = []
            result.command()
            return True


class Window(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self._layout = QGridLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)
        self.keyboardHandler = KeyboardHandler()

        self._webviews = []

        # create the main view
        view = self._create_webview()
        self._currentWebView = view
        self._layout.addWidget(view)

    def _create_webview(self):
        view = WebView(self)
        self._webviews.append(view)
        return view

    def currentWebView(self):
        return self._currentWebView

    def _currentPosition(self):
        for row in range(self._layout.rowCount()):
            for col in range(self._layout.columnCount()):
                item = self._layout.itemAtPosition(row, col)
                if item.widget() == self._currentWebView:
                    return (row, col)

    def createViewOnRight(self):
        row, col = self._currentPosition()
        view = self._create_webview()
        self._layout.addWidget(view, row, col + 1)
        return view

    def paintEvent(self, _):
        # to allow custom styling from stylesheet
        from PyQt5.QtWidgets import QStyleOption, QStyle
        from PyQt5.QtGui import QPainter
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)
