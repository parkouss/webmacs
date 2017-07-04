from collections import namedtuple

from PyQt5.QtCore import QUrl, QThread, pyqtSlot as Slot, \
    pyqtSignal as Signal, QStringListModel, QObject


from ..minibuffer import Prompt, PromptTableModel
from ..commands import define_command
from ..webbuffer import current_buffer, create_buffer
from ..window import current_window
from ..application import Application

WebJump = namedtuple("WebJump", ("url", "doc", "allow_args", "complete_fn"))
WEBJUMPS = {}


def define_webjump(name, url, doc="", complete_fn=None):
    allow_args = "%s" in url
    WEBJUMPS[name] = WebJump(url, doc, allow_args, complete_fn)


class CompletionReceiver(QObject):
    got_completions = Signal(list)

    @Slot(object, str, str)
    def get_completions(self, w, name, text):
        self.got_completions.emit([name + d
                                   for d in w.complete_fn(text)])


class WebJumpPrompt(Prompt):
    label = "url/webjump:"
    complete_options = {
        "autocomplete": True,
    }

    ask_completions = Signal(object, str, str)

    def completer_model(self):
        data = []
        for name, w in WEBJUMPS.items():
            if w.allow_args:
                name = name + " "
            data.append((name, w.doc))
        return PromptTableModel(data)

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        minibuffer.input().textEdited.connect(self._text_edited)
        self._wc_model = QStringListModel()
        self._wb_model = minibuffer.input().completer_model()
        self._cthread = QThread(Application.INSTANCE)
        self._creceiver = CompletionReceiver()
        self._creceiver.moveToThread(self._cthread)
        self._completion_timer = 0
        self._active_webjump = None
        self._cthread.finished.connect(self._cthread.deleteLater)
        self.ask_completions.connect(self._creceiver.get_completions)
        self._creceiver.got_completions.connect(self._got_completions)
        self._cthread.start()

    def _text_edited(self, text):
        model = self._wb_model
        for name, w in WEBJUMPS.items():
            if w.allow_args and w.complete_fn:
                name = name + " "
                if text.startswith(name):
                    model = self._wc_model
                    self._active_webjump = (w, name)
                    if self._completion_timer != 0:
                        self.killTimer(self._completion_timer)
                    self._completion_timer = self.startTimer(250)
                    break
        if self.minibuffer.input().completer_model() != model:
            self.minibuffer.input().popup().hide()
            self.minibuffer.input().set_completer_model(model)

    def timerEvent(self, _):
        text = self.minibuffer.input().text()
        w, name = self._active_webjump
        self.ask_completions.emit(w, name, text[len(name):])
        self.killTimer(self._completion_timer)
        self._completion_timer = 0

    @Slot(list)
    def _got_completions(self, data):
        self._wc_model.setStringList(data)
        self.minibuffer.input().show_completions()

    def close(self):
        Prompt.close(self)
        self._cthread.quit()
        # not sure if those are required;
        self._wb_model.deleteLater()
        self._wc_model.deleteLater()


def get_url(value):
    args = value.split(" ", 1)
    command = args[0]
    try:
        webjump = WEBJUMPS[command]
    except KeyError:
        return value

    if webjump.allow_args:
        args = args[1] if len(args) > 1 else ""
        return webjump.url % str(QUrl.toPercentEncoding(args), "utf-8")
    else:
        return webjump.url


@define_command("go-to", prompt=WebJumpPrompt)
def go_to(prompt):
    url = get_url(prompt.value())
    if url:
        current_buffer().load(url)


class WebJumpPromptNewUrl(WebJumpPrompt):
    label = "url/webjump (new buffer):"


@define_command("go-to-new-buffer", prompt=WebJumpPromptNewUrl)
def go_to_new_buffer(prompt):
    url = get_url(prompt.value())
    if url:
        view = current_window().current_web_view()
        view.setBuffer(create_buffer(url))
