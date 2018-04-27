# This file is part of webmacs.
#
# webmacs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# webmacs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with webmacs.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import signal
import socket
import logging
import imp
import sys
import atexit

from PyQt5.QtNetwork import QAbstractSocket

from .application import Application, app as _app
from .ipc import IpcServer
from .session import session_load, session_save


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

    parser.add_argument("-i", "--instance",
                        help="Create or reuse a named webmacs instance.")

    parser.add_argument("url", nargs="?",
                        help="url to open")

    return parser.parse_args(argv)


def init(opts):
    """
    Default initialization of webmacs.

    If an url is given on the command line, it opens it. Else it try
    to load the buffers that were opened the last time webmacs has
    exited. If none of that works, the default is to open a buffer
    with an url to the duckduck go search engine.

    Also open the view maximized.

    :param opts: the result of the parsed command line.
    """
    app = _app()
    app.aboutToQuit.connect(lambda: session_save(app.profile))
    session_load(app.profile, opts)


def _handle_user_init_error(msg):
    import traceback
    conf_path = _app().conf_path()
    stack_size = 0
    tbs = traceback.extract_tb(sys.exc_info()[2])
    for i, t in enumerate(tbs):
        if t[0].startswith(conf_path):
            stack_size = -len(tbs[i:])
            break
    logging.critical(("%s\n\n" % msg)
                     + traceback.format_exc(stack_size))
    sys.exit(1)


def main():
    opts = parse_args()
    setup_logging(getattr(logging, opts.log_level.upper()),
                  getattr(logging, opts.webcontent_log_level.upper()))

    conn = IpcServer.check_server_connection(opts.instance)

    if conn:
        conn.send_data(opts.__dict__)
        data = conn.get_data()
        conn.sock.close()
        msg = data.get("message")
        if msg:
            print(msg)
        return

    app = Application(["webmacs"])
    server = IpcServer(opts.instance)
    atexit.register(server.cleanup)

    # load a user init module if any
    try:
        spec = imp.find_module("init", [app.conf_path()])
    except ImportError:
        user_init = None
    else:
        try:
            user_init = imp.load_module("_webmacs_userconfig", *spec)
        except Exception:
            _handle_user_init_error("Error reading the user configuration.")

    # and exectute its init function if there is one
    if user_init is None or not hasattr(user_init, "init"):
        init(opts)
    else:
        try:
            user_init.init(opts)
        except Exception:
            _handle_user_init_error("Error executing user init function in %s."
                                    % user_init.__file__)

    app.post_init()
    signal_wakeup(app)
    signal.signal(signal.SIGINT, lambda s, h: app.quit())
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
