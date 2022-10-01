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

import os
import itertools
import collections

from PyQt6.QtCore import QObject, QAbstractTableModel, QModelIndex, Qt, \
    pyqtSlot as Slot, pyqtSignal as Signal, QEventLoop, QPropertyAnimation, \
    QEvent, QRegularExpression

from PyQt6.QtGui import QColor, QRegularExpressionValidator

from ..keyboardhandler import set_global_keymap_enabled
from ..keymaps import Keymap
from .. import variables


FLASH_DURATION = variables.define_variable(
    "minibuffer-flash-duration",
    "Total duration in seconds of the minibuffer flash animation.",
    0.3,
    type=variables.Float(min=0.0),
)
FLASH_COLOR = variables.define_variable(
    "minibuffer-flash-color",
    "Color for the minibuffer flash animation. Should be given as"
    " an hexadecimal string.",
    "#ff0000",
    type=variables.String(),
)
FLASH_COUNT = variables.define_variable(
    "minibuffer-flash-count",
    "How many flashes should be displayed during the minibuffer"
    " flash animation.",
    2,
    type=variables.Int(min=0),
)


class FSModel(QAbstractTableModel):
    """
    A custom filesystemmodel that does work with the custom completer;

    May not be as efficient as the qt version, but works without much pain.
    """

    def __init__(self, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._root_dir = ""
        self._files = []

    def rowCount(self, index=QModelIndex()):
        return len(self._files)

    def columnCount(self, index=QModelIndex()):
        return 1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        try:
            return os.path.join(self._root_dir, self._files[index.row()])
        except IndexError:
            return None

    @Slot(str)
    def text_changed(self, text):
        if text.endswith("/"):
            root_dir = text
        else:
            root_dir = os.path.dirname(text)

        if root_dir != self._root_dir:
            try:
                files = os.listdir(root_dir)
            except OSError:
                return
            self.beginResetModel()
            self._files = files
            self._root_dir = root_dir
            self.endResetModel()


class PromptTableModel(QAbstractTableModel):
    def __init__(self, data, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, index=QModelIndex()):
        return len(self._data)

    def columnCount(self, index=QModelIndex()):
        if self._data:
            return len(self._data[0])
        return 0

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        return index.internalPointer()

    def index(self, row, col, parent=QModelIndex()):
        try:
            return self.createIndex(row, col, self._data[row][col])
        except IndexError:
            return QModelIndex()


def _prompt_exec(prompt, loop):
    # mocked in tests to not block.
    loop.exec()


class Prompt(QObject):
    label = ""
    complete_options = {}
    keymap = None
    history = None
    value_return_index_data = False

    SimpleMatch = 0
    FuzzyMatch = 1

    finished = Signal()
    closed = Signal()

    def __init__(self, ctx):
        QObject.__init__(self)
        self.ctx = ctx
        self.__finished = False

    def completer_model(self):
        return None

    def enable(self, minibuffer):
        self.__flash = None
        self.__index = QModelIndex()
        self.minibuffer = minibuffer
        minibuffer.label.setText(self.label)
        buffer_input = minibuffer.input()
        buffer_input.reinit()
        buffer_input.show()
        buffer_input.setFocus()
        # keeping valid references of qobjects is really hard sometimes
        # without this completer reference on self, visited_links_history
        # will (quite) randomly generate segfault...
        self.__completer_model = completer_model = self.completer_model()
        if hasattr(completer_model, "text_changed"):
            buffer_input.textEdited.connect(completer_model.text_changed)
        buffer_input.set_completer_model(completer_model)
        buffer_input.returnPressed.connect(self._on_edition_finished)
        buffer_input.completion_activated.connect(
            self._on_completion_activated)
        buffer_input.configure_completer(self.complete_options)
        if self.complete_options.get("complete-empty"):
            buffer_input.show_completions()

    def close(self):
        minibuffer = self.minibuffer
        minibuffer.label.setText("")
        buffer_input = minibuffer.input()
        buffer_input.returnPressed.disconnect(self._on_edition_finished)
        buffer_input.completion_activated.disconnect(
            self._on_completion_activated)

        view = minibuffer.parent().current_webview()
        # calling setFocus() on the view is required, else the view is scrolled
        # to the top automatically. But we don't even get a focus in event;
        view.internal_view().setFocus()
        # and to not lose the keyboard focus
        view.show_focused(True)

        buffer_input.hide()
        buffer_input.set_mark(False)
        c_model = buffer_input.completer_model()
        buffer_input.set_completer_model(None)
        if c_model:
            c_model.deleteLater()
        if self.history:
            self.history.reset()
        if self.__flash:
            self.__flash.stop()
            self.__flash.deleteLater()
        self.closed.emit()

    def flash(self):
        if self.__flash is None:
            self.__flash = self._create_flash_animation()
            if self.__flash:
                self.__flash.start()
        elif self.__flash.state() == self.__flash.Stopped:
            self.__flash.start()

    def _create_flash_animation(self):
        if FLASH_COUNT.value <= 0 or \
           FLASH_DURATION.value <= 0:
            return None
        minibuff_input = self.minibuffer.input()
        anim = QPropertyAnimation(minibuff_input,
                                  b"background_color")
        base = minibuff_input.property(b"background_color")
        flash_color = QColor(FLASH_COLOR.value)
        anim.setDuration(int(FLASH_DURATION.value * 1000))

        step = 1./(FLASH_COUNT.value * 2)
        pos = step
        colors = itertools.cycle((flash_color, base))

        anim.setStartValue(base)
        while pos < 1:
            anim.setKeyValueAt(pos, next(colors))
            pos += step
        anim.setEndValue(base)
        return anim

    def _on_completion_activated(self, index):
        self.__index = index

    def value(self):
        if not self.__finished:
            return None
        if self.value_return_index_data:
            index = self.index()
            if index:
                return index.internalPointer()
        else:
            return self.minibuffer.input().text()

    def index(self):
        return self.__index

    @Slot()
    def _on_edition_finished(self):
        history = self.history
        if history:
            history.push(self.minibuffer.input().text())
        self.close()
        self.__finished = True
        self.finished.emit()

    def exec(self, minibuffer, flash=False, sync=True):
        self.enable(minibuffer)
        if flash:
            self.flash()
        if sync:
            loop = QEventLoop()
            self.closed.connect(loop.quit)
            _prompt_exec(self, loop)
            return self.value()


class PromptHistory(object):
    """
    In memory history for prompts.
    """

    def __init__(self, maxsize=50):
        self._history = collections.deque((), maxlen=maxsize)
        self.reset()

    def reset(self):
        self._in_user_value = True
        self._user_value = ""
        self._cursor = 0

    def push(self, text):
        # avoid following duplicates
        if self._history and self._history[0] == text:
            return
        self._history.append(text)

    def in_user_value(self):
        """
        indicate if we are in the state where the user see its custom value
        """
        return self._in_user_value

    def set_user_value(self, text):
        self._user_value = text

    def __get(self, delta):
        # delta must be 1 or -1
        size = len(self._history)
        if size == 0:
            return self._user_value

        if self._in_user_value:
            self._in_user_value = False
            self._cursor = 0 if delta > 0 else size - 1
        else:
            cursor = self._cursor + delta
            if cursor >= size or cursor < 0:
                self._in_user_value = True
                return self._user_value
            self._cursor = cursor

        return self._history[self._cursor]

    def get_next(self):
        return self.__get(1)

    def get_previous(self):
        return self.__get(-1)


class YesNoPrompt(Prompt):
    NO = 0
    YES = 1
    ALWAYS = 2
    NEVER = 3

    keymap = Keymap("yes-no")  # an empty keymap

    def __init__(self, label, parent=None, always=False, never=False):
        Prompt.__init__(self, parent)
        self.never = never
        self.always = always
        self.label = label + self.build_label()
        self.valid_keys = self.build_valid_keys()
        self._value = 0

    def build_label(self):
        optional = ""
        if self.always:
            optional += "/Always"
        if self.never:
            optional += "/Never"
        return "[yes/no{}]".format(optional)

    def build_valid_keys(self):
        optional = ""
        if self.always:
            optional += "A"
        if self.never:
            optional += "N"
        return "yYn{}".format(optional)

    def enable(self, minibuffer):
        set_global_keymap_enabled(False)  # disable any global keychord

        Prompt.enable(self, minibuffer)
        buffer_input = minibuffer.input()

        validator = QRegularExpressionValidator(QRegularExpression(
            "[" + self.valid_keys + "]"), buffer_input)
        buffer_input.setValidator(validator)
        minibuffer.input().installEventFilter(self)
        buffer_input.textEdited.connect(self._on_text_edited)

    def _on_text_edited(self, text):
        if text in ("y", "Y"):
            self._value = self.YES
        elif text == "N":
            self._value = self.NEVER
        elif text == "A":
            self._value = self.ALWAYS
        else:
            self._value = self.NO

        self.close()
        set_global_keymap_enabled(True)

    def value(self):
        return self._value

    def eventFilter(self, obj, evt):
        if evt.type() in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease,
                          QEvent.Type.ShortcutOverride):
            if evt.text() in self.valid_keys:
                return False
            evt.accept()
            self.flash()
            return True
        return False

    def close(self):
        self.minibuffer.input().removeEventFilter(self)
        set_global_keymap_enabled(True)
        Prompt.close(self)


class AskPasswordPrompt(Prompt):
    def __init__(self, buffer):
        Prompt.__init__(self, None)
        self.buffer = buffer
        self.username, self.password = "", ""
        self.label = "username: "
        set_global_keymap_enabled(False)

    def _on_edition_finished(self):
        input = self.minibuffer.input()
        if not self.username:
            self.username = input.text()
            input.clear()
            input.setEchoMode(input.EchoMode.Password)
            self.minibuffer.label.setText("password: ")
        else:
            self.password = input.text()
            Prompt._on_edition_finished(self)
            set_global_keymap_enabled(True)
