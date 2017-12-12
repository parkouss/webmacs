import logging
from collections import namedtuple

from PyQt5.QtCore import QUrl, QThread, pyqtSlot as Slot, \
    pyqtSignal as Signal, QStringListModel, QObject


from ..minibuffer.prompt import Prompt, PromptTableModel, PromptHistory
from ..commands import define_command
from ..webbuffer import create_buffer
from .. import current_window, current_buffer
from ..application import app
from ..keyboardhandler import current_prefix_arg

WebJump = namedtuple("WebJump", ("url", "doc", "allow_args", "complete_fn"))
WEBJUMPS = {}
DEFAULT_WEBJUMP_SEARCH = None


def define_webjump(name, url, doc="", complete_fn=None):
    allow_args = "%s" in url
    WEBJUMPS[name] = WebJump(url, doc, allow_args, complete_fn)


def set_default(text):
    global DEFAULT_WEBJUMP_SEARCH
    DEFAULT_WEBJUMP_SEARCH = text


class CompletionReceiver(QObject):
    got_completions = Signal(list)

    @Slot(object, str, str)
    def get_completions(self, w, name, text):
        try:
            completions = [name + d for d in w.complete_fn(text)]
        except:
            logging.exception("Can not autocomplete for the webjump.")
        else:
            self.got_completions.emit(completions)


class WebJumpPrompt(Prompt):
    label = "url/webjump:"
    complete_options = {
        "autocomplete": True,
    }
    history = PromptHistory()

    ask_completions = Signal(object, str, str)
    force_new_buffer = False

    def completer_model(self):
        data = []
        for name, w in WEBJUMPS.items():
            if w.allow_args:
                name = name
            data.append((name, w.doc))
        return PromptTableModel(data)

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        if self.force_new_buffer:
            self.new_buffer = True
        else:
            self.new_buffer = current_prefix_arg() == (4,)
        if self.new_buffer:
            minibuffer.label.setText(minibuffer.label.text() + " (new buffer)")
        minibuffer.input().textEdited.connect(self._text_edited)
        self._wc_model = QStringListModel()
        self._wb_model = minibuffer.input().completer_model()
        self._cthread = QThread(app())
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
                name = name
                if text.startswith(name):
                    model = self._wc_model
                    self._active_webjump = (w, name)
                    if self._completion_timer != 0:
                        self.killTimer(self._completion_timer)
                    self._completion_timer = self.startTimer(10)
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

    def get_buffer(self):
        if self.new_buffer:
            buf = create_buffer()
            view = current_window().current_web_view()
            view.setBuffer(buf)
        else:
            buf = current_buffer()
        return buf


class WebJumpPromptCurrentUrl(WebJumpPrompt):
    def enable(self, minibuffer):
        WebJumpPrompt.enable(self, minibuffer)
        url = current_buffer().url().toString()
        input = minibuffer.input()
        input.setText(url)
        input.setSelection(0, len(url))


class DefaultSearchPrompt(WebJumpPrompt):
    def enable(self, minibuffer):
        WebJumpPrompt.enable(self, minibuffer)
        if DEFAULT_WEBJUMP_SEARCH:
            minibuffer.input().setText(DEFAULT_WEBJUMP_SEARCH)


def get_url(value):
    args = value.split(" ", 1)
    command = args[0] + " "
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
        prompt.get_buffer().load(url)


@define_command("go-to-selected-url", prompt=WebJumpPromptCurrentUrl)
def go_to_selected_url(prompt):
    url = get_url(prompt.value())
    if url:
        prompt.get_buffer().load(url)


class WebJumpPromptNewUrl(WebJumpPrompt):
    force_new_buffer = False


@define_command("go-to-new-buffer", prompt=WebJumpPromptNewUrl)
def go_to_new_buffer(prompt):
    url = get_url(prompt.value())
    if url:
        view = current_window().current_web_view()
        view.setBuffer(create_buffer(url))


@define_command("search-default", prompt=DefaultSearchPrompt)
def search_default(prompt):
    go_to(prompt)
