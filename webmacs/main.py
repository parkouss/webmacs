import argparse
import signal
import socket
import logging

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


def setup_logging(level, webcontent_level):
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    webcontent_logger = logging.getLogger("webcontent")
    handler = logging.StreamHandler()
    fmt = logging.Formatter("%(levelname)s %(name)s: [%(url)s] %(message)s")
    handler.setFormatter(fmt)
    webcontent_logger.addHandler(handler)
    webcontent_logger.propagate = False
    webcontent_logger.setLevel(webcontent_level)


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log-level",
                        help="Set the log level, defaults to %(default)s.",
                        default="warning",
                        choices=("debug", "info", "warning",
                                 "error", "critical"))

    # There is no such javascript error level, critical - still since there
    # is some logs that are printed anyway and that it is easier to implement
    # let's keep the critical level.
    parser.add_argument("-w", "--webcontent-log-level",
                        help="Set the log level for the web contents,"
                        " defaults to %(default)s.",
                        default="critical",
                        choices=("info", "warning", "error", "critical"))

    return parser.parse_args(argv)


def main():
    opts = parse_args()
    setup_logging(getattr(logging, opts.log_level.upper()),
                  getattr(logging, opts.webcontent_log_level.upper()))
    app = Application(["webmacs"])

    window = Window()

    buffer = WebBuffer()
    buffer.load("http://www.google.fr")
    window.current_web_view().setBuffer(buffer)

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
