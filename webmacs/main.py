import signal
import socket

from PyQt5.QtNetwork import QAbstractSocket

from .webbuffer import WebBuffer
from .application import Application
from .window import Window


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


def main():
    app = Application([])

    window = Window()

    buffer = WebBuffer(window)
    buffer.load("http://www.google.fr")
    window.currentWebView().setBuffer(buffer)

    # view = window.createViewOnRight()
    # buffer2 = WebBuffer(window)
    # buffer2.load("http://www.google.fr")
    # view.setBuffer(buffer2)
    # view.setFocus()

    window.show()

    signal_wakeup(app)
    signal.signal(signal.SIGINT, lambda s, h: app.quit())
    app.exec_()


if __name__ == '__main__':
    main()
