from collections import namedtuple
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent


KEY2CHAR = {}
CHAR2KEY = {}


def _set_key(key, char, *chars):
    KEY2CHAR[key] = char
    CHAR2KEY[char] = key
    for ch in chars:
        CHAR2KEY[ch] = key


_set_key(Qt.Key_A, "a", "A")
_set_key(Qt.Key_B, "b", "B")
_set_key(Qt.Key_C, "c", "C")
_set_key(Qt.Key_D, "d", "D")
_set_key(Qt.Key_E, "e", "E")
_set_key(Qt.Key_F, "f", "F")
_set_key(Qt.Key_G, "g", "G")
_set_key(Qt.Key_H, "h", "H")
_set_key(Qt.Key_I, "i", "I")
_set_key(Qt.Key_J, "j", "J")
_set_key(Qt.Key_K, "k", "K")
_set_key(Qt.Key_L, "l", "L")
_set_key(Qt.Key_M, "m", "M")
_set_key(Qt.Key_N, "n", "N")
_set_key(Qt.Key_O, "o", "O")
_set_key(Qt.Key_P, "p", "P")
_set_key(Qt.Key_Q, "q", "Q")
_set_key(Qt.Key_R, "r", "R")
_set_key(Qt.Key_S, "s", "S")
_set_key(Qt.Key_T, "t", "T")
_set_key(Qt.Key_U, "u", "U")
_set_key(Qt.Key_V, "v", "v")
_set_key(Qt.Key_W, "w", "W")
_set_key(Qt.Key_X, "x", "X")
_set_key(Qt.Key_Y, "y", "Y")
_set_key(Qt.Key_Z, "z", "Z")

_set_key(Qt.Key_0, "0")
_set_key(Qt.Key_1, "1")
_set_key(Qt.Key_2, "2")
_set_key(Qt.Key_3, "3")
_set_key(Qt.Key_4, "4")
_set_key(Qt.Key_5, "5")
_set_key(Qt.Key_6, "6")
_set_key(Qt.Key_7, "7")
_set_key(Qt.Key_8, "8")
_set_key(Qt.Key_9, "9")

_set_key(Qt.Key_Escape, "Esc")
_set_key(Qt.Key_Tab, "Tab")
_set_key(Qt.Key_Down, "Down")
_set_key(Qt.Key_Up, "Up")
_set_key(Qt.Key_Right, "Right")
_set_key(Qt.Key_Left, "Left")
_set_key(Qt.Key_Return, "Return")
_set_key(Qt.Key_Backspace, "Backspace")
_set_key(Qt.Key_Space, "Space")
_set_key(Qt.Key_Less, "<")
_set_key(Qt.Key_Greater, ">")

_set_key(Qt.Key_Egrave, "è", "È")
_set_key(Qt.Key_Eacute, "é", "É")


def is_one_letter_upcase(char):
    return len(char) == 1 and char.isalpha() and char.isupper()


_KeyPress = namedtuple("_KeyPress", ("key", "control_modifier", "alt_modifier",
                                     "super_modifier", "is_upper_case"))


class KeyPress(_KeyPress):
    @classmethod
    def from_qevent(cls, event):
        key = event.key()
        if key not in KEY2CHAR:
            return None

        modifiers = event.modifiers()

        return cls(
            key,
            bool(modifiers & Qt.ControlModifier),
            bool(modifiers & Qt.AltModifier),
            bool(modifiers & Qt.MetaModifier),
            is_one_letter_upcase(event.text())
        )

    @classmethod
    def from_str(cls, string):
        ctrl, alt, super = False, False, False
        parts = string.split("-")
        for p in parts[:-1]:
            if p == "C":
                ctrl = True
            elif p == "M":
                alt = True
            elif p == "S":
                super = True
            else:
                raise Exception("Unknown key modifier: %s" % p)

        text = parts[-1]
        try:
            key = CHAR2KEY[text]
        except KeyError:
            raise Exception("Unknown key %s" % text)

        return cls(
            key,
            ctrl,
            alt,
            super,
            is_one_letter_upcase(text)
        )

    def to_qevent(self, type):
        modifiers = Qt.NoModifier
        key = self.key
        if self.control_modifier:
            modifiers |= Qt.ControlModifier
        if self.alt_modifier:
            modifiers |= Qt.AltModifier
        if self.super_modifier:
            modifiers |= Qt.MetaModifier

        if self.is_upper_case:
            return QKeyEvent(type, key, modifiers, KEY2CHAR[key].upper())
        else:
            return QKeyEvent(type, key, modifiers)

    def __str__(self):
        keyrepr = []

        if self.control_modifier:
            keyrepr.append("C")
        if self.alt_modifier:
            keyrepr.append("M")
        if self.super_modifier:
            keyrepr.append("S")

        char = KEY2CHAR[self.key]
        if self.is_upper_case:
            char = char.upper()

        keyrepr.append(char)

        return "-".join(keyrepr)

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

    def _define_key(self, key, binding):
        keys = [KeyPress.from_str(k) for k in key.split()]
        assert keys, "key should not be empty"
        assert callable(binding) or isinstance(binding, str), \
            "binding should be callable or a command name"

        kmap = self
        for keypress in keys[:-1]:
            if keypress in kmap.bindings:
                othermap = kmap.bindings[keypress]
                if not isinstance(othermap, Keymap):
                    othermap = Keymap()
            else:
                othermap = Keymap()
            kmap.bindings[keypress] = othermap
            kmap = othermap

        kmap.bindings[keys[-1]] = binding

    def define_key(self, key, binding=None):
        """
        Define a binding (callable) for a key chord on the keymap.

        Note that if binding is not given, it should be used as a decorator.
        """
        if binding is None:
            def wrapper(func):
                self._define_key(key, func)
                return func
            return wrapper
        else:
            self._define_key(key, binding)

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

    def __str__(self):
        return self.name


GLOBAL_KEYMAP = Keymap("global")


def global_key_map():
    return GLOBAL_KEYMAP
