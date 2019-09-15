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

import importlib

from PyQt5.QtCore import QObject, QEvent, QTimer

from . import hooks


__version__ = '0.9'


# access to every opened buffers
BUFFERS = []

# dictionary of all known commands
COMMANDS = {}


def require(module, package=__package__):
    return importlib.import_module(module, package)


# handler for windows, to be able to list them and determine the one currently
# active.
class WindowsHandler(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.windows = []
        self.current_window = None

    def _on_last_window_closing(self):
        # last window is closed, do not remove it from the list but exit the
        # application. This is required from proper session saving.
        from .application import app
        app().quit()
        return True

    def register_window(self, window):
        window.installEventFilter(self)
        self.windows.append(window)

    def eventFilter(self, window, event):
        t = event.type()
        if t == QEvent.WindowActivate:
            self.current_window = window
            hooks.window_activated(window)
        elif t == QEvent.Close:
            if window.quit_if_last_closed and len(self.windows) == 1:
                if self._on_last_window_closing():
                    return True
            self.windows.remove(window)
            window.deleteLater()
            if window == self.current_window:
                self.current_window = None
            hooks.window_closed(window)

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
    w = current_window()
    if w:
        return w.current_webview().buffer()


def buffers():
    "Returns the list of buffers."
    return BUFFERS


def recent_buffers():
    """
    Returns an iterable of buffers, most recently used first.
    """
    return sorted(BUFFERS, key=lambda b: b.last_use, reverse=True)


def current_minibuffer():
    """
    Returns the current minibuffer.
    """
    w = current_window()
    if w:
        return w.minibuffer()


def minibuffer_show_info(text):
    """
    Display text information in the current minibuffer.
    """
    minibuffer = current_minibuffer()
    if minibuffer:
        minibuffer.show_info(text)


def call_later(fn, msec=0):
    """
    Call the given function after the given time interval.

    If msec is 0, the function call is still delayed to the next handling of
    events in the qt event loop.
    """
    QTimer.singleShot(msec, fn)


class ObjRef(object):
    """
    Maintain object references.
    """
    __slots__ = ("__refs",)

    def __init__(self):
        self.__refs = {}

    def ref(self, obj, data=True):
        self.__refs[obj] = data

    def unref(self, obj):
        return self.__refs.pop(obj)


# Sometimes we need to keep objects around with pyqt to avoid segfault;
# This global object holder is designed to allow that.
GLOBAL_OBJECTS = ObjRef()
