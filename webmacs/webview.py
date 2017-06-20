from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QEvent


class WebView(QWebEngineView):
    def __init__(self, window):
        QWebEngineView.__init__(self)
        self.window = window

    def setBuffer(self, buffer):
        self.setPage(buffer)

    def buffer(self):
        return self.page()

    def event(self, event):
        # it appears that the key event are dispatched on a child widget that
        # is not accessible through the public api...
        if (event.type() == QEvent.ChildAdded):
            event.child().installEventFilter(self.window.keyboard_handler)
        return QWebEngineView.event(self, event)
