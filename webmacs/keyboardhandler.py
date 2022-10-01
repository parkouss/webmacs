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

from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtGui import QWindow

from .keymaps import KeyPress, GLOBAL_KEYMAP, CHAR2KEY
from . import hooks
from . import COMMANDS, minibuffer_show_info, current_minibuffer, \
    current_window
from .mode import Mode


class CommandContext(object):
    def __init__(self):
        self.window = current_window()
        self.view = self.window.current_webview() if self.window else None
        self.buffer = self.view.buffer() if self.view else None
        self.current_prefix_arg = KEY_EATER._prefix_arg
        self.prompt = None

    @property
    def minibuffer(self):
        win = self.window
        if win:
            return win.minibuffer()


class LocalKeymapSetter(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.enabled_minibuffer = False

    def eventFilter(self, obj, evt):
        # event filter on the global app is required to avoid click on webviews
        t = evt.type()

        if t == QEvent.Type.KeyPress and isinstance(obj, QWindow):
            return KEY_EATER.event_filter(obj, evt)
        elif t == QEvent.Type.ShortcutOverride:
            # disable automatic shortcuts in browser, like C-a
            return True
        elif self.enabled_minibuffer and t in (
                QEvent.Type.MouseButtonPress,
                QEvent.Type.MouseButtonDblClick,
                QEvent.Type.MouseButtonRelease,
                QEvent.Type.MouseMove):
            minibuff = current_minibuffer()
            if minibuff:
                # allow clicks in minibuffer inputs and popup only
                # note: QWidget.underMouse does not works here.
                input = minibuff.input()
                if input.rect().contains(input.mapFromGlobal(evt.globalPosition().toPoint())):
                    return False
                else:
                    popup = input.popup()
                    if popup.isVisible() and popup.rect().contains(
                            popup.mapFromGlobal(evt.globalPosition().toPoint())):
                        return False
                # else flash the minibuffer on click.
                if evt.type() in (QEvent.Type.MouseButtonPress,
                                  QEvent.Type.MouseButtonDblClick) \
                                  and minibuff.prompt():  # noqa: 125
                    minibuff.prompt().flash()
            return True
        return False

    def minibuffer_input_focus_changed(self, mbi, enabled):
        self.enabled_minibuffer = enabled
        if enabled:
            set_local_keymap(mbi.keymap())
        else:
            if not mbi.isVisible():
                # when the minibuffer input is hidden, enable its view's
                # buffer
                buff = mbi.parent().parent().current_webview().buffer()
                set_local_keymap(buff.active_keymap())

    def view_focus_changed(self, view, enabled):
        if enabled and not self.enabled_minibuffer:
            # fixes issue were a raw qwebenginepage comes here. To
            # reproduce, have two opened buffers, then C-x 2, C-x 3.
            if hasattr(view.buffer(), "active_keymap"):
                set_local_keymap(view.buffer().active_keymap())
                if view.main_window.current_webview() == view:
                    hooks.webbuffer_current_changed(view.buffer())

    def web_content_edit_focus_changed(self, buff, enabled):
        if enabled:
            buff.set_keymap_mode(Mode.KEYMAP_CONTENT_EDIT)
            if not self.enabled_minibuffer:
                set_local_keymap(buff.active_keymap())
        else:
            buff.set_keymap_mode(Mode.KEYMAP_NORMAL)
            if not self.enabled_minibuffer:
                set_local_keymap(buff.active_keymap())

    def caret_browsing_changed(self, buff, enabled):
        if enabled:
            buff.set_keymap_mode(Mode.KEYMAP_CARET_BROWSING)
            if not self.enabled_minibuffer:
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
        self._prefix_arg_keys = []
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
            yield GLOBAL_KEYMAP

    def _add_keypress(self, keypress):
        self._keypresses.append(keypress)
        logging.debug("keychord: %s" % self._keypresses)

    def _num_update_prefix_arg(self, numstr):
        if not isinstance(self._prefix_arg, int):
            self._prefix_arg = int(numstr)
        else:
            self._prefix_arg = int(str(self._prefix_arg) + numstr)

    def _show_info_kbd(self, extra=""):
        all_presses = self._prefix_arg_keys + self._keypresses
        minibuffer_show_info(
            " ".join((str(k) for k in all_presses)) + extra
        )

    def _handle_keypress(self, sender, keypress):
        if keypress == self.universal_key and not self._keypresses:
            if isinstance(self._prefix_arg, tuple):
                self._prefix_arg = (self._prefix_arg[0] * 4,)
            else:
                self._prefix_arg = (4,)
            self._prefix_arg_keys.append(keypress)
            self._show_info_kbd()
            return True
        if self._prefix_arg is not None:
            try:
                func = self._allowed_universal_keys[keypress.key]
            except KeyError:
                pass
            else:
                if not keypress.has_any_modifier():
                    func()
                    self._prefix_arg_keys.append(keypress)
                    self._show_info_kbd()
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
            else:
                minibuffer_show_info("")
            self._keypresses = []
            self.call_handler.no_call(sender, keymap, keypress)
            self._prefix_arg = None
            self._prefix_arg_keys = []
            return False

        if result.complete:
            self._show_info_kbd()
            self._keypresses = []
            ctx = CommandContext()
            self._prefix_arg = None
            self._prefix_arg_keys = []
            try:
                self.call_handler.call(ctx, keymap, keypress,
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

    def call(self, ctx, keymap, keypress, command):
        if isinstance(command, str):
            try:
                command = self._commands[command]
            except KeyError:
                raise KeyError("No such command: %s" % command)

        command(ctx)

    def no_call(self, sender, keymap, keypress):
        pass

    def partial_call(self, sender, keymap, keypress):
        pass


KEY_EATER = KeyEater()


def send_key_event(keypress):
    from .application import app as _app
    app = _app()
    w = app.focusWindow()
    app.postEvent(w, keypress.to_qevent(QEvent.Type.KeyPress))
    app.postEvent(w, keypress.to_qevent(QEvent.Type.KeyRelease))


def local_keymap():
    return KEY_EATER.local_key_map()


def set_local_keymap(keymap):
    KEY_EATER.set_local_key_map(keymap)


def set_global_keymap_enabled(enable):
    KEY_EATER.set_global_keymap_enabled(enable)
