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
from ..minibuffer.keymap import KEYMAP as MINIBUF_KEYMAP
from .. keymaps import Keymap
from ..commands import define_command
from .. import current_buffer
from ..application import app
from .prompt_helper import PromptNewBuffer
from .. import variables
from .. import version


WebJump = namedtuple(
    "WebJump", ("name", "url", "doc", "allow_args", "complete_fn", "protocol"))
WEBJUMPS = {}


webjump_default = variables.define_variable(
    "webjump-default",
    "The default webjump",
    "",
    type=variables.String(choices=WEBJUMPS),
)


def define_webjump(name, url, doc="", complete_fn=None, protocol=False):
    """
    Define a webjump.

    A webjump is a quick way to access a URL, optionally with a
    variable section (for example a URL for a Google search). A
    function may be given to provide auto-completion.

    :param name: the name of the webjump.
    :param url: the url of the webjump. If the url contains "%s", it is
        assumed that it has a variable part.
    :param doc: associated documentation for the webjump.
    :param complete_fn: a function that should create a suitable
        :class:`WebJumpCompleter` to provide auto-completion, or None if there
        is no completion support for this webjump.
    :param protocol: True if the webjump should be treated as the protocol
                     part of a URI (eg: file://)

    """
    allow_args = "%s" in url
    WEBJUMPS[name.strip()] = WebJump(
        name.strip(), url,
        doc,
        allow_args,
        complete_fn or empty_completer,
        protocol
    )


def define_protocol(name, doc="", complete_fn=None):
    define_webjump(name, name + "://%s", doc, complete_fn, True)


def set_default(name):
    """
    Set the default webjump.

    Deprecated: use the *webjump-default* variable instead.

    :param name: the name of the webjump.
    """
    webjump_default.set_value(name)


class WebJumpCompleter(object if version.building_doc else QObject):

    """
    Provides auto-completion in webjumps.

    An instance is created automatically when required, and lives while the
    webjump is active. When a key is entered in the minibuffer input, the
    method :meth:`complete` is called with the current text, asking for
    completion.

    The signal `completed` must then be emitted with the list of possible
    completions.

    Note that there is no underlying thread in the completion framework.
    """
    completed = Signal(list)

    def complete(self, text):
        """Must be implemented by subclasses."""
        raise NotImplementedError

    def abort(self):
        """
        Called when the completion request should be aborted.

        Subclasses should implement this if possible.
        """
        pass


class SyncWebJumpCompleter(WebJumpCompleter):

    """
    A simple completer that provides completion given a function.

    This completer will block the UI: use it with care.

    :param complete_fn: a function that takes the current string, and must
        return the possible completions as a list of strings.
    """

    def __init__(self, complete_fn):
        WebJumpCompleter.__init__(self)
        self.complete_fn = complete_fn

    def complete(self, text):
        self.completed.emit(self.complete_fn(text))


def empty_completer():
    return SyncWebJumpCompleter(lambda _: [])


class WebJumpRequestCompleter(WebJumpCompleter):

    """
    A completer that executes a Web request to provide completion.

    This completer will not block the UI.

    :param url_fn: a function that takes the text to complete, and returns a
        URL that will provide completion. The returned value can be none
        if no URL is suitable for the given text.
    :param extract_completions_fn: a function that takes the bytes of the
        request reply, and must convert them to the completions
        (a string list).
    """

    def __init__(self, url_fn, extract_completions_fn):
        WebJumpCompleter.__init__(self)
        self.url_fn = url_fn
        self.extract_completions_fn = extract_completions_fn
        self.reply = None

    def complete(self, text):
        url = self.url_fn(text)
        if not url:
            self.completed.emit([])
            return
        elif not isinstance(url, QUrl):
            url = QUrl(url)
        req = QNetworkRequest(QUrl(url))
        self.reply = app().network_manager.get(req)
        self.reply.finished.connect(self._on_reply_finished)

    def abort(self):
        if self.reply:
            self.reply.abort()

    def _on_reply_finished(self):
        if self.reply.error() == self.reply.NoError:
            try:
                completions = self.extract_completions_fn(self.reply.readAll())
            except Exception:
                logging.exception(
                    "Error when trying to extract completions from %s"
                    % self.reply.url().toString()
                )
                completions = []
            self.completed.emit(completions)

        self.reply.deleteLater()
        self.reply = None


WEBJUMP_PROMPT_KEYMAP = Keymap("webjump-minibuffer", parent=MINIBUF_KEYMAP)


@WEBJUMP_PROMPT_KEYMAP.define_key("Tab")
def wb_complete(ctx):
    input = ctx.minibuffer.input()
    if not input.popup().isVisible():
        input.show_completions()
    else:
        input.complete()
        ctx.minibuffer.prompt()._text_edited(input.text())


