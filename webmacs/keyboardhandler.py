import logging

from PyQt5.QtCore import QObject, QEvent, pyqtSlot as Slot

from .keymap import KeyPress, global_key_map
from .commands import COMMANDS


class LocalKeymapSetter(QObject):
    def __init__(self):
        QObject.__init__(self)
        self._views = []
        self._minibuffer_inputs = []
        self._current_obj = None

    def register_view(self, view):
        view.installEventFilter(self)
        view.destroyed.connect(self._view_destroyed)
        self._views.append(view)

    @Slot(QObject)
    def _view_destroyed(self, view):
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
                KEY_EATER.set_local_key_map_provider(obj.keymap)
        elif t == QEvent.Show:
            if obj in self._minibuffer_inputs:
                # when the minibuffer input is shown, enable it
                KEY_EATER.set_local_key_map_provider(obj.keymap)
        elif t == QEvent.Hide:
            if obj in self._minibuffer_inputs:
                # when the minibuffer input is hidden, enable its view
                KEY_EATER.set_local_key_map_provider(
                    obj.parent().parent().current_web_view().keymap)
        return QObject.eventFilter(self, obj, event)


LOCAL_KEYMAP_SETTER = LocalKeymapSetter()


class KeyEater(QObject):
    """
    Handle Qt keypresses events.
    """
    def __init__(self):
        QObject.__init__(self)
        self._keypresses = []
        self._commands = COMMANDS
        self._local_key_map_provider = None

    def set_local_key_map_provider(self, func):
        self._local_key_map_provider = func

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = KeyPress.from_qevent(event)
            if key is None:
                return False
            if self._handle_keypress(key):
                return True
        return QObject.eventFilter(self, obj, event)

    def active_keymaps(self):
        if self._local_key_map_provider:
            yield self._local_key_map_provider()
        yield global_key_map()

    def _handle_keypress(self, keypress):
        incomplete_keychord = False
        command_called = False
        self._keypresses.append(keypress)
        logging.info("keychord: %s" % self._keypresses)

        for keymap in self.active_keymaps():
            result = keymap.lookup(self._keypresses)

            if result is None:
                pass
            elif not result.complete:
                incomplete_keychord = True
            else:
                try:
                    self._call_command(result.command)
                except Exception as exc:
                    print("Error calling command: %s" % exc)
                    import traceback
                    traceback.print_exc()
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
