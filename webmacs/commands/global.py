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

import itertools
import os
from PyQt6.QtCore import QStringListModel, QModelIndex

from . import define_command, COMMANDS, register_prompt_opener_commands
from ..minibuffer import Prompt
from ..minibuffer.prompt import PromptTableModel, PromptHistory
from ..application import app
from ..webbuffer import create_buffer
from ..keymaps import KeyPress, VISITEDLINKS_KEYMAP, BOOKMARKS_KEYMAP, KEYMAPS
from ..keyboardhandler import send_key_event, local_keymap, KEY_EATER, \
    CallHandler
from .. import BUFFERS, windows, variables
from ..mode import MODES
from ..window import Window
from ..session import session_clean, session_load
from ..ipc import IpcServer
from ..url_opener import url_open


class CommandsListPrompt(Prompt):
    label = "M-x: "
    complete_options = {
        "match": Prompt.FuzzyMatch,
        "complete-empty": True,
    }
    history = PromptHistory()

    def completer_model(self):
        model = QStringListModel(self)
        model.setStringList(sorted(k for k, v in COMMANDS.items()
                                   if v.visible))
        return model


@define_command("quit")
def quit(ctx):
    """
    Quit the application.
    """
    app().quit()


@define_command("M-x", visible=False)
def commands(ctx):
    """
    Prompt for a command name to execute.
    """
    prompt = CommandsListPrompt(ctx)
    value = ctx.minibuffer.do_prompt(prompt)
    try:
        COMMANDS[value](ctx)
    except KeyError:
        pass


@define_command("toggle-fullscreen")
def toggle_fullscreen(ctx):
    """
    Toggle fullscreen state of the current window.
    """
    win = ctx.window
    if not win:
        return
    if win.isFullScreen():
        win.showNormal()
    else:
        win.showFullScreen()


@define_command("toggle-maximized")
def toggle_maximised(ctx):
    """
    Toggle maximised state of the current window.
    """
    win = ctx.window
    if not win:
        return
    if win.isMaximized():
        win.showNormal()
    else:
        win.showMaximized()


def _get_or_create_buffer(win):
    visible_buffers = []
    for awin in windows():
        for view in awin.webviews():
            visible_buffers.append(view.buffer())
    current_buffer = win.current_webview().buffer()
    buffers = [b for b in BUFFERS
               if b not in visible_buffers
               or b == current_buffer]

    # if there is at least one buffer not visible, use the one just
    # after the current one in the list
    if len(buffers) > 1:
        ibuffers = itertools.cycle(buffers)
        while True:
            buff = next(ibuffers)
            if buff == current_buffer:
                return next(ibuffers)

    # else create a new buffer, reusing the current buffer's url
    return create_buffer(url=current_buffer.url())


@define_command("split-view-right")
def split_window_right(ctx):
    """
    Create a new view on the right of the current one.
    """
    win = ctx.window
    view = win.create_webview_on_right()
    view.setBuffer(_get_or_create_buffer(win))
    view.set_current()


@define_command("split-view-bottom")
def split_window_bottom(ctx):
    """
    Create a new view below the current one.
    """
    win = ctx.window
    view = win.create_webview_on_bottom()
    view.setBuffer(_get_or_create_buffer(win))
    view.set_current()


@define_command("make-window")
def create_window(ctx):
    """
    Create a new window and focus it.
    """
    win = Window()
    home_page = variables.get("home-page")
    win.current_webview().setBuffer(
        create_buffer(home_page)
        if home_page and variables.get("home-page-in-new-window")
        else _get_or_create_buffer(ctx.window)
    )
    win.show()
    win.activateWindow()


@define_command("other-window")
def other_window(ctx):
    """
    Switch to the next window.
    """
    if len(windows()) <= 1:
        return False
    iterwindows = itertools.cycle(windows())
    while True:
        win = next(iterwindows)
        if win == ctx.window:
            next(iterwindows).activateWindow()
            return True


@define_command("close-window")
def close_window(ctx):
    """
    Close the current window, unless there is only one left.
    """
    # first activate the next view
    if other_window(ctx):
        ctx.window.close()


