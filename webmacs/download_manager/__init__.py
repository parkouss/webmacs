import json

from PyQt5.QtCore import QObject, pyqtSlot as Slot, QEventLoop, \
    pyqtSignal as Signal

from PyQt5.QtWebEngineWidgets import QWebEngineDownloadItem

from ..minibuffer.prompt import Prompt, FSModel
from ..minibuffer import current_minibuffer
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
def cancel_dl():
    prompt = current_minibuffer().prompt()
    prompt._dl.cancel()
    cancel()
    prompt.finished.emit()  # to end the event loop


class DlPrompt(Prompt):
    keymap = DL_PROMPT_KEYMAP
    complete_options = {
        "autocomplete": True
    }
    download_started = Signal(object)

    def __init__(self, dl):
        Prompt.__init__(self)
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
    return json.dumps({
        "path": dlitem.path(),
        "state": state_str(dlitem.state()),
        "id": dlitem.id(),
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

        loop = QEventLoop()
        prompt.finished.connect(loop.quit)
        dl.finished.connect(finished)

        minibuff.do_prompt(prompt)

        loop.exec_()
