from PyQt5.QtWebEngineWidgets import QWebEngineView


class FullScreenWindow(QWebEngineView):
    def __init__(self, window):
        QWebEngineView.__init__(self)
        self._other_view = None
        # setup a window attr to have a webview like interface
        self.window = window  # todo fix this accessor

    def enable(self, webview):
        self._other_view = webview
        self.setPage(webview.page())
        self.showFullScreen()

    def disable(self):
        self._other_view.setPage(self.page())
        self.close()
        self.deleteLater()

    # only to have a webview like interface
    def set_current(self):
        pass
