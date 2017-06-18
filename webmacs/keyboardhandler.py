from PyQt5.QtCore import QObject, QEvent

from .keymap import KeyPress, global_key_map


def is_keypress(event):
    return event.type() == QEvent.KeyPress


class KeyboardHandler(object):
    """
    Handle qt keypress event against a list of keymaps.

    THE way to get full key events in qt is to override the event() method of a
    given QObject. Using an event filter (aba KeyboardEventFilterHandler) will
    not catch Tab keys in some circumstances; So to be sure to catch
    everything, use a construct like::

      class MyObject(SomeQObjectSubclass):
          def __init__(self):
              SomeQObjectSubclass.__init__(self)
              self.self.keyboard_handler = KeyboardHandler(keymaps)

          def event(self, event):
              if is_keypress(event) and \
                  self.keyboard_handler.handle_keypress(event):

                  return True

              return SomeQObjectSubclass.event(self, event)
    """
    def __init__(self, keymaps, use_global=True):
        self._keymaps = keymaps
        if use_global:
            self._keymaps.append(global_key_map())
        self._keypresses = []

        # late import to avoid import issues
        from .commands import COMMANDS
        self._commands = COMMANDS

    def handle_keypress(self, event):
        key = KeyPress.from_qevent(event)
        if key is None:
            return True
        if self._handle_keypress(key):
            return True

    def _handle_keypress(self, keypress):
        incomplete_keychord = False
        command_called = False
        self._keypresses.append(keypress)

        for keymap in self._keymaps:
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


class KeyboardEventFilterHandler(QObject):
    def __init__(self, keymaps, parent=None, **kwargs):
        QObject.__init__(self, parent)
        self.keyboard_handler = KeyboardHandler(keymaps, **kwargs)

    def eventFilter(self, obj, event):
        if is_keypress(event) and self.keyboard_handler.handle_keypress(event):
            return True
        return QObject.eventFilter(self, obj, event)