@define_command("close-other-windows")
def close_other_windows(ctx):
    """
    Close all windows except the current one.
    """
    for win in windows():
        if win != ctx.window:
            win.close()


@define_command("other-view")
def other_view(ctx):
    """
    Focus on the next view.
    """
    win = ctx.window
    win.other_view()


@define_command("close-view")
def close_view(ctx):
    """
    Close the current view.
    """
    window = ctx.window
    window.close_view(window.current_webview())


@define_command("maximise-view")
def maximise_view(ctx):
    """
    Close all the views in the current window except the current one.
    """
    ctx.window.close_other_views()


@define_command("toggle-ad-block")
def toggle_ad_block(ctx):
    """
    Toggle ad-blocking on or off.
    """
    from .webbuffer import reload_buffer_no_cache

    app().url_interceptor().toggle_use_adblock()
    reload_buffer_no_cache(ctx)


@define_command("toggle-toolbar")
def toggle_toolbar(ctx):
    """
    Toggle the main window toolbar on or off.
    """
    ctx.window.toggle_toolbar()


class VisitedLinksModel(PromptTableModel):

    def __init__(self, parent):
        visitedlinks = app().visitedlinks()
        PromptTableModel.__init__(self, visitedlinks.visited_urls())
        self.visitedlinks = visitedlinks

    def remove_history_entry(self, index):
        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        self.visitedlinks.remove(self._data.pop(index.row())[0])
        self.endRemoveRows()


class VisitedLinksPrompt(Prompt):
    label = "Find url from visited links:"
    complete_options = {
        "match": Prompt.FuzzyMatch,
        "complete-empty": True,
    }
    keymap = VISITEDLINKS_KEYMAP
    value_return_index_data = True

    def completer_model(self):
        return VisitedLinksModel(self)


@define_command("visited-links-delete-highlighted")
def visited_links_remove_entry(ctx):
    """
    Deletes from the database the currently highlighted visited link.
    """
    pinput = ctx.minibuffer.input()

    selection = pinput.popup().selectionModel().currentIndex()
    if not selection.isValid():
        return

    selection = selection.model().mapToSource(selection)
    pinput.completer_model().remove_history_entry(selection)


register_prompt_opener_commands(
    "visited-links-history",
    VisitedLinksPrompt,
    "Prompt to open a link previously visited",
)


class BookmarksModel(VisitedLinksModel):

    def __init__(self, parent):
        bookmarks = app().bookmarks()
        PromptTableModel.__init__(self, bookmarks.list())
        # this makes the remove_history_entry method works
        self.visitedlinks = bookmarks


@define_command("bookmarks-delete-highlighted")
def bookmarks_remove_entry(ctx):
    """
    Deletes from the database the currently highlighted bookmark.
    """
    # removing a bookmark is like removing a visited link
    visited_links_remove_entry(ctx)


class BookmarksPrompt(VisitedLinksPrompt):
    label = "Open bookmark:"
    keymap = BOOKMARKS_KEYMAP
    history = PromptHistory()

    def completer_model(self):
        return BookmarksModel(self)


register_prompt_opener_commands(
    "bookmark-open",
    BookmarksPrompt,
    "Prompt to open a bookmark",
)


class BookmarkAddPrompt(Prompt):
    label = "Create a bookmark for: "

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        url = self.ctx.buffer.url().toString()
        input = minibuffer.input()
        input.setText(url)
        input.setSelection(0, len(url))


class BookmarkNamePrompt(Prompt):
    label = "bookmark's name: "

    def enable(self, minibuffer):
        Prompt.enable(self, minibuffer)
        name = self.ctx.buffer.title()
        input = minibuffer.input()
        input.setText(name)
        input.setSelection(0, len(name))


@define_command("bookmark-add")
def bookmark_add(ctx):
    """
    Create or rename a bookmark for the current url.
    """
    prompt = BookmarkAddPrompt(ctx)
    url = ctx.minibuffer.do_prompt(prompt)
    if not url:
        return

    otherprompt = BookmarkNamePrompt(ctx)
    name = ctx.minibuffer.do_prompt(otherprompt)

    if name:
        app().bookmarks().set(url, name)
        ctx.minibuffer.show_info("Bookmark {} created.".format(name))


