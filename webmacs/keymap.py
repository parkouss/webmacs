import re

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

TO_QT = {
    "C": "Ctrl",
    "M": "Alt",
    "S": "Shift"
}

FROM_QT = {v: k for k, v in TO_QT.items()}


RE_TO_QT = re.compile(r"(%s)-" % "|".join(TO_QT.keys()))
RE_FROM_QT = re.compile(r"(%s)\+" % "|".join(FROM_QT.keys()))


class KeyPress(object):
    """
    Represent a key pressed, possibly with one or more modifier.
    """
    __slots__ = "key"

    def __init__(self, key):
        self.key = key

    @classmethod
    def fromQEvent(cls, event):
        # see https://stackoverflow.com/a/6665017
        key = event.key()
        modifiers = event.modifiers()
        if modifiers & Qt.ShiftModifier:
            key += Qt.SHIFT
        if modifiers & Qt.ControlModifier:
            key += Qt.CTRL
        if modifiers & Qt.AltModifier:
            key += Qt.ALT
        if modifiers & Qt.MetaModifier:
            key += Qt.META
        return cls(key)

    @classmethod
    def fromStr(cls, string):
        parts = [p for p in RE_TO_QT.split(string) if p]
        key = QKeySequence.fromString(
            "+".join(TO_QT.get(p, p) for p in parts))[0]
        return cls(key)

    def __eq__(self, other):
        return self.key == other.key

    def __ne__(self, other):
        return self.key != other.key

    def __str__(self):
        string = QKeySequence(self.key).toString()
        parts = [p for p in RE_FROM_QT.split(string) if p]
        return "-".join(FROM_QT.get(p, p) for p in parts)
