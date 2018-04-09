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
import weakref

from PyQt5.QtCore import QObject, QEvent, pyqtSlot as Slot

from .keymaps import KeyPress, global_keymap, CHAR2KEY
from . import hooks
from . import COMMANDS, minibuffer_show_info


class LocalKeymapSetter(QObject):
    def __init__(self):
        QObject.__init__(self)
        self._views = []
        self._minibuffer_inputs = []
        self._current_obj = None

    def register_view(self, view):
        view.installEventFilter(self)
        self._views.append(view)

    def view_destroyed(self, view):
        self._views.remove(view)

    def register_minibuffer_input(self, minibuffer_input):
        minibuffer_input.installEventFilter(self)
        minibuffer_input.destroyed.connect(self._minibuffer_input_destroyed)
        self._minibuffer_inputs.append(minibuffer_input)

    @Slot(QObject)
    def _minibuffer_input_destroyed(self, minibuffer_input):
        # TODO FIXME this fails under integration testing.
        try:
            self._minibuffer_inputs.remove(minibuffer_input)
        except ValueError:
            pass

    def eventFilter(self, obj, event):
        t = event.type()
        if t == QEvent.WindowActivate:
            if obj in self._views:
                # enable the current view's buffer
                set_local_keymap(obj.buffer().active_keymap())
        elif t == QEvent.FocusIn:
            if obj in self._minibuffer_inputs:
                # when the minibuffer input is shown, enable it
                set_local_keymap(obj.keymap())
        elif t == QEvent.FocusOut:
            if obj in self._minibuffer_inputs:
                # the focus is lost when the popup is active
                if not obj.popup().isVisible():
                    # when the minibuffer input is hidden, enable its view's
                    # buffer
                    buff = obj.parent().parent().current_web_view().buffer()
                    set_local_keymap(buff.active_keymap())
        return QObject.eventFilter(self, obj, event)

    def web_content_edit_focus_changed(self, buff, enabled):
        if enabled:
            buff.set_keymap_mode(buff.KEYMAP_MODE_CONTENT_EDIT)
            set_local_keymap(buff.active_keymap())
        else:
            buff.set_keymap_mode(buff.KEYMAP_MODE_NORMAL)
            window = buff.main_window()
            if window and not window.minibuffer().input().hasFocus():
                set_local_keymap(buff.active_keymap())

    def caret_browsing_changed(self, buff, enabled):
        if enabled:
            buff.set_keymap_mode(buff.KEYMAP_MODE_CARET_BROWSING)
            set_local_keymap(buff.active_keymap())
        else:
            buff.set_keymap_mode(buff.KEYMAP_MODE_NORMAL)
            window = buff.main_window()
            if window and not window.minibuffer().input().hasFocus():
                set_local_keymap(buff.active_keymap())


LOCAL_KEYMAP_SETTER = LocalKeymapSetter()
hooks.webview_created.add(LOCAL_KEYMAP_SETTER.register_view)
hooks.webview_closed.add(LOCAL_KEYMAP_SETTER.view_destroyed)


class KeyEater(object):
    """
    Handle Qt keypresses events.
    """
    def __init__(self):
        self._keypresses = []
        self._commands = COMMANDS
        self._local_key_map = None
        self.current_obj = None
        self._use_global_keymap = True
        self.universal_key = KeyPress.from_str("C-u")
        self._prefix_arg = None
        self._reset_prefix_arg = False
        self._allowed_universal_keys = {}
        for i in "1234567890":
            self._allowed_universal_keys[CHAR2KEY[i]] \
                = lambda: self._num_update_prefix_arg(i)

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
        self.current_obj = weakref.ref(obj)
        if self._handle_keypress(key):
            return True
        return False

    def active_keymaps(self):
        if self._local_key_map:
            yield self._local_key_map
        if self._use_global_keymap:
            yield global_keymap()

    def _add_keypress(self, keypress):
        self._keypresses.append(keypress)
        minibuffer_show_info(
            " ".join((str(k) for k in self._keypresses))
        )
        logging.debug("keychord: %s" % self._keypresses)

    def _num_update_prefix_arg(self, numstr):
        if not isinstance(self._prefix_arg, int):
            self._prefix_arg = int(numstr)
        else:
            self._prefix_arg = int(str(self._prefix_arg) + numstr)

    def _handle_keypress(self, keypress):
        if self._reset_prefix_arg:
            self._reset_prefix_arg = False
            self._prefix_arg = None
        if keypress == self.universal_key:
            if isinstance(self._prefix_arg, tuple):
                self._prefix_arg = (self._prefix_arg[0] * 4,)
            else:
                self._prefix_arg = (4,)
                self._keypresses = []
            self._add_keypress(keypress)
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

        incomplete_keychord = False
        command_called = False
        self._add_keypress(keypress)

        for keymap in self.active_keymaps():
            result = keymap.lookup(self._keypresses)

            if result is None:
                pass
            elif not result.complete:
                incomplete_keychord = True
            else:
                try:
                    self._call_command(result.command)
                except Exception:
                    logging.exception("Error calling command:")
                command_called = True

        if command_called or not incomplete_keychord:
            self._keypresses = []

        if command_called:
            self._reset_prefix_arg = True

        return command_called or incomplete_keychord

    def _call_command(self, command):
        if isinstance(command, str):
            try:
                command = self._commands[command]
            except KeyError:
                raise KeyError("No such command: %s" % command)

        command()


KEY_EATER = KeyEater()


def send_key_event(keypress):
    obj = KEY_EATER.current_obj
    if obj:
        obj = obj()
        if obj:
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