class WebJumpPrompt(Prompt):
    label = "url/webjump:"
    complete_options = {
        "match": Prompt.SimpleMatch
    }
    history = PromptHistory()
    force_new_buffer = False
    keymap = WEBJUMP_PROMPT_KEYMAP
    select_current_url = True

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
        self._popup_sel_model = None
        if self.select_current_url:
            url = current_buffer().url().toString()
            input = minibuffer.input()
            input.setText(url)
            input.setSelection(0, len(url))

    def eventFilter(self, obj, event):
        # call _text_edited on backspace release, as this is not reported by
        # the textEdited slot.
        if event.type() == QEvent.KeyRelease:
            if event.key() == Qt.Key_Backspace:
                self._text_edited(self.minibuffer.input().text())
        return Prompt.eventFilter(self, obj, event)

    def _set_active_webjump(self, wj):
        if self._active_webjump == wj:
            return

        if self._active_webjump:
            if self._completer:
                self._completer.completed.disconnect(self._got_completions)
                self._completer.abort()
                self._completer.deleteLater()
                self._completer = None

        m_input = self.minibuffer.input()
        if wj:
            self._completer = wj.complete_fn()
            self._completer.completed.connect(self._got_completions)
            # set matching strategy
            m_input.set_match(None)
            model = self._wc_model
        else:
            m_input.set_match(Prompt.SimpleMatch)
            model = self._wb_model

        self._active_webjump = wj
        if m_input.completer_model() != model:
            m_input.popup().hide()
            m_input.set_completer_model(model)
            if self._popup_sel_model:
                self._popup_sel_model.selectionChanged.disconnect(
                    self._popup_selection_changed
                )
                self._popup_sel_model = None
            if wj:
                m_input.popup().selectionModel()\
                               .selectionChanged.connect(
                                   self._popup_selection_changed
                )

    def _popup_selection_changed(self, _sel, _desel):
        # try to abort any completion if the user select something in
        # the popup
        if self._completer:
            self._completer.abort()

    def _text_edited(self, text):
        # search for a matching webjump
        first_word = text.split(" ")[0].split("://")[0]
        if first_word in [w for w in WEBJUMPS if len(w) < len(text)]:
            self._set_active_webjump(WEBJUMPS[first_word])
            self.start_completion(self._active_webjump)
        else:
            # didn't find a webjump, go back to matching
            # webjump/bookmark/history
            self._set_active_webjump(None)

    def start_completion(self, webjump):
        text = self.minibuffer.input().text()
        prefix = webjump.name + ("://" if webjump.protocol else " ")
        self._completer.abort()
        self._completer.complete(text[len(prefix):])

    @Slot(list)
    def _got_completions(self, data):
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


class WebJumpPromptAlternateUrl(WebJumpPrompt):

    def enable(self, minibuffer):
        WebJumpPrompt.enable(self, minibuffer)
        minibuffer.input().deselect()


class DefaultSearchPrompt(WebJumpPrompt):
    select_current_url = False

    def enable(self, minibuffer):
        WebJumpPrompt.enable(self, minibuffer)
        wj = WEBJUMPS.get(webjump_default.value)
        if wj:
            minibuffer.input().setText(
                wj.name + ("://" if wj.protocol else " ")
            )


def get_url(prompt):
    value = prompt.value().strip()

    # split webjumps and protocols between command and argument
    if re.match(r"^\S+://.*", value):
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
        if not webjump.allow_args:
            # send the url as is
            return webjump.url
        elif len(args) < 2:
                # send the url without a search string
            return webjump.url.replace("%s", "")

        else:
            # format the url as entered
            if webjump.protocol:
                return value
            else:
                return webjump.url.replace(
                    "%s",
                    str(QUrl.toPercentEncoding(args[1]), "utf-8")
                )

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
    Prompt to open a URL or a webjump.
    """
    url = get_url(ctx.prompt)
    if url:
        ctx.prompt.get_buffer().load(url)


@define_command("go-to-alternate-url", prompt=WebJumpPromptAlternateUrl)
def go_to_selected_url(ctx):
    """
    Prompt to open an alternative URL from the current one.
    """
    go_to(ctx)


class WebJumpPromptNewUrl(WebJumpPrompt):
    force_new_buffer = True


@define_command("go-to-new-buffer", prompt=WebJumpPromptNewUrl)
def go_to_new_buffer(ctx):
    """
    Prompt to open a URL or webjump in a new buffer.
    """
    go_to(ctx)


class WebJumpPromptAlternateUrlNewBuffer(WebJumpPromptAlternateUrl):
    force_new_buffer = True


@define_command(
    "go-to-alternate-url-new-buffer",
    prompt=WebJumpPromptAlternateUrlNewBuffer
)
def go_to_selected_url_new_buffer(ctx):
    """
    Prompt to open an alternative URL from the current one in a new buffer.
    """
    go_to(ctx)


@define_command("search-default", prompt=DefaultSearchPrompt)
def search_default(ctx):
    """
    Prompt to open a URL with the default webjump.
    """
    go_to(ctx)


class DefaultSearchPromptNewBuffer(DefaultSearchPrompt):
    force_new_buffer = True


@define_command(
    "search-default-new-buffer", prompt=DefaultSearchPromptNewBuffer)
def search_default_new_buffer(ctx):
    """
    Prompt to open a URL with the default webjump.
    """
    go_to_new_buffer(ctx)
