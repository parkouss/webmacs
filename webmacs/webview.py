from PyQt5.QtWebEngineWidgets import QWebEngineView
from .keyboardhandler import LOCAL_KEYMAP_SETTER


class WebView(QWebEngineView):
    def __init__(self, window):
        QWebEngineView.__init__(self)
        self.window = window
        LOCAL_KEYMAP_SETTER.register_view(self)

    def setBuffer(self, buffer):
        self.setPage(buffer)

    def buffer(self):
        return self.page()

    def keymap(self):
        return self.buffer().keymap()
