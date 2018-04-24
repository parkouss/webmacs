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

from PyQt5.QtCore import QObject, QEvent

from .keymaps import KeyPress, global_keymap, CHAR2KEY
from . import hooks
from . import COMMANDS, minibuffer_show_info, CommandContext
from .mode import Mode


class LocalKeymapSetter(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.enabled_minibuffer = False

    def eventFilter(self, obj, evt):
        # event filter on the global app is required to avoid click on webviews
        if self.enabled_minibuffer and evt.type() in (
                QEvent.MouseButtonPress,
                QEvent.MouseButtonDblClick,
                QEvent.MouseButtonRelease,
                QEvent.MouseMove):
            return True
        return False

    def set_enabled_minibuffer(self, enabled):
        self.enabled_minibuffer = enabled

    def minibuffer_input_focus_changed(self, mb, enabled):
        if enabled:
            set_local_keymap(mb.keymap())
        else:
            if not mb.popup().isVisible():
                # when the minibuffer input is hidden, enable its view's
                # buffer
                buff = mb.parent().parent().current_web_view().buffer()
                set_local_keymap(buff.active_keymap())

    def view_focus_changed(self, view, enabled):
        if enabled:
            set_local_keymap(view.buffer().active_keymap())

    def web_content_edit_focus_changed(self, buff, enabled):
        if enabled:
            buff.set_keymap_mode(Mode.KEYMAP_CONTENT_EDIT)
            set_local_keymap(buff.active_keymap())
        else:
            buff.set_keymap_mode(Mode.KEYMAP_NORMAL)
            if not self.enabled_minibuffer:
                set_local_keymap(buff.active_keymap())

    def caret_browsing_changed(self, buff, enabled):
        if enabled:
            buff.set_keymap_mode(Mode.KEYMAP_CARET_BROWSING)
            set_local_keymap(buff.active_keymap())
        else:
            buff.set_keymap_mode(Mode.KEYMAP_NORMAL)
            if not self.enabled_minibuffer:
                set_local_keymap(buff.active_keymap())

    def buffer_mode_changed(self, buffer, old_mode):
        # check that the previous keymap was the one corresponding to the mode
        old_km = old_mode.keymap_for_mode(buffer.keymap_mode)
        if old_km == local_keymap():
            set_local_keymap(buffer.active_keymap())

    def buffer_opened_in_view(self, buffer):
        if not self.enabled_minibuffer:
            set_local_keymap(buffer.active_keymap())


LOCAL_KEYMAP_SETTER = LocalKeymapSetter()


class KeyEater(object):
    """
    Handle Qt keypresses events.
    """
    def __init__(self):
        self.set_call_handler(CallHandler())
        self._keypresses = []
        self._local_key_map = None
        self._use_global_keymap = True
        self.universal_key = KeyPress.from_str("C-u")
        self._prefix_arg = None
        self._reset_prefix_arg = False
        self._allowed_universal_keys = {}
        for i in "1234567890":
            self._allowed_universal_keys[CHAR2KEY[i]] \
                = lambda: self._num_update_prefix_arg(i)

    def set_call_handler(self, call_handler):
        self.call_handler = call_handler

    def set_local_key_map(self, keymap):
        if keymap != self._local_key_map:
            self._local_key_map = keymap
            hooks.local_mode_changed(keymap)
            logging.debug("local keymap activated: %s", keymap)

    def local_key_map(self):
        return self._local_key_map

    def set_global_keymap_enabled(self, enable):
        self._use_global_keymap = enable

    def event_filter(self, obj, event):
        key = KeyPress.from_qevent(event)
        if key is None:
            return False
        if self._handle_keypress(obj, key):
            return True
        return False

    def active_keymaps(self):
        if self._local_key_map:
            yield self._local_key_map
        if self._use_global_keymap:
            yield global_keymap()

    def _add_keypress(self, keypress):
        self._keypresses.append(keypress)
        logging.debug("keychord: %s" % self._keypresses)

    def _num_update_prefix_arg(self, numstr):
        if not isinstance(self._prefix_arg, int):
            self._prefix_arg = int(numstr)
        else:
            self._prefix_arg = int(str(self._prefix_arg) + numstr)

    def _show_info_kbd(self, extra=""):
        minibuffer_show_info(
            " ".join((str(k) for k in self._keypresses)) + extra
        )

    def _handle_keypress(self, sender, keypress):
        if self._reset_prefix_arg:
            self._reset_prefix_arg = False
            self._prefix_arg = None
        if keypress == self.universal_key:
            if isinstance(self._prefix_arg, tuple):
                self._prefix_arg = (self._prefix_arg[0] * 4,)
            else:
                self._prefix_arg = (4,)
                self._keypresses = []
            return True
        if self._prefix_arg is not None:
            try:
                func = self._allowed_universal_keys[keypress.key]
            except KeyError:
                pass
            else:
                if not keypress.has_any_modifier():
                    func()
                    self._add_keypress(keypress)
                    return True

        result = None
        self._add_keypress(keypress)

        for keymap in self.active_keymaps():
            result = keymap.lookup(self._keypresses)
            if result:
                break

        if not result:
            if len(self._keypresses) > 1:
                self._show_info_kbd(" is undefined.")
            self._keypresses = []
            self.call_handler.no_call(sender, keymap, keypress)
            return False

        if result.complete:
            self._show_info_kbd()
            self._keypresses = []
            self._reset_prefix_arg = True
            try:
                self.call_handler.call(sender, keymap, keypress,
                                       result.command)
            except Exception:
                logging.exception("Error calling command:")
        else:
            self._show_info_kbd(" -")
            self.call_handler.partial_call(sender, keymap, keypress)

        return result is not None


class CallHandler(object):
    def __init__(self):
        self._commands = COMMANDS

    def call(self, sender, keymap, keypress, command):
        if isinstance(command, str):
            try:
                command = self._commands[command]
            except KeyError:
                raise KeyError("No such command: %s" % command)

        command(CommandContext(sender, keypress))

    def no_call(self, sender, keymap, keypress):
        pass

    def partial_call(self, sender, keymap, keypress):
        pass


KEY_EATER = KeyEater()


def send_key_event(obj, keypress):
    from .application import app as _app
    app = _app()
    app.postEvent(obj, keypress.to_qevent(QEvent.KeyPress))
    app.postEvent(obj, keypress.to_qevent(QEvent.KeyRelease))


def local_keymap():
    return KEY_EATER.local_key_map()


def set_local_keymap(keymap):
    KEY_EATER.set_local_key_map(keymap)


def set_global_keymap_enabled(enable):
    KEY_EATER.set_global_keymap_enabled(enable)


def current_prefix_arg():
    return KEY_EATER._prefix_arg
