import logging
import weakref

from PyQt5.QtCore import QObject, QEvent, pyqtSlot as Slot

from .keymaps import KeyPress, global_key_map
from . import hooks
from . import register_global_event_callback, COMMANDS, minibuffer_show_info


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
        self._minibuffer_inputs.remove(minibuffer_input)

    def eventFilter(self, obj, event):
        t = event.type()
        if t == QEvent.WindowActivate:
            if obj in self._views:
                # enable the current view
                set_local_keymap(obj.keymap())
        elif t == QEvent.FocusIn:
            if obj in self._minibuffer_inputs:
                # when the minibuffer input is shown, enable it
                set_local_keymap(obj.keymap())
        elif t == QEvent.FocusOut:
            if obj in self._minibuffer_inputs:
                # the focus is lost when the popup is active
                if not obj.popup().isVisible():
                    # when the minibuffer input is hidden, enable its view
                    set_local_keymap(
                        obj.parent().parent().current_web_view().keymap())
        return QObject.eventFilter(self, obj, event)

    def web_content_edit_focus_changed(self, window, enabled):
        if enabled:
            buff = window.current_web_view().buffer()
            set_local_keymap(buff.content_edit_keymap())
        else:
            if not window.minibuffer().input().hasFocus():
                buff = window.current_web_view().buffer()
                set_local_keymap(buff.keymap())


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

    def set_local_key_map(self, keymap):
        self._local_key_map = keymap
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

    def active_keymaps(self):
        if self._local_key_map:
            yield self._local_key_map
        if self._use_global_keymap:
            yield global_key_map()

    def _handle_keypress(self, keypress):
        incomplete_keychord = False
        command_called = False
        self._keypresses.append(keypress)
        minibuffer_show_info(
            " ".join((str(k) for k in self._keypresses))
        )
        logging.debug("keychord: %s" % self._keypresses)

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

        return command_called or incomplete_keychord

    def _call_command(self, command):
        if isinstance(command, str):
            try:
                command = self._commands[command]
            except KeyError:
                raise KeyError("No such command: %s" % command)

        command()


KEY_EATER = KeyEater()
register_global_event_callback(QEvent.KeyPress, KEY_EATER.event_filter)


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
