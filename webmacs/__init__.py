import importlib

from PyQt5.QtCore import QObject, QEvent


__version__ = '0.1'


# access to every opened buffers
BUFFERS = []

# dictionary of all known commands
COMMANDS = {}


def require(module, package=__package__):
        return importlib.import_module(module, package)


# application level event filter. It will be set on the QApplication instance.
class _GlobalEventFilter(QObject):
    def __init__(self):
        QObject.__init__(self)
        self._events = {}

    def register(self, event_type, callback):
        self._events[event_type] = callback

    def eventFilter(self, obj, event):
        try:
            cb = self._events[event.type()]
        except KeyError:
            return QObject.eventFilter(self, obj, event)
        result = cb(obj, event)
        if result is None:
            return QObject.eventFilter(self, obj, event)
        return result


GLOBAL_EVENT_FILTER = _GlobalEventFilter()


def register_global_event_callback(event_type, callback):
    GLOBAL_EVENT_FILTER.register(event_type, callback)


# handler for windows, to be able to list them and determine the one currently
# active.
class WindowsHandler(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.windows = []
        self.current_window = None

    def register_window(self, window):
        window.installEventFilter(self)
        self.windows.append(window)

    def eventFilter(self, window, event):
        t = event.type()
        if t == QEvent.WindowActivate:
            self.current_window = window
        elif t == QEvent.Close:
            self.windows.remove(window)
            if window == self.current_window:
                self.current_window = None

        return QObject.eventFilter(self, window, event)


WINDOWS_HANDLER = WindowsHandler()


def windows():
    """
    Returns the window list.

    Do not modify this list.
    """
    return WINDOWS_HANDLER.windows


def current_window():
    """
    Returns the currently activated window.
    """
    return WINDOWS_HANDLER.current_window


def current_buffer():
    """
    Returns the current buffer.
    """
    return current_window().current_web_view().buffer()


def buffers():
    "Return the list of buffers."
    return BUFFERS


def current_minibuffer():
    """
    Returns the current minibuffer.
    """
    return current_window().minibuffer()


def minibuffer_show_info(text):
    """
    Display text information in the current minibuffer.
    """
    current_minibuffer().show_info(text)
