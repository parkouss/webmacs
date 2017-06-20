import re

from PyQt5.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QLabel, \
    QTableView, QHeaderView, QApplication
from PyQt5.QtCore import QObject, pyqtSignal as Signal, pyqtSlot as Slot, \
    QPoint, QEvent, QSortFilterProxyModel, QRegExp, Qt

from .keyboardhandler import KeyboardHandler, is_keypress
from .keymap import Keymap


KEYMAP = Keymap("minibuffer")


class Prompt(QObject):
    label = ""
    got_value = Signal(object)
    closed = Signal()

    def completer_model(self):
        return None

    def validate(self, text):
        return text

    def enable(self, minibuffer):
        self.minibuffer = minibuffer
        minibuffer.label.setText(self.label)
        buffer_input = minibuffer.input()
        buffer_input.show()
        buffer_input.setFocus()
        buffer_input.set_completer_model(self.completer_model())
        buffer_input.returnPressed.connect(self._on_edition_finished)

    def close(self):
        minibuffer = self.minibuffer
        minibuffer.label.setText("")
        buffer_input = minibuffer.input()
        buffer_input.hide()
        buffer_input.setText("")
        c_model = buffer_input.completer_model()
        buffer_input.set_completer_model(None)
        if c_model:
            c_model.deleteLater()
        self.closed.emit()

    @Slot()
    def _on_edition_finished(self):
        txt = self.minibuffer.input().text()
        value = self.validate(txt)
        self.got_value.emit(value)
        self.close()


class Popup(QTableView):
    def __init__(self):
        QTableView.__init__(self)
        self.setParent(None, Qt.Popup)
        self.setFocusPolicy(Qt.NoFocus)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(24)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setEditTriggers(QTableView.NoEditTriggers)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setShowGrid(False)
        self._max_visible_items = 10

    def popup(self, widget):
        h = (24) * min(self._max_visible_items, self.model().rowCount()) + 3

        w = widget.width()
        pos = widget.mapToGlobal(QPoint(0, -(h + 1)))

        self.setGeometry(pos.x(), pos.y(), w, h)

        cols = self.model().columnCount()
        col_width = w / cols
        for i in range(cols):
            self.setColumnWidth(i, col_width)

        if not self.isVisible():
            self.show()


class MinibufferInput(QLineEdit):
    FuzzyFilter = 0
    SimpleFilter = 1

    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)
        self._completer_model = None
        self._popup = Popup()
        self.textEdited.connect(self._show_completions)
        self._popup.installEventFilter(self)
        self.installEventFilter(self)
        self._eat_focusout = False
        self._proxy_model = QSortFilterProxyModel(self)
        self._proxy_model.setFilterKeyColumn(-1)
        self._popup.setModel(self._proxy_model)
        self._popup.activated.connect(self._on_completion_activated)
        self._filter_type = self.SimpleFilter
        self.keyboard_handler = KeyboardHandler([KEYMAP])
        self._mark = False

    def event(self, event):
        if is_keypress(event) and self.keyboard_handler.handle_keypress(event):
            return True
        return QLineEdit.event(self, event)

    def eventFilter(self, obj, event):
        etype = event.type()
        if etype == QEvent.FocusOut and obj == self and self._eat_focusout \
           and self._popup.isVisible():
            # keep the focus on the line edit
            return True
        elif etype == QEvent.MouseButtonPress:
            # if we've clicked in the widget (or its descendant), let it handle
            # the click
            pos = obj.mapToGlobal(event.pos())
            target = QApplication.widgetAt(pos)
            if target and (self.isAncestorOf(target) or target == self):
                if not self._popup.underMouse():
                    self._popup.hide()
                target.event(event)
                return True

            if not self._popup.underMouse():
                self._popup.hide()
                return True
        elif etype in (QEvent.KeyPress, QEvent.KeyRelease):
            # send event to the line edit
            self._eat_focusout = True
            self.event(event)
            self._eat_focusout = False
            return True

        return QLineEdit.eventFilter(self, obj, event)

    def set_completer_model(self, completer_model):
        self._proxy_model.setSourceModel(completer_model)

    def completer_model(self):
        return self._proxy_model.sourceModel()

    def set_filter_type(self, type):
        self._filter_type = type
        if self._popup.isVisible():
            self._show_completions(self.text)

    def _show_completions(self, txt, force=False):
        if self._filter_type == self.SimpleFilter:
            pattern = "^" + QRegExp.escape(txt)
        else:
            pattern = ".*".join(QRegExp.escape(t) for t in txt.split())

        self._proxy_model.setFilterRegExp(QRegExp(pattern))
        if self._proxy_model.rowCount() == 0:
            self._popup.hide()
        elif not txt and not force:
            self._popup.hide()
        else:
            self._popup.popup(self)

    def show_completions(self):
        self._show_completions(self.text(), True)

    def _on_completion_activated(self, index):
        self._popup.hide()
        model = index.model()
        if index.column() != 0:
            index = model.index(index.row(), 0)

        self.setText(model.data(index))

    def popup(self):
        return self._popup

    def complete(self):
        if not self._popup.isVisible():
            return

        index = self._popup.selectionModel().currentIndex()
        if index.isValid():
            self._on_completion_activated(index)

    def select_next_completion(self, forward=True):
        model = self._proxy_model
        entries = model.rowCount()
        if entries == 0:
            return

        selection = self._popup.selectionModel().currentIndex()
        if not selection.isValid():
            row = 0 if forward else (entries - 1)
        else:
            if forward:
                row = row + 1
                if row >= entries:
                    row = 0
            else:
                row = row - 1
                if row < 0:
                    row = (entries - 1)

        self._popup.selectRow(row)

    def mark(self):
        return self._mark

    def set_mark(self, value=None):
        if value is None:
            value = not self._mark
        self._mark = value
        return self._mark


