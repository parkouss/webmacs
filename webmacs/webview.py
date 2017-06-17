from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QEvent


class WebView(QWebEngineView):
    def __init__(self, mainwindow):
        QWebEngineView.__init__(self)
        self.mainwindow = mainwindow

    def setBuffer(self, buffer):
        self.setPage(buffer)

    def event(self, event):
        # it appears that the key event are dispatched on a child widget that
        # is not accessible through the public api...
        if (event.type() == QEvent.ChildAdded):
            event.child().installEventFilter(self.mainwindow.keyboardHandler)
        return QWebEngineView.event(self, event)