class ModesPrompt(Prompt):
    label = "switch to mode:"
    complete_options = {
        "match": Prompt.FuzzyMatch,
        "complete-empty": True,
    }
    value_return_index_data = True

    def completer_model(self):
        return PromptTableModel([
            (name, MODES[name].description) for name in sorted(MODES)
        ])


@define_command("buffer-set-mode")
def buffer_set_mode(ctx):
    """
    Change the mode of the current buffer.
    """
    prompt = ModesPrompt(ctx)
    mode = ctx.minibuffer.do_prompt(prompt)
    if mode:
        ctx.buffer.set_mode(mode)


@define_command("send-key-down")
def send_down(ctx):
    """Send a key down event."""
    send_key_event(KeyPress.from_str("Down"))


@define_command("send-key-up")
def send_up(ctx):
    """Send a key up event."""
    send_key_event(KeyPress.from_str("Up"))


@define_command("send-key-right")
def send_right(ctx):
    """Send a key right event."""
    send_key_event(KeyPress.from_str("Right"))


@define_command("send-key-left")
def send_left(ctx):
    """Send a key left event."""
    send_key_event(KeyPress.from_str("Left"))


@define_command("describe-bindings")
def describe_bindings(ctx):
    """
    Display current bindings in the current buffer or in a new buffer.
    """
    url_open(ctx, "webmacs://bindings", new_buffer=ctx.current_prefix_arg == (4,))


@define_command("describe-commands")
def describe_commands(ctx):
    """
    Display commands in the current buffer or in a new buffer.
    """
    url_open(ctx, "webmacs://commands", new_buffer=ctx.current_prefix_arg == (4,))


@define_command("describe-variables")
def describe_variables(ctx):
    """
    Display variables in the current buffer or in a new buffer.
    """
    url_open(ctx, "webmacs://variables", new_buffer=ctx.current_prefix_arg == (4,))


@define_command("downloads")
def downloads(ctx):
    """
    Display information about the current downloads.
    """
    url_open(ctx, "webmacs://downloads", new_buffer=ctx.current_prefix_arg == (4,))


@define_command("version")
def version(ctx):
    """
    Display version information.
    """
    url_open(ctx, "webmacs://version", new_buffer=ctx.current_prefix_arg == (4,))


class VariableListPrompt(Prompt):
    label = "describe variable: "
    complete_options = {
        "match": Prompt.FuzzyMatch,
        "complete-empty": True,
    }
    history = PromptHistory()

    def completer_model(self):
        model = QStringListModel(self)
        model.setStringList(sorted(variables.VARIABLES))
        return model


@define_command("describe-variable")
def describe_variable(ctx):
    """
    Prompt for a variable name to describe.
    """
    variable = ctx.minibuffer.do_prompt(VariableListPrompt(ctx))
    if variable in variables.VARIABLES:
        buffer = create_buffer("webmacs://variable/%s" % variable)
        ctx.view.setBuffer(buffer)


class DescribeCommandsListPrompt(CommandsListPrompt):
    label = "describe command: "
    history = PromptHistory()


@define_command("describe-command")
def describe_command(ctx):
    """
    Prompt for a command name to describe.
    """
    command = ctx.minibuffer.do_prompt(DescribeCommandsListPrompt(ctx))
    if command in COMMANDS:
        url_open(ctx, "webmacs://command/%s" % command)


