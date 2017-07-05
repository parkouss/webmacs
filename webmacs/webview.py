from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QWidget, QVBoxLayout


class WebViewContainer(QWidget):
    def __init__(self, view):
        QWidget.__init__(self)
        self._view = view
        layout = QVBoxLayout()
        layout.addWidget(view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

    def show_focused(self, active):
        if active:
            self.layout().setContentsMargins(0, 3, 0, 0)
        else:
            self.layout().setContentsMargins(0, 0, 0, 0)

    def view(self):
        return self._view


class WebView(QWebEngineView):
    """Do not instantiate that class directly"""
    def __init__(self, window):
        QWebEngineView.__init__(self)
        self.window = window
        self._container = WebViewContainer(self)

    def container(self):
        return self._container

    def setBuffer(self, buffer):
        self.setPage(buffer)

    def buffer(self):
        return self.page()

    def keymap(self):
        return self.buffer().keymap()

    def set_current(self):
        self.window._change_current_webview(self)
        self.setFocus()
