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
import os

from PyQt5.QtNetwork import QAbstractSocket

from .ipc import IpcServer
from . import variables


log_to_disk = variables.define_variable(
    "log-to-disk-max-files",
    "Maximum number of log files to keep. Log files are stored in"
    " ~/.webmacs/logs. Setting this to a number less or"
    "equal to 0 will deactivate file logging completely.",
    0,
    conditions=(
        variables.condition(lambda x: isinstance(x, int),
                            "Must be an int"),
    ),
)


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
    root = logging.getLogger()
    webcontent = logging.getLogger("webcontent")
    for logger, format, lvl in (
            (root,
             "%(levelname)s: %(message)s",
             level),
            (webcontent,
             "%(levelname)s %(name)s: [%(url)s] %(message)s",
             webcontent_level)):
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        fmt = logging.Formatter("%(levelname)s: %(message)s")
        handler.setFormatter(fmt)
        handler.setLevel(lvl)
        logger.addHandler(handler)

    webcontent.propagate = False


def setup_logging_on_disk(log_dir, backup_count=5):
    from logging.handlers import RotatingFileHandler

    root = logging.getLogger()
    webcontent = logging.getLogger("webcontent")

    class Formatter(logging.Formatter):
        def formatMessage(self, record):
            fmt = ("%(levelname)s %(name)s: [%(url)s] %(message)s"
                   if record.name == "webcontent"
                   else "%(levelname)s: %(message)s")
            return fmt % record.__dict__

    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)

    handler = RotatingFileHandler(os.path.join(log_dir, "log"),
                                  backupCount=backup_count,
                                  delay=True)
    handler.setFormatter(Formatter())
    handler.doRollover()
    handler.setLevel(logging.DEBUG)

    for logger in (root, webcontent):
        logger.addHandler(handler)


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
    from .application import app
    from .session import session_load, session_save
    from .window import Window
    from .webbuffer import create_buffer

    a = app()
    a.aboutToQuit.connect(lambda: session_save(a.profile.session_file))

    def create_window(url):
        w = Window()
        buff = create_buffer(url)
        w.current_webview().setBuffer(buff)
        w.showMaximized()

    home_page = variables.get("home-page")
    session_file = a.profile.session_file
    if home_page:
        create_window(home_page)
    elif opts.url:
        create_window(opts.url)
    elif os.path.exists(session_file):
        try:
            session_load(session_file)
        except Exception:
            create_window("http://duckduckgo.com/")


def _handle_user_init_error(msg):
    import traceback
    from .application import app

    conf_path = app().conf_path()
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

    conf_path = os.path.join(os.path.expanduser("~"), ".webmacs")
    if not os.path.isdir(conf_path):
        os.makedirs(conf_path)

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

    # Delay loading after command line parsing and ipc checking.
    # Loading qwebengine stuff takes a couple of seconds...
    from .application import Application, _app_requires

    _app_requires()

    # load a user init module if any
    try:
        spec = imp.find_module("init", [conf_path])
    except ImportError:
        user_init = None
    else:
        try:
            user_init = imp.load_module("_webmacs_userconfig", *spec)
        except Exception:
            _handle_user_init_error("Error reading the user configuration.")

    app = Application(conf_path, [
        # The first argument passed to the QApplication args defines
        # the x11 property WM_CLASS.
        "webmacs" if not opts.instance
        else "webmacs-%s" % opts.instance
    ])
    server = IpcServer(opts.instance)
    atexit.register(server.cleanup)

    # execute the user init function if there is one
    if user_init is None or not hasattr(user_init, "init"):
        init(opts)
    else:
        try:
            user_init.init(opts)
        except Exception:
            _handle_user_init_error("Error executing user init function in %s."
                                    % user_init.__file__)

    if log_to_disk.value > 0:
        setup_logging_on_disk(os.path.join(conf_path, "logs"),
                              backup_count=log_to_disk.value)
    app.post_init()
    signal_wakeup(app)
    signal.signal(signal.SIGINT, lambda s, h: app.quit())
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