class Minibuffer(QWidget):
    def __init__(self, window):
        QWidget.__init__(self, window)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.label = QLabel(self)
        layout.addWidget(self.label)

        self._input = MinibufferInput(self)
        layout.addWidget(self._input)

        self._input.hide()
        self._prompt = None

    def input(self):
        return self._input

    def prompt(self, prompt):
        self.close_prompt()
        self._prompt = prompt
        if prompt:
            prompt.enable(self)
            prompt.closed.connect(self._prompt_closed)
            prompt.closed.connect(prompt.deleteLater)

    def close_prompt(self):
        if self._prompt:
            self._prompt.close()
            self._prompt = None

    def _prompt_closed(self):
        self._prompt = None


def current_minibuffer():
    from .window import current_window
    return current_window().minibuffer()


@KEYMAP.define_key("Tab")
def complete():
    input = current_minibuffer().input()

    if not input.popup().isVisible():
        input.show_completions()
    else:
        input.select_next_completion()


@KEYMAP.define_key("C-n")
@KEYMAP.define_key("Down")
def next_completion():
    current_minibuffer().input().select_next_completion()


@KEYMAP.define_key("C-p")
@KEYMAP.define_key("Top")
def previous_completion():
    current_minibuffer().input().select_next_completion(False)


@KEYMAP.define_key("Return")
def edition_finished():
    current_minibuffer().input().complete()
    current_minibuffer().input().popup().hide()
    current_minibuffer().input().returnPressed.emit()


@KEYMAP.define_key("C-g")
@KEYMAP.define_key("Esc")
def cancel():
    minibuffer = current_minibuffer()
    input = minibuffer.input()
    if input.popup().isVisible():
        input.popup().hide()
    elif input.selectedText():
        input.deselect()
    else:
        minibuffer.close_prompt()


@KEYMAP.define_key("M-Backspace")
def clean_aindent_bsunindent():
    input = current_minibuffer().input()

    parts = re.split(r"([-_ ])", input.text())
    while parts:
        if parts[-1] in ("", "-", "_", " "):
            parts.pop()
        else:
            break
    input.setText("".join(parts[:-1]))


@KEYMAP.define_key("C-Space")
def set_mark():
    if not current_minibuffer().input().set_mark():
        current_minibuffer().input().deselect()


@KEYMAP.define_key("C-f")
@KEYMAP.define_key("Right")
def forward_char():
    edit = current_minibuffer().input()
    edit.cursorForward(edit.mark(), 1)


@KEYMAP.define_key("C-b")
@KEYMAP.define_key("Left")
def backward_char():
    edit = current_minibuffer().input()
    edit.cursorBackward(edit.mark(), 1)


@KEYMAP.define_key("M-f")
@KEYMAP.define_key("M-Right")
def forward_word():
    edit = current_minibuffer().input()
    edit.cursorWordForward(edit.mark())


@KEYMAP.define_key("M-b")
@KEYMAP.define_key("M-Left")
def backward_word():
    edit = current_minibuffer().input()
    edit.cursorWordBackward(edit.mark())


@KEYMAP.define_key("M-w")
def copy():
    current_minibuffer().input().copy()
    current_minibuffer().input().deselect()


@KEYMAP.define_key("C-w")
def cut():
    current_minibuffer().input().cut()


@KEYMAP.define_key("C-y")
def paste():
    current_minibuffer().input().paste()


@KEYMAP.define_key("C-d")
def delete_char():
    current_minibuffer().input().del_()


@KEYMAP.define_key("M-d")
def delete_word():
    edit = current_minibuffer().input()
    if edit.hasSelectedText():
        edit.del_()
    else:
        pos = edit.cursorPosition()
        text = edit.text()
        deleted_some = False
        for i in range(pos, len(text)):
            char = text[i]
            if char in ("-", "_", " "):
                if deleted_some:
                    break
                edit.del_()
            else:
                deleted_some = True
                edit.del_()


@KEYMAP.define_key("C-a")
def beginning_of_line():
    edit = current_minibuffer().input()
    edit.home(edit.mark())


@KEYMAP.define_key("C-e")
def end_of_line():
    edit = current_minibuffer().input()
    edit.end(edit.mark())
