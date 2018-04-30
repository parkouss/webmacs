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

import json

from PyQt5.QtCore import QObject, pyqtSlot as Slot, pyqtSignal as Signal

from PyQt5.QtWebEngineWidgets import QWebEngineDownloadItem

from ..minibuffer.prompt import Prompt, FSModel
from .. import current_minibuffer
from ..minibuffer.keymap import KEYMAP, cancel
from ..keymaps import Keymap

DL_PROMPT_KEYMAP = Keymap("dl-prompt", parent=KEYMAP)

STATE_STR = {
    QWebEngineDownloadItem.DownloadRequested: "Requested",
    QWebEngineDownloadItem.DownloadInProgress: "In progress",
    QWebEngineDownloadItem.DownloadCompleted: "Completed",
    QWebEngineDownloadItem.DownloadCancelled: "Cancelled",
    QWebEngineDownloadItem.DownloadInterrupted: "Interrupted",
}


def state_str(state):
    return STATE_STR.get(state, "Unknown state")


@DL_PROMPT_KEYMAP.define_key("C-g")
def cancel_dl(ctx):
    prompt = ctx.minibuffer.prompt()
    prompt._dl.cancel()
    cancel(ctx)
    prompt.finished.emit()  # to end the event loop


class DlPrompt(Prompt):
    keymap = DL_PROMPT_KEYMAP
    complete_options = {
        "autocomplete": True
    }
    download_started = Signal(object)

    def __init__(self, dl):
        Prompt.__init__(self, None)
        self._dl = dl
        self.label = "Download file [{}]:".format(dl.mimeType())

    def completer_model(self):
        # todo, not working
        model = FSModel(self)
        return model

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        minibuffer.input().setText(self._dl.path())

    def _on_edition_finished(self):
        path = self.minibuffer.input().text()
        self._dl.setPath(path)
        self._dl.accept()
        self.download_started.emit(self._dl)
        Prompt._on_edition_finished(self)


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

    def attach_buffer(self, buffer):
        self._buffers.append(buffer)
        for dl in self.downloads:
            buffer.runJavaScript("add_download(%s);" % download_to_json(dl))

    def detach_buffer(self, buffer):
        try:
            self._buffers.remove(buffer)
        except ValueError:
            pass

    def _download_started(self, dlitem):
        self.downloads.append(dlitem)
        dlitem.destroyed.connect(lambda: self.downloads.remove(dlitem))
        self.download_started.emit(dlitem)
        dl = download_to_json(dlitem)
        for buffer in self._buffers:
            buffer.runJavaScript("add_download(%s);" % dl)
        dlitem.downloadProgress.connect(self._download_state_changed)
        dlitem.stateChanged.connect(self._download_state_changed)
        dlitem.finished.connect(self._download_state_changed)

    @Slot()
    def _download_state_changed(self):
        dlitem = self.sender()
        dl = download_to_json(dlitem)
        for buffer in self._buffers:
            buffer.runJavaScript("update_download(%s);" % dl)

    @Slot("QWebEngineDownloadItem*")
    def download_requested(self, dl):
        minibuff = current_minibuffer()
        prompt = DlPrompt(dl)
        prompt.download_started.connect(self._download_started)

        def finished():
            state = state_str(dl.state())
            minibuff.show_info("[{}] download: {}".format(state, dl.path()))

        dl.finished.connect(finished)

        minibuff.do_prompt(prompt)
