import re

from collections import namedtuple
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
    def from_qevent(cls, event):
        # see https://stackoverflow.com/a/6665017
        key = event.key()
        # key is a either a single modifier press or unknown
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta,
                   Qt.Key_unknown):
            return None

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
    def from_str(cls, string):
        parts = [p for p in RE_TO_QT.split(string) if p]
        key = QKeySequence.fromString(
            "+".join(TO_QT.get(p, p) for p in parts))[0]
        return cls(key)

    def __eq__(self, other):
        return self.key == other.key

    def __ne__(self, other):
        return self.key != other.key

    def __hash__(self):
        return self.key

    def __str__(self):
        string = QKeySequence(self.key).toString()

        def to_s(p):
            if p in FROM_QT:
                return FROM_QT[p]
            elif len(p) == 1 and p.isalpha():
                return p.lower()
            return p

        return "-".join(to_s(p) for p in RE_FROM_QT.split(string) if p)

    def __repr__(self):
        return "<%s (%s)>" % (self.__class__.__name__, str(self))


KeymapLookupResult = namedtuple("KeymapLookupResult",
                                ("complete", "command"))


class Keymap(object):
    __slots__ = ("name", "bindings", "parent")

    def __init__(self, name=None, parent=None):
        self.name = name
        self.parent = parent
        self.bindings = {}

    def define_key(self, key, binding):
        keys = [KeyPress.from_str(k) for k in key.split()]
        assert keys, "key should not be empty"
        assert callable(binding), "binding should be callable"

        kmap = self
        for keypress in keys[:-1]:
            if keypress in kmap.bindings:
                othermap = kmap.bindings[keypress]
                if not isinstance(othermap, Keymap):
                    othermap = Keymap()
            else:
                othermap = Keymap()
            kmap.bindings[keypress] = othermap
            othermap = kmap

        kmap.bindings[keys[-1]] = binding

    def _look_up(self, keypress):
        keymap = self
        while keymap:
            try:
                return keymap.bindings[keypress]
            except KeyError:
                keymap = keymap.parent

    def lookup(self, keypresses):
        partial_match = False
        keymap = self
        for keypress in keypresses:
            while keymap:
                entry = keymap.bindings.get(keypress)
                if entry is not None:
                    if isinstance(entry, Keymap):
                        keymap = entry
                        partial_match = True
                        break
                    else:
                        return KeymapLookupResult(True, entry)
                keymap = keymap.parent

        if keymap is None:
            return None
        elif partial_match:
            return KeymapLookupResult(False, None)
        else:
            return None
