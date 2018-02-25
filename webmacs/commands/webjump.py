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

import logging
from collections import namedtuple

from PyQt5.QtCore import QUrl, QThread, pyqtSlot as Slot, \
    pyqtSignal as Signal, QStringListModel, QObject


from ..minibuffer.prompt import Prompt, PromptTableModel, PromptHistory
from ..commands import define_command
from .. import current_buffer
from ..application import app
from .prompt_helper import PromptNewBuffer
from .. import variables


WebJump = namedtuple("WebJump", ("url", "doc", "allow_args", "complete_fn"))
WEBJUMPS = {}


webjump_default = variables.define_variable(
    "webjump-default",
    "The default webjump",
    "",
    conditions=(
        variables.condition(
            lambda v: not v or v in WEBJUMPS,
            "Must be one of %s." % (tuple(WEBJUMPS),)
        ),
    ),
)


def define_webjump(name, url, doc="", complete_fn=None):
    """
    Define a webjump.

    A webjump is a quick way to access an url, optionally with a
    variable section (for example an url for a google search). A
    function might be given to provide auto-completion.

    :param name: the name of the webjump.
    :param url: the url of the webjump. If the url contains "%s", it is
                assumed that it as a variable part.
    :param doc: associated documentation for the webjump.
    :param complete_fn: a function that provides autocompletion. The
                        function takes one parameter, the current
                        text, and must returns a list of strings (the
                        possible completions)

    """
    allow_args = "%s" in url
    WEBJUMPS[name.strip()] = WebJump(url, doc, allow_args, complete_fn)


def set_default(name):
    """
    Set the default webjump.

    Deprecated: use the *webjump-default* variable instead.

    :param name: the name of the webjump.
    """
    webjump_default.set_value(name)


class CompletionReceiver(QObject):
    got_completions = Signal(list)

    @Slot(object, str, str)
    def get_completions(self, w, name, text):
        try:
            completions = [name + d for d in w.complete_fn(text)]
        except Exception:
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
            data.append((name, w.doc))

        for url, name in self.bookmarks:
            data.append((name, url))

        return PromptTableModel(data)

    def enable(self, minibuffer):
        self.bookmarks = app().bookmarks().list()
        Prompt.enable(self, minibuffer)
        self.new_buffer = PromptNewBuffer(self.force_new_buffer)
        self.new_buffer.enable(minibuffer)
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
        return self.new_buffer.get_buffer()


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
        if webjump_default.value:
            minibuffer.input().setText(webjump_default.value)


def get_url(prompt):
    value = prompt.value()

    args = value.split(" ", 1)
    command = args[0]
    try:
        webjump = WEBJUMPS[command]
    except KeyError:
        bookmarks = {name: url
                     for url, name in prompt.bookmarks}
        try:
            return bookmarks[value]
        except KeyError:
            pass

        if "://" not in value:
            url = QUrl.fromUserInput(value)
            if url.isValid():
                # default scheme is https for us
                if url.scheme() == "http":
                    url.setScheme("https")
                return url
        return value

    if webjump.allow_args:
        args = args[1] if len(args) > 1 else ""
        return webjump.url % str(QUrl.toPercentEncoding(args), "utf-8")
    else:
        return webjump.url


@define_command("go-to", prompt=WebJumpPrompt)
def go_to(prompt):
    """
    Prompt to open an url or a webjump.
    """
    url = get_url(prompt)
    if url:
        prompt.get_buffer().load(url)


@define_command("go-to-selected-url", prompt=WebJumpPromptCurrentUrl)
def go_to_selected_url(prompt):
    """
    Prompt (defaulting to current selection) to open an url or a webjump.
    """
    go_to(prompt)


class WebJumpPromptNewUrl(WebJumpPrompt):
    force_new_buffer = True


@define_command("go-to-new-buffer", prompt=WebJumpPromptNewUrl)
def go_to_new_buffer(prompt):
    """
    Prompt to open an url or webjump in a new buffer.
    """
    go_to(prompt)


class WebJumpPromptCurrentUrlNewBuffer(WebJumpPromptCurrentUrl):
    force_new_buffer = True


@define_command(
    "go-to-selected-url-new-buffer",
    prompt=WebJumpPromptCurrentUrlNewBuffer
)
def go_to_selected_url_new_buffer(prompt):
    """
    Prompt (defaulting to current selection) to open an url or a webjump.
    """
    go_to(prompt)


@define_command("search-default", prompt=DefaultSearchPrompt)
def search_default(prompt):
    """
    Prompt to open an url with the default webjump.
    """
    go_to(prompt)


class DefaultSearchPromptNewBuffer(DefaultSearchPrompt):
    force_new_buffer = True


@define_command(
    "search-default-new-buffer", prompt=DefaultSearchPromptNewBuffer)
def search_default_new_buffer(prompt):
    """
    Prompt to open an url with the default webjump.
    """
    go_to_new_buffer(prompt)
