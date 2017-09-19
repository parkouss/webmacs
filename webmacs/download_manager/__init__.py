from PyQt5.QtCore import QObject, pyqtSlot as Slot, QEventLoop
from PyQt5.QtWidgets import QFileSystemModel

from ..minibuffer.prompt import Prompt
from ..minibuffer import current_minibuffer
from ..minibuffer.keymap import KEYMAP
from ..keymaps import Keymap

DL_PROMPT_KEYMAP = Keymap("dl-prompt", parent=KEYMAP)


@DL_PROMPT_KEYMAP.define_key("C-g")
def cancel_dl():
    prompt = current_minibuffer().prompt()
    prompt._dl.cancel()
    prompt.close()
    prompt.finished.emit()


class DlPrompt(Prompt):
    keymap = DL_PROMPT_KEYMAP

    def __init__(self, dl):
        Prompt.__init__(self)
        self._dl = dl
        self.label = "Download file [{}]:".format(dl.mimeType())

    def completer_model(self):
        # todo, not working
        model = QFileSystemModel(self)
        model.setRootPath("")
        return model

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        minibuffer.input().setText(self._dl.path())

    def _on_edition_finished(self):
        path = self.minibuffer.input().text()
        self._dl.setPath(path)
        self._dl.accept()
        Prompt._on_edition_finished(self)


class DownloadManager(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)

    @Slot("QWebEngineDownloadItem*")
    def download_requested(self, dl):
        minibuff = current_minibuffer()
        prompt = DlPrompt(dl)

        def finished():
            state = {
                dl.DownloadCompleted: "Completed",
                dl.DownloadCancelled: "Cancelled",
                dl.DownloadInterrupted: "Interrupted",
            }.get(dl.state(), "Unknown state")
            minibuff.show_info("[{}] download: {}".format(state, dl.path()))

        loop = QEventLoop()
        prompt.finished.connect(loop.quit)
        dl.finished.connect(finished)

        minibuff.do_prompt(prompt)

        loop.exec_()
