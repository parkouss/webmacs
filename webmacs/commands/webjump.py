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


WebJump = namedtuple(
    "WebJump", ("name", "url", "doc", "allow_args", "complete_fn", "protocol"))
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


def define_webjump(name, url, doc="", complete_fn=None, protocol=False):
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
    :param protocol: True if the webjump should be treated as the protocol
                     part of a URI (eg: file://)

    """
    allow_args = "%s" in url
    WEBJUMPS[name.strip()] = WebJump(name.strip(), url,
                                     doc, allow_args, complete_fn, protocol)


def define_protocol(name, doc="", complete_fn=None):
    define_webjump(name, name+"://%s", doc, complete_fn, True)


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
            completions = w.complete_fn(text)
        except Exception:
            logging.exception("Can not autocomplete for the webjump.")
        else:
            self.got_completions.emit(completions)


class WebJumpPrompt(Prompt):
    label = "url/webjump:"
    complete_options = {
        "autocomplete": True,
        "match": Prompt.SimpleMatch
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
        # reset the active webjump
        self._active_webjump = None

        # the text was deleted, nothing to do
        if text == "":
            return

        # search for a matching webjump
        first_word = text.split(" ")[0].split("://")[0]
        if first_word in [w for w in WEBJUMPS if len(w) < len(text)]:
            model = self._wc_model
            self._active_webjump = WEBJUMPS[first_word]
            # disable matching, we want all completions from
            # complete_fn
            self.minibuffer.input().set_match(
                Prompt.SimpleMatch if self._active_webjump.protocol else None)
            if self._completion_timer != 0:
                self.killTimer(self._completion_timer)
            self._completion_timer = self.startTimer(10)
        else:
            # didn't find a webjump, go back to matching
            # webjump/bookmark/history
            self.minibuffer.input().set_match(Prompt.SimpleMatch)
            model = self._wb_model

        if self.minibuffer.input().completer_model() != model:
            self.minibuffer.input().popup().hide()
            self.minibuffer.input().set_completer_model(model)

    def timerEvent(self, _):
        text = self.minibuffer.input().text()
        prefix = self._active_webjump.name + \
            ("://" if self._active_webjump.protocol else " ")
        self.ask_completions.emit(
            self._active_webjump, prefix, text[len(prefix):])
        self.killTimer(self._completion_timer)
        self._completion_timer = 0

    @Slot(list)
    def _got_completions(self, data):
        self._wc_model.setStringList(data)
        text = self.minibuffer.input().text()
        prefix = self._active_webjump.name + \
            ("://" if self._active_webjump.protocol else " ")
        self.minibuffer.input().show_completions(text[len(prefix):])

    def close(self):
        Prompt.close(self)
        self._cthread.quit()
        # not sure if those are required;
        self._wb_model.deleteLater()
        self._wc_model.deleteLater()

    def get_buffer(self):
        return self.new_buffer.get_buffer()

    def _on_completion_activated(self, index):
        super()._on_completion_activated(index)

        chosen_text = self.minibuffer.input().text()
        # if there is already an active webjump,
        if self._active_webjump:
            # add the selected completion after it
            if self._active_webjump.protocol:
                self.minibuffer.input().setText(self._active_webjump.name + "://" + chosen_text)
            else:
                self.minibuffer.input().setText(self._active_webjump.name + " " + chosen_text)

        # if we just chose a webjump
        # and not WEBJUMPS[chosen_text].protocol:
        elif chosen_text in WEBJUMPS:
            # add a space after the selection
            self.minibuffer.input().setText(
                chosen_text + (" " if not WEBJUMPS[chosen_text].protocol else "://"))


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

    # Look for webjumps
    webjump = None
    if command in WEBJUMPS:
        webjump = WEBJUMPS[command]
    else:
        # Look for a incomplete webjump, accepting a candidate
        # if there is a single option
        candidates = [wj for wj in WEBJUMPS if wj.startswith(command)]
        if len(candidates) == 1:
            webjump = WEBJUMPS[candidates[0]]

    if webjump:
        # found
        if webjump.allow_args:
            args = args[1] if len(args) > 1 else ""
            return webjump.url % str(QUrl.toPercentEncoding(args), "utf-8")
        else:
            return webjump.url

    # Look for a bookmark
    bookmarks = {name: url
                 for url, name in prompt.bookmarks}
    if value in bookmarks:
        return bookmarks[value]

    # Look for a incomplete bookmarks, accepting a candidate
    # if there is a single option
    candidates = [bm for bm in bookmarks if bm.startswith(command)]
    if len(candidates) == 1:
        return bookmarks[candidates[0]]

    # No webjump, no bookmark, look for a url
    if "://" not in value:
        url = QUrl.fromUserInput(value)
        if url.isValid():
            # default scheme is https for us
            if url.scheme() == "http":
                url.setScheme("https")
            return url
    return value


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
