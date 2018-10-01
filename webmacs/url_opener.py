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

import sys

from .webbuffer import create_buffer
from .window import Window
from .ipc import IpcServer

from PyQt5.QtCore import QProcess, QUrl


def url_open(ctx, url, instance=None, new_window=False, new_buffer=False,
             allow_create_instance=False):
    """
    Open an url.
    """
    if instance is not None:
        if isinstance(url, QUrl):
            url = str(url.toEncoded(), "utf-8")
        instances = IpcServer.list_all_instances()
        if instance in instances:
            IpcServer.instance_send(instance, {"url": url})
        if allow_create_instance:
            QProcess.startDetached(
                sys.executable,
                ["-m", "webmacs.main", "--instance", instance, url]
            )
        return

    buffer = None

    if new_buffer or new_window:
        buffer = create_buffer()
        if new_window:
            w = Window()
            w.current_webview().setBuffer(buffer)
            buffer.load(url)  # load before showing
            w.show()
            w.activateWindow()
            return
        else:
            ctx.view.setBuffer(buffer)
    else:
        buffer = ctx.buffer

    buffer.load(url)