class ReportCallHandler(CallHandler):

    def __init__(self, prompt):
        CallHandler.__init__(self)
        self.prompt = prompt
        self.key_presses = []

    def keys_as_text(self):
        return " - ".join(str(k) for k in self.key_presses)

    def no_call(self, sender, keymap, keypress):
        self.key_presses.append(keypress)
        self.prompt.close()
        self.prompt.minibuffer.show_info("No such key: %s"
                                         % self.keys_as_text())

    def partial_call(self, sender, keymap, keypress):
        self.key_presses.append(keypress)
        self.prompt.minibuffer.input().setText("%s -"
                                               % self.keys_as_text())

    def call(self, ctx, keymap, keypress, command):
        self.key_presses.append(keypress)
        if not isinstance(command, str):
            command = "{}:{}".format(command.__module__,
                                     command.__name__)
        self.prompt.called_with = {
            "command": command,
            "key": self.keys_as_text(),
            "keymap": keymap.name or "unknown",
        }
        self.prompt.finished.emit()
        self.prompt.close()


class BindingPrompt(Prompt):
    label = "describe key: "
    called_with = None

    def enable(self, minibuffer):
        self.keymap = local_keymap()
        Prompt.enable(self, minibuffer)
        self.orig_handler = KEY_EATER.call_handler
        KEY_EATER.set_call_handler(ReportCallHandler(self))

    def close(self):
        KEY_EATER.set_call_handler(self.orig_handler)
        Prompt.close(self)

    def value(self):
        return self.called_with


@define_command("describe-key")
def describe_binding(ctx):
    """
    Retrieve the command called by the given binding.
    """
    called_with = ctx.minibuffer.do_prompt(BindingPrompt(ctx))
    if called_with:
        url = "webmacs://key/{key}?command={command}&keymap={keymap}".format(
            **called_with
        )
        url_open(ctx, url, new_buffer=True)


@define_command("describe-key-briefly")
def describe_binding_briefly(ctx):
    """
    Display in the minibuffer the command name called by the given binding.
    """
    called_with = ctx.minibuffer.do_prompt(BindingPrompt(ctx))
    if called_with:
        ctx.minibuffer.show_info(
            "{key} runs the command {command} (keymap: {keymap})".format(
                **called_with
            )
        )


class WhereIsCommandsListPrompt(CommandsListPrompt):
    label = "Where is command: "
    history = PromptHistory()


@define_command("where-is")
def where_is(ctx):
    """
    Print short notice of where a command is bound
    """
    command = ctx.minibuffer.do_prompt(WhereIsCommandsListPrompt(ctx))
    if not command:
        return
    bindings_str = ", ".join("{} (keymap: {})".format(k, kmapname)
                             for kmapname, kmap in KEYMAPS.items()
                             for k, v in kmap.all_bindings() if v == command)
    if bindings_str:
        ctx.minibuffer.show_info("{} is on: {}".format(command, bindings_str))
    else:
        ctx.minibuffer.show_info("{} is not on any key".format(command))


@define_command("restore-session")
def restore_session(ctx):
    """
    Restore windows and buffers from the previous sessions.
    """
    session_file = app().profile.session_file
    if not os.path.exists(session_file):
        ctx.minibuffer.show_info("Error: No session file found.")

    session_clean()
    try:
        session_load(session_file)
    except Exception:
        w = Window()
        w.current_webview().setBuffer("about:blank")
        w.show()


class InstancesListPrompt(Prompt):
    label = "webmacs instances: "
    complete_options = {
        "match": Prompt.FuzzyMatch,
        "complete-empty": True,
    }
    history = PromptHistory()
    exclude_self_instance = True

    def __init__(self, ctx):
        super().__init__(ctx)
        instances = IpcServer.list_all_instances(check=False)
        if self.exclude_self_instance:
            current = app().instance_name
            instances = [i for i in instances if i != current]
        self.instances = instances

    def completer_model(self):
        model = QStringListModel(self)
        model.setStringList(self.instances)
        return model


@define_command("raise-instance")
def raise_instance(ctx):
    """
    Raise the current window of the selected instance.
    """
    prompt = InstancesListPrompt(ctx)
    if not prompt.instances:
        ctx.minibuffer.show_info("There is only one instance running: %s"
                                 % app().instance_name)
    else:
        value = ctx.minibuffer.do_prompt(prompt)
        if value:
            IpcServer.instance_send(value, {})


@define_command("current-instance")
def current_instance(ctx):
    """
    Show the current instance name.
    """
    ctx.minibuffer.show_info("Current instance name: %s" % app().instance_name)
