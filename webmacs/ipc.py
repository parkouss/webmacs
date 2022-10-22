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

import os
import json
import struct
import logging
from PyQt6.QtCore import QObject, pyqtSlot as Slot, pyqtSignal as Signal, Qt, \
    QDir
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from . import version


HEADER_FMT = "!I"
HEADER_SIZE = struct.calcsize(HEADER_FMT)


class IPcReader(QObject):
    message_received = Signal(object)

    def __init__(self, sock):
        QObject.__init__(self)
        self.sock = sock
        self._msg_size = None
        self._data = b""

    @Slot()
    def on_ready_read(self):
        if self._msg_size is None:
            if self.sock.bytesAvailable() < HEADER_SIZE:
                # not enough data yet
                return
            self._msg_size = struct.unpack(HEADER_FMT,
                                           self.sock.read(HEADER_SIZE))[0]
        remaining = self._msg_size - len(self._data)
        if remaining <= 0:
            return
        self._data += self.sock.read(min(remaining,
                                         self.sock.bytesAvailable()))
        if len(self._data) == self._msg_size:
            msg = json.loads(self._data.decode("utf-8"))
            self.message_received.emit(msg)
            return msg

    @Slot(object)
    def send_data(self, data):
        data = json.dumps(data).encode("utf-8")
        len_data = len(data)
        self.sock.write(struct.pack(HEADER_FMT, len_data))
        self.sock.write(data)

    def get_data(self):
        while self.sock.waitForReadyRead():
            r = self.on_ready_read()
            if r is not None:
                return r

    def clear(self):
        self.sock.deleteLater()
        self.sock = None


class IpcServer(QObject):
    @classmethod
    def get_sock_name(cls, instance):
        run_path = f"/run/user/{os.getuid()}"
        prefix = run_path if os.access(run_path, os.W_OK) else ""

        if instance == "default":
            return os.path.join(prefix, "webmacs.ipc")
        return os.path.join(prefix, f"webmacs.{instance}.ipc")

    @classmethod
    def list_all_instances(cls, check=True):
        if version.is_windows:
            logging.error(
                "list all instances is not supported on windows"
            )
            return []
        # from qt sources, named pipes are created in QDir.tempPath()
        instances = [
            n[8:-4] or "default"
            for n in os.listdir(QDir.tempPath())
            if n.startswith("webmacs.") and n.endswith(".ipc")
        ]
        if check:
            new_instances = []
            for instance in instances:
                local = cls.check_server_connection(instance)
                if local is not None:
                    local.clear()
                    new_instances.append(instance)
            instances = new_instances
        return instances

    @classmethod
    def instance_send(cls, instance, data, cb=None):
        """
        Send some data to a webmacs instance asynchronously.
        """
        conn = cls.check_server_connection(instance)
        if conn is None:
            return

        def callback(result):
            conn.clear()
            if cb is not None:
                cb(result)

        conn.message_received.connect(callback)
        conn.send_data(data)

    @classmethod
    def check_server_connection(cls, instance=None):
        sock = QLocalSocket()
        sock.connectToServer(cls.get_sock_name(instance))
        if sock.waitForConnected(1000):
            return IPcReader(sock)
        return None

    def __init__(self, instance=None):
        QObject.__init__(self)
        sock_name = self.get_sock_name(instance)
        QLocalServer.removeServer(sock_name)
        self._server = QLocalServer()
        self._server.setSocketOptions(
            QLocalServer.SocketOption.UserAccessOption)
        self._server.newConnection.connect(self._on_new_connection)
        if not self._server.listen(sock_name):
            logging.error("Can not start ipc: %s"
                          % self._server.errorString())
        self._readers = {}

    def cleanup(self):
        try:
            os.unlink(self._server.fullServerName())
        except OSError:
            pass

    @Slot()
    def _on_new_connection(self):
        conn = self._server.nextPendingConnection()
        reader = IPcReader(conn)
        reader.message_received.connect(self.handle_data)
        conn.readyRead.connect(reader.on_ready_read)
        conn.disconnected.connect(self.reader_disconnected)
        self._readers[conn] = reader

    @Slot(object)
    def handle_data(self, data):
        reader = self.sender()
        try:
            res = ipc_dispatch(data)
        except Exception as exc:
            res = str(exc)

        if res in (True, None):
            reader.send_data({"result": True})
        else:
            reader.send_data({"result": False, "message": res})

    def reader_disconnected(self):
        conn = self.sender()
        reader = self._readers.pop(conn)
        reader.clear()
        reader.deleteLater()


def ipc_dispatch(data):
    from . import current_window
    from .webbuffer import create_buffer
    win = current_window()
    url = data.get("url")
    if url:
        view = win.current_webview()
        view.setBuffer(create_buffer(url))

    # this is quite hard to raise a window. The following works fine
    # for me with gnome 3.
    flags = win.windowFlags()
    win.setWindowFlags(flags | Qt.WindowType.Popup)
    win.raise_()
    win.activateWindow()
    win.setWindowFlags(flags)
    win.show()
