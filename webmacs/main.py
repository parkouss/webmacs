import os
import signal
import socket

from PyQt5.QtWebEngineWidgets import QWebEngineProfile, QWebEngineScript
from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QAbstractSocket

from .websocket import WebSocketClientWrapper
from .window import Window
from .webbuffer import WebBuffer


THIS_DIR = os.path.dirname(os.path.realpath(__file__))


def signal_wakeup(app):
    """
    Allow to be notified in python for signals when in long-running calls from
    the C or c++ side, like QApplication.exec_().

    See https://stackoverflow.com/a/37229299.
    """
    sock = QAbstractSocket(QAbstractSocket.UdpSocket, app)
    # Create a socket pair
    sock.wsock, sock.rsock = socket.socketpair(type=socket.SOCK_DGRAM)
    # Let Qt listen on the one end
    sock.setSocketDescriptor(sock.rsock.fileno())
    # And let Python write on the other end
    sock.wsock.setblocking(False)
    signal.set_wakeup_fd(sock.wsock.fileno())
    # add a dummy callback just to be on the python side as soon as possible.
    sock.readyRead.connect(lambda: None)


class Application(QApplication):
    def __init__(self, args):
        QApplication.__init__(self, args)

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
            default_profile.scripts().insert(script)

        for script in ("qwebchannel.js", "setup.js"):
            with open(os.path.join(THIS_DIR, script)) as f:
                src = f.read()
            if script == "setup.js":
                src = ("var webmacsBaseUrl = 'ws://localhost:%d';\n%s"
                       % (port, src))
            inject_js(src)


def main():
    app = Application([])

    window = Window()

    buffer = WebBuffer(window)
    buffer.load("http://www.google.fr")
    window.currentWebView().setBuffer(buffer)

    view = window.createViewOnRight()
    buffer2 = WebBuffer(window)
    buffer2.load("http://www.google.fr")
    view.setBuffer(buffer2)
    view.setFocus()

    window.show()

    signal_wakeup(app)
    signal.signal(signal.SIGINT, lambda s, h: app.quit())
    app.exec_()


if __name__ == '__main__':
    main()
