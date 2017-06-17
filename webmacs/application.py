import os

from PyQt5.QtWebEngineWidgets import QWebEngineProfile, QWebEngineScript
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, QEvent

from .websocket import WebSocketClientWrapper
from .window import Window


THIS_DIR = os.path.dirname(os.path.realpath(__file__))


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


class Application(QApplication):
    INSTANCE = None

    def __init__(self, args):
        QApplication.__init__(self, args)
        self.__class__.INSTANCE = self

        self._windows_handler = WindowsHandler(self)

        with open(os.path.join(THIS_DIR, "app_style.css")) as f:
            self.setStyleSheet(f.read())
        self._setup_websocket()
        self._setup_default_profile(self.sock_client.port)

    def _setup_websocket(self):
        """
        An internal websocket is used to communicate between web page content
        (using javascript) and the python code.
        """
        self.sock_client = WebSocketClientWrapper()

    def _setup_default_profile(self, port):
        default_profile = QWebEngineProfile.defaultProfile()

        def inject_js(src):
            script = QWebEngineScript()
            script.setInjectionPoint(QWebEngineScript.DocumentCreation)
            script.setSourceCode(src)
            script.setWorldId(QWebEngineScript.ApplicationWorld)
            default_profile.scripts().insert(script)

        for script in ("qwebchannel.js", "setup.js"):
            with open(os.path.join(THIS_DIR, script)) as f:
                src = f.read()
            if script == "setup.js":
                src = ("var webmacsBaseUrl = 'ws://localhost:%d';\n%s"
                       % (port, src))
            inject_js(src)

    def createWindow(self):
        """
        Create and returns a browser window.

        Note the created window is not shown, and only contains a webview with
        no buffer.

        This must be used so the window get registered correctly.
        """
        window = Window()
        self._windows_handler.register_window(window)
        return window

    def windows(self):
        """
        Returns the window list.

        Do not modify this list.
        """
        return self._windows_handler.windows

    def current_window(self):
        """
        Returns the currently activated window.
        """
        return self._windows_handler.current_window
