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
import sys
import atexit
import os
import warnings

from PyQt5.QtNetwork import QAbstractSocket

from .ipc import IpcServer
from . import variables, filter_webengine_output
from .xdg_utils import XDG_CACHE_HOME, XDG_CONFIG_HOME, XDG_DATA_HOME


log_to_disk = variables.define_variable(
    "log-to-disk-max-files",
    "Maximum number of log files to keep. Log files are stored in"
    " $XDG_DATA_HOME/webmacs/logs. Setting this to 0 will deactivate file "
    " logging completely.",
    0,
    type=variables.Int(min=0),
)


def signal_wakeup(app):
    """
    Allow to be notified in Python for signals when in long-running calls from
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
        fmt = logging.Formatter(format)
        handler.setFormatter(fmt)
        handler.setLevel(lvl)
        logger.addHandler(handler)

    webcontent.propagate = False

    warnings.filterwarnings('always', r"^.*$", DeprecationWarning,
                            r"^webmacs.*$")


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

    # There is no such JavaScript error level, critical - still since there
    # are some logs that are printed anyway and that it is easier to implement.
    # Let's keep the critical level.
    parser.add_argument("-w", "--webcontent-log-level",
                        help="Set the log level for the web contents,"
                        " defaults to %(default)s.",
                        default="critical",
                        choices=("info", "warning", "error", "critical"))

    parser.add_argument("-i", "--instance", default="default",
                        help="Create or reuse a named webmacs instance."
                        " If the given instance name is the empty string, an"
                        " automatically generated name will be used.")

    parser.add_argument("-c", "--config",
                        default=os.path.join(XDG_CONFIG_HOME, "webmacs"),
                        help="The path from which to load the configuration "
                        "module.")

    parser.add_argument("--list-instances", action="store_true",
                        help="List running instances and exit.")

    parser.add_argument("url", nargs="?",
                        help="url to open")

    opts = parser.parse_args(argv)

    # handle local file path
    if opts.url and os.path.exists(opts.url) \
       and not os.path.isabs(opts.url):
        opts.url = os.path.realpath(opts.url)

    return opts


def init(opts):
    """
    Default initialization of webmacs.

    If a URL is given on the command line, this method opens it. Else, it tries
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


def _handle_user_init_error(conf_path, msg):
    import traceback

    stack_size = 0
    tbs = traceback.extract_tb(sys.exc_info()[2])
    for i, t in enumerate(tbs):
        if t[0].startswith(conf_path):
            stack_size = -len(tbs[i:])
            break
    logging.critical(("%s\n\n" % msg)
                     + traceback.format_exc(stack_size))
    sys.exit(1)


if sys.version_info >= (3, 5):
    import importlib.machinery
    import importlib.util

    def load_user_module(conf_path):
        spec = importlib.machinery.PathFinder.find_spec("init", [conf_path])
        if spec is None:
            return None
        user_init = importlib.util.module_from_spec(spec)
        sys.modules["init"] = user_init
        spec.loader.exec_module(user_init)
        return user_init
else:
    import imp

    def load_user_module(conf_path):
        try:
            spec = imp.find_module("init", [conf_path])
        except ImportError:
            return None
        return imp.load_module("_webmacs_userconfig", *spec)


def main():
    opts = parse_args()

    if opts.list_instances:
        for instance in IpcServer.list_all_instances():
            print(instance)
        sys.exit(0)
    elif not opts.instance:
        # pick a random instance name.
        uniq = [int(n) for n in IpcServer.list_all_instances(check=False)
                if n.isdigit()]
        opts.instance = str(max(uniq) + 1) if uniq else "1"

    conf_path = opts.config
    if not os.path.isdir(conf_path):
        deprecated = os.path.expanduser("~/.webmacs")
        if os.path.isdir(deprecated):
            # Since logging has not been setup yet, use manual print
            print("Warning: '{}' as an init directory has been deprecated. "
                  "Please use '{}' or configure it using '-c' instead."
                  .format(deprecated, conf_path), file=sys.stderr)
            conf_path = deprecated
        else:
            os.makedirs(conf_path)

    data_path = os.path.join(XDG_DATA_HOME, "webmacs")
    if not os.path.isdir(data_path):
        deprecated = os.path.expanduser("~/.webmacs")
        if os.path.isdir(deprecated):
            # Since logging has not been setup yet, use manual print
            print("Warning: '{}' as a data directory has been deprecated. "
                  "Please move your profile and adblock directories to '{}'."
                  .format(deprecated, data_path), file=sys.stderr)
            data_path = deprecated
        else:
            os.makedirs(data_path)

    cache_path = os.path.join(XDG_CACHE_HOME, "webmacs")
    if not os.path.isdir(data_path):
        os.makedirs(cache_path)

    out_filter = filter_webengine_output.make_filter()

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
        user_init = load_user_module(conf_path)
    except Exception:
        _handle_user_init_error(
            conf_path,
            "Error reading the user configuration."
        )

    app = Application(data_path, cache_path, [
        # The first argument passed to the QApplication args defines
        # the x11 property WM_CLASS.
        "webmacs" if opts.instance == "default"
        else "webmacs-%s" % opts.instance
    ], instance_name=opts.instance)
    server = IpcServer(opts.instance)
    atexit.register(server.cleanup)

    out_filter.enable()

    # execute the user init function if there is one
    if user_init is None or not hasattr(user_init, "init"):
        init(opts)
    else:
        try:
            user_init.init(opts)
        except Exception:
            _handle_user_init_error(
                data_path,
                "Error executing user init function in %s."
                % user_init.__file__
            )

    if log_to_disk.value > 0:
        setup_logging_on_disk(os.path.join(data_path, "logs"),
                              backup_count=log_to_disk.value)
    app.post_init()
    signal_wakeup(app)
    signal.signal(signal.SIGINT, lambda s, h: app.quit())
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
