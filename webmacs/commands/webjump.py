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

import re
import logging
from collections import namedtuple

from PyQt5.QtCore import QUrl, pyqtSlot as Slot, \
    pyqtSignal as Signal, QStringListModel, QObject, QEvent, Qt
from PyQt5.QtNetwork import QNetworkRequest

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
                                     doc,
                                     allow_args,
                                     complete_fn if complete_fn else
                                     lambda x: [],
                                     protocol)


def define_protocol(name, doc="", complete_fn=None):
    define_webjump(name, name+"://%s", doc, complete_fn, True)


def set_default(name):
    """
    Set the default webjump.

    Deprecated: use the *webjump-default* variable instead.

    :param name: the name of the webjump.
    """
    webjump_default.set_value(name)


class WebJumpCompleter(QObject):
    complete = Signal(list)

    def abort(self):
        pass


class WebJumpRequestCompleter(WebJumpCompleter):
    def __init__(self, url, extract_completions_fn):
        WebJumpCompleter.__init__(self)
        req = QNetworkRequest(QUrl(url))
        self.reply = app().network_manager.get(req)
        self.extract_completions_fn = extract_completions_fn
        self.reply.finished.connect(self._on_reply_finished)

    def abort(self):
        self.reply.abort()

    def _on_reply_finished(self):
        if self.reply.error() == self.reply.NoError:
            try:
                completions = self.extract_completions_fn(self.reply.readAll())
            except Exception:
                logging.exception("Error when trying to extract completions from %s"
                                  % self.reply.url().toString())
                completions = []
            self.complete.emit(completions)

        self.reply.deleteLater()
        self.deleteLater()


class WebJumpPrompt(Prompt):
    label = "url/webjump:"
    complete_options = {
        "autocomplete": True,
        "match": Prompt.SimpleMatch
    }
    history = PromptHistory()
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
        self.new_buffer = PromptNewBuffer(self.ctx, self.force_new_buffer)
        self.new_buffer.enable(minibuffer)
        minibuffer.input().textEdited.connect(self._text_edited)
        minibuffer.input().installEventFilter(self)
        self._wc_model = QStringListModel()
        self._wb_model = minibuffer.input().completer_model()
        self._active_webjump = None
        self._completer = None

    def eventFilter(self, obj, event):
        # call _text_edited on backspace release, as this is not reported by
        # the textEdited slot.
        if event.type() == QEvent.KeyRelease:
            if event.key() == Qt.Key_Backspace:
                self._text_edited(self.minibuffer.input().text())
        return Prompt.eventFilter(self, obj, event)

    def _text_edited(self, text):
        # reset the active webjump
        self._active_webjump = None

        # search for a matching webjump
        first_word = text.split(" ")[0].split("://")[0]
        if first_word in [w for w in WEBJUMPS if len(w) < len(text)]:
            model = self._wc_model
            self._active_webjump = WEBJUMPS[first_word]
            # set matching strategy
            self.minibuffer.input().set_match(
                Prompt.SimpleMatch if self._active_webjump.protocol else None)
            self.start_completion(self._active_webjump)
        else:
            # didn't find a webjump, go back to matching
            # webjump/bookmark/history
            self.minibuffer.input().set_match(Prompt.SimpleMatch)
            model = self._wb_model

        if self.minibuffer.input().completer_model() != model:
            self.minibuffer.input().popup().hide()
            self.minibuffer.input().set_completer_model(model)

    def start_completion(self, webjump):
        if self._completer:
            self._completer.complete.disconnect(self._got_completions)
            self._completer.abort()
        text = self.minibuffer.input().text()
        prefix = webjump.name + ("://" if webjump.protocol else " ")
        completer = webjump.complete_fn(text[len(prefix):])
        if completer:
            if isinstance(completer, WebJumpCompleter):
                completer.complete.connect(self._got_completions)
                self._completer = completer
            else:
                self._got_completions(completer)
        else:
            self._got_completions(())

    @Slot(list)
    def _got_completions(self, data):
        self._completer = None
        if self._active_webjump:
            self._wc_model.setStringList(data)
            text = self.minibuffer.input().text()
            prefix = self._active_webjump.name + \
                ("://" if self._active_webjump.protocol else " ")
            self.minibuffer.input().show_completions(text[len(prefix):])

    def close(self):
        Prompt.close(self)
        self.minibuffer.input().removeEventFilter(self)
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
                self.minibuffer.input().setText(
                    self._active_webjump.name + "://" + chosen_text)
            else:
                self.minibuffer.input().setText(
                    self._active_webjump.name + " " + chosen_text)

        # if we just chose a webjump
        # and not WEBJUMPS[chosen_text].protocol:
        elif chosen_text in WEBJUMPS:
            # add a space after the selection
            self.minibuffer.input().setText(
                chosen_text + (" " if not WEBJUMPS[chosen_text].protocol
                               else "://"))


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
    value = prompt.value().strip()

    # split webjumps and protocols between command and argument
    if re.match("^\S+://.*", value):
        args = value.split("://", 1)
    else:
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
        if '%s' not in webjump.url:
            # send the url as is
            return webjump.url
        elif len(args) < 2:
                # send the url without a search string
            return webjump.url % ''

        else:
            # format the url as entered
            if webjump.protocol:
                return value
            else:
                return webjump.url % str(QUrl.toPercentEncoding(args[1]),
                                         "utf-8")

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
def go_to(ctx):
    """
    Prompt to open an url or a webjump.
    """
    url = get_url(ctx.prompt)
    if url:
        ctx.prompt.get_buffer().load(url)


@define_command("go-to-selected-url", prompt=WebJumpPromptCurrentUrl)
def go_to_selected_url(ctx):
    """
    Prompt (defaulting to current selection) to open an url or a webjump.
    """
    go_to(ctx)


class WebJumpPromptNewUrl(WebJumpPrompt):
    force_new_buffer = True


@define_command("go-to-new-buffer", prompt=WebJumpPromptNewUrl)
def go_to_new_buffer(ctx):
    """
    Prompt to open an url or webjump in a new buffer.
    """
    go_to(ctx)


class WebJumpPromptCurrentUrlNewBuffer(WebJumpPromptCurrentUrl):
    force_new_buffer = True


@define_command(
    "go-to-selected-url-new-buffer",
    prompt=WebJumpPromptCurrentUrlNewBuffer
)
def go_to_selected_url_new_buffer(ctx):
    """
    Prompt (defaulting to current selection) to open an url or a webjump.
    """
    go_to(ctx)


@define_command("search-default", prompt=DefaultSearchPrompt)
def search_default(ctx):
    """
    Prompt to open an url with the default webjump.
    """
    go_to(ctx)


class DefaultSearchPromptNewBuffer(DefaultSearchPrompt):
    force_new_buffer = True


@define_command(
    "search-default-new-buffer", prompt=DefaultSearchPromptNewBuffer)
def search_default_new_buffer(ctx):
    """
    Prompt to open an url with the default webjump.
    """
    go_to_new_buffer(ctx)
