from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWidgets import QFrame, QVBoxLayout

from .keymaps import Keymap
from .keyboardhandler import local_keymap, set_local_keymap


class WebViewContainer(QFrame):
    def __init__(self, view):
        QFrame.__init__(self)
        self._view = view
        layout = QVBoxLayout()
        layout.addWidget(view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

    def show_focused(self, active):
        self.setProperty("current", active)
        # force the style to be taken into account
        self.setStyle(self.style())

    def view(self):
        return self._view


class WebView(QWebEngineView):
    """Do not instantiate that class directly"""
    def __init__(self, window, with_container=True):
        QWebEngineView.__init__(self)
        self.window = window  # todo fix this accessor
        if with_container:
            self._container = WebViewContainer(self)
        else:
            self._container = None

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

    def request_fullscreen(self, toggle_on):
        w = self.window

        if toggle_on:
            if w.fullscreen_window:
                return
            w.fullscreen_window = FullScreenWindow(self.window)
            w.fullscreen_window.enable(self)
            return True
        else:
            if not w.fullscreen_window:
                return
            w.fullscreen_window.disable()
            w.fullscreen_window = None
            return True


FULLSCREEN_KEYMAP = Keymap("fullscreen")


@FULLSCREEN_KEYMAP.define_key("C-g")
@FULLSCREEN_KEYMAP.define_key("Esc")
def exit_full_screen():
    from .window import current_window
    fw = current_window().fullscreen_window
    if fw:
        fw.triggerPageAction(QWebEnginePage.ExitFullScreen)


class FullScreenWindow(WebView):
    def __init__(self, window):
        WebView.__init__(self, window, with_container=False)
        self._other_view = None
        self._other_keymap = None

    def enable(self, webview):
        self._other_view = webview
        self.setPage(webview.page())
        self._other_keymap = local_keymap()
        set_local_keymap(self.keymap())
        self.showFullScreen()

    def disable(self):
        self._other_view.setPage(self.page())
        self.close()
        self.deleteLater()
        set_local_keymap(self._other_keymap)
        self._other_keymap = None

    def keymap(self):
        return FULLSCREEN_KEYMAP

    def set_current(self):
        pass
