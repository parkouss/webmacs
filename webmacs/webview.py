from PyQt5.QtWebEngineWidgets import QWebEngineView


class WebView(QWebEngineView):
    """Do not instantiate that class directly"""
    def __init__(self, window):
        QWebEngineView.__init__(self)
        self.window = window

    def setBuffer(self, buffer):
        self.setPage(buffer)

    def buffer(self):
        return self.page()

    def keymap(self):
        return self.buffer().keymap()

    def set_current(self):
        self.window._current_web_view = self
        self.setFocus()
