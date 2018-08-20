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


__version__ = '0.7'


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
        elif t == QEvent.Close:
            if window.quit_if_last_closed and len(self.windows) == 1:
                if self._on_last_window_closing():
                    return True
            self.windows.remove(window)
            window.deleteLater()
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
    w = current_window()
    if w:
        return w.current_webview().buffer()


def buffers():
    "Return the list of buffers."
    return BUFFERS


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


class CommandContext(object):
    def __init__(self, sender, keypress):
        self.sender = sender
        self.keypress = keypress
        self.window = current_window()
        self.view = self.window.current_webview() if self.window else None
        self.buffer = self.view.buffer() if self.view else None
        self.prompt = None

    @property
    def minibuffer(self):
        win = self.window
        if win:
            return win.minibuffer()
