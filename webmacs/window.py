from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtCore import QEvent, QObject, Qt

from .webview import WebView


class KeyboardHandler(QObject):
    def eventFilter(self, obj, event):
        if (event.type() == QEvent.KeyPress):
            # see https://stackoverflow.com/a/6665017
            key = event.key()
            modifiers = event.modifiers()
            if modifiers & Qt.ShiftModifier:
                key += Qt.SHIFT
            if modifiers & Qt.ControlModifier:
                key += Qt.CTRL
            if modifiers & Qt.AltModifier:
                key += Qt.ALT
            if modifiers & Qt.MetaModifier:
                key += Qt.META

        return QObject.eventFilter(self, obj, event)


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
