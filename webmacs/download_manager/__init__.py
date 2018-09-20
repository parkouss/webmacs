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
import shlex
import logging

from PyQt5.QtCore import QObject, pyqtSlot as Slot, pyqtSignal as Signal, \
    QProcess

from PyQt5.QtWebEngineWidgets import QWebEngineDownloadItem

from .prompts import (DlChooseActionPrompt, DlOpenActionPrompt, DlPrompt,
                      OverwriteFilePrompt)
from .. import current_minibuffer
from .. import hooks


STATE_STR = {
    QWebEngineDownloadItem.DownloadRequested: "Requested",
    QWebEngineDownloadItem.DownloadInProgress: "In progress",
    QWebEngineDownloadItem.DownloadCompleted: "Completed",
    QWebEngineDownloadItem.DownloadCancelled: "Cancelled",
    QWebEngineDownloadItem.DownloadInterrupted: "Interrupted",
}


def state_str(state):
    return STATE_STR.get(state, "Unknown state")


def download_to_json(dlitem):
    try:
        progress = (round(dlitem.receivedBytes() / float(dlitem.totalBytes())
                          * 100, 2))
    except ZeroDivisionError:
        progress = -1
    return json.dumps({
        "path": dlitem.path(),
        "state": state_str(dlitem.state()),
        "id": dlitem.id(),
        "isFinished": dlitem.isFinished(),
        "progress": progress,
    })


class DownloadManager(QObject):
    download_started = Signal(object)

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.downloads = []
        self._buffers = []  # list of web buffers currently showing downloads
        self._running_procs = {}

        def on_buffer_load_finished(buff):
            url = buff.url()
            if url.scheme() == "webmacs" and url.authority() == "downloads":
                self.attach_buffer(buff)
            else:
                self.detach_buffer(buff)

        hooks.webbuffer_load_finished.add(on_buffer_load_finished)
        hooks.webbuffer_closed.add(self.detach_buffer)

    def attach_buffer(self, buffer):
        self._buffers.append(buffer)
        for dl in self.downloads:
            buffer.runJavaScript("add_download(%s);" % download_to_json(dl))

    def detach_buffer(self, buffer):
        try:
            self._buffers.remove(buffer)
        except ValueError:
            pass

    def _start_download(self, dlitem):
        dlitem.accept()
        self.downloads.append(dlitem)
        dlitem.destroyed.connect(lambda: self.downloads.remove(dlitem))
        self.download_started.emit(dlitem)
        dl = download_to_json(dlitem)
        for buffer in self._buffers:
            buffer.runJavaScript("add_download(%s);" % dl)
        dlitem.downloadProgress.connect(self._download_state_changed)
        dlitem.stateChanged.connect(self._download_state_changed)
        dlitem.finished.connect(self._download_state_changed)
        dlitem.finished.connect(dlitem.deleteLater)

    @Slot()
    def _download_state_changed(self):
        dlitem = self.sender()
        dl = download_to_json(dlitem)
        for buffer in self._buffers:
            buffer.runJavaScript("update_download(%s);" % dl)

    @Slot("QWebEngineDownloadItem*")
    def download_requested(self, dl):
        minibuff = current_minibuffer()

        prompt = DlChooseActionPrompt(dl.path(), dl.mimeType())
        action = minibuff.do_prompt(prompt)

        if action == "open":
            prompt = DlOpenActionPrompt()
            executable = minibuff.do_prompt(prompt)
            if executable is None:
                return

            logging.info("Downloading %s...", dl.path())

            def finished():
                if dl.state() == QWebEngineDownloadItem.DownloadCompleted:
                    logging.info("Opening external file %s with %s",
                                 dl.path(), executable)
                    self._run_program(executable, dl.path())

            dl.finished.connect(finished)
            self._start_download(dl)

        elif action == "download":

            prompt = DlPrompt(dl.path(), dl.mimeType())
            path = minibuff.do_prompt(prompt)
            if path is None:
                return

            if os.path.isfile(path):
                if not minibuff.do_prompt(OverwriteFilePrompt(path)):
                    return

            dl.setPath(path)
            logging.info("Downloading %s...", dl.path())

            def finished():
                state = state_str(dl.state())
                logging.info("Finished download [%s] of %s", state, dl.path())
                minibuff.show_info("[{}] download: {}".format(state,
                                                              dl.path()))
            dl.finished.connect(finished)
            self._start_download(dl)

    def _run_program(self, executable, path):
        shell_arg = "{} {}".format(executable, shlex.quote(path))
        args = ["-c", shell_arg]
        shell = get_shell()
        proc = QProcess()
        self._running_procs[proc] = path

        logging.debug("Executing command: %s %s", shell, " ".join(args))

        proc.finished.connect(self._program_finished)
        proc.start(shell, args, QProcess.ReadOnly)

    @Slot(int, QProcess.ExitStatus)
    def _program_finished(self, code, status):
        proc = self.sender()
        path = self._running_procs.pop(proc)
        logging.debug("Removing downloaded file %s", path)
        try:
            os.unlink(path)
        except Exception:
            pass


def get_shell():
    return os.environ.get("SHELL", "/bin/sh")
