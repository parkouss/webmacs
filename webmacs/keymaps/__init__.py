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

import warnings

from collections import namedtuple
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent


KEY2CHAR = {}
CHAR2KEY = {}
KEYMAPS = {}


def _set_key(key, char, *chars):
    KEY2CHAR[key] = char
    CHAR2KEY[char] = key
    for ch in chars:
        CHAR2KEY[ch] = key


# see http://doc.qt.io/qt-5/qt.html#Key-enum,
# https://www.blunix.org/using-german-umlauts-on-us-layout-keyboards/

_set_key(Qt.Key_Escape, "Esc")
_set_key(Qt.Key_Tab, "Tab")
_set_key(Qt.Key_Backtab, "Backtab")
_set_key(Qt.Key_Backspace, "Backspace")
_set_key(Qt.Key_Return, "Return")
_set_key(Qt.Key_Enter, "Enter")
_set_key(Qt.Key_Insert, "Insert")
_set_key(Qt.Key_Delete, "Delete")
_set_key(Qt.Key_Pause, "Pause")  # pause/break key, not media pause
_set_key(Qt.Key_Print, "Print")
_set_key(Qt.Key_SysReq, "SysReq")
_set_key(Qt.Key_Clear, "Clear")
_set_key(Qt.Key_Home, "Home")
_set_key(Qt.Key_End, "End")
_set_key(Qt.Key_Left, "Left")
_set_key(Qt.Key_Up, "Up")
_set_key(Qt.Key_Right, "Right")
_set_key(Qt.Key_Down, "Down")
_set_key(Qt.Key_PageUp, "PageUp")
_set_key(Qt.Key_PageDown, "PageDown")

_set_key(Qt.Key_F1, "F1")
_set_key(Qt.Key_F2, "F2")
_set_key(Qt.Key_F3, "F3")
_set_key(Qt.Key_F4, "F4")
_set_key(Qt.Key_F5, "F5")
_set_key(Qt.Key_F6, "F6")
_set_key(Qt.Key_F7, "F7")
_set_key(Qt.Key_F8, "F8")
_set_key(Qt.Key_F9, "F9")
_set_key(Qt.Key_F10, "F10")
_set_key(Qt.Key_F11, "F11")
_set_key(Qt.Key_F12, "F12")


_set_key(Qt.Key_Space, "Space")
_set_key(Qt.Key_Exclam, "!")
_set_key(Qt.Key_QuoteDbl, '"')
_set_key(Qt.Key_Dollar, '$')
_set_key(Qt.Key_Percent, "%")
_set_key(Qt.Key_Ampersand, "&")
_set_key(Qt.Key_Apostrophe, "'")
_set_key(Qt.Key_ParenLeft, "(")
_set_key(Qt.Key_ParenRight, ")")
_set_key(Qt.Key_Asterisk, "*")
_set_key(Qt.Key_Plus, "+")
_set_key(Qt.Key_Comma, ",")
_set_key(Qt.Key_Minus, "-")
_set_key(Qt.Key_Period, ".")
_set_key(Qt.Key_Slash, "/")

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

_set_key(Qt.Key_Colon, ":")
_set_key(Qt.Key_Semicolon, ";")
_set_key(Qt.Key_Less, "<")
_set_key(Qt.Key_Equal, "=")
_set_key(Qt.Key_Greater, ">")
_set_key(Qt.Key_Question, "?")
_set_key(Qt.Key_At, "@")

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

_set_key(Qt.Key_BracketLeft, "[")
_set_key(Qt.Key_Backslash, "\\")
_set_key(Qt.Key_BracketRight, "]")
_set_key(Qt.Key_AsciiCircum, "^")
_set_key(Qt.Key_Underscore, "_")
_set_key(Qt.Key_Underscore, "_")
# _set_key(Qt.Key_QuoteLeft, "")
_set_key(Qt.Key_BraceLeft, "{")
_set_key(Qt.Key_Bar, "|")
_set_key(Qt.Key_BraceRight, "}")
_set_key(Qt.Key_AsciiTilde, "~")
_set_key(Qt.Key_nobreakspace, " ")
_set_key(Qt.Key_nobreakspace, " ")
_set_key(Qt.Key_exclamdown, "¡")
_set_key(Qt.Key_cent, "¢")
_set_key(Qt.Key_sterling, "£")
_set_key(Qt.Key_currency, "¤")
_set_key(Qt.Key_yen, "¥")
_set_key(Qt.Key_brokenbar, "¦")
_set_key(Qt.Key_section, "§")
_set_key(Qt.Key_diaeresis, "¨")
_set_key(Qt.Key_copyright, "©")
_set_key(Qt.Key_ordfeminine, "ª")
_set_key(Qt.Key_guillemotleft, "«")
_set_key(Qt.Key_notsign, "¬")
# _set_key(Qt.Key_hyphen, "")
_set_key(Qt.Key_registered, "®")
_set_key(Qt.Key_macron, "¯")
_set_key(Qt.Key_degree, "°")
_set_key(Qt.Key_plusminus, "±")
_set_key(Qt.Key_twosuperior, "²")
_set_key(Qt.Key_threesuperior, "³")
_set_key(Qt.Key_acute, "´")
_set_key(Qt.Key_mu, "µ")
_set_key(Qt.Key_paragraph, "¶")
_set_key(Qt.Key_periodcentered, "·")
_set_key(Qt.Key_cedilla, "¸")
_set_key(Qt.Key_onesuperior, "¹")
_set_key(Qt.Key_masculine, "º")
_set_key(Qt.Key_guillemotright, "»")
_set_key(Qt.Key_onequarter, "¼")
_set_key(Qt.Key_onehalf, "½")
_set_key(Qt.Key_threequarters, "¾")
_set_key(Qt.Key_questiondown, "¿")
_set_key(Qt.Key_Agrave, "à", "À")
_set_key(Qt.Key_Aacute, "á", "Á")
_set_key(Qt.Key_Acircumflex, "â", "Â")
_set_key(Qt.Key_Atilde, "ã", "Ã")
_set_key(Qt.Key_Adiaeresis, "ä", "Ä")
_set_key(Qt.Key_Aring, "å", "Å")
_set_key(Qt.Key_AE, "æ", "Æ")
_set_key(Qt.Key_Ccedilla, "ç", "Ç")
_set_key(Qt.Key_Egrave, "è", "È")
_set_key(Qt.Key_Eacute, "é", "É")
_set_key(Qt.Key_Ecircumflex, "ê", "Ê")
_set_key(Qt.Key_Ediaeresis, "Ë", "ë")
_set_key(Qt.Key_Igrave, "ì", "Ì")
_set_key(Qt.Key_Iacute, "í", "Í")
_set_key(Qt.Key_Icircumflex, "î", "Î")
_set_key(Qt.Key_Idiaeresis, "ï", "Ï")
_set_key(Qt.Key_ETH, "Ð")
_set_key(Qt.Key_Ntilde, "ñ", "Ñ")
_set_key(Qt.Key_Ograve, "ò", "Ò")
_set_key(Qt.Key_Oacute, "ó", "Ó")
_set_key(Qt.Key_Ocircumflex, "ô", "Ô")
_set_key(Qt.Key_Odiaeresis, "ö", "Ö")
_set_key(Qt.Key_multiply, "×")
_set_key(Qt.Key_Ooblique, "Ø", "ø")
_set_key(Qt.Key_Ugrave, "ù", "Ù")
_set_key(Qt.Key_Uacute, "ú", "Ú")
_set_key(Qt.Key_Ucircumflex, "û", "Û")
_set_key(Qt.Key_Udiaeresis, "ü", "Ü")
_set_key(Qt.Key_Yacute, "ý", "Ý")
_set_key(Qt.Key_THORN, "þ", "Þ")


def is_one_letter_upcase(char):
    return len(char) == 1 and char.isalpha() and char.isupper()


_KeyPress = namedtuple("_KeyPress", ("key", "control_modifier", "alt_modifier",
                                     "super_modifier", "is_upper_case"))


class KeyPress(_KeyPress):
    @classmethod
    def from_qevent(cls, event):
        text = event.text()

        # Try to get the key value depending on the text. Despite what the qt
        # doc says, it seems more reliable to get the good value this way. For
        # example, to match C-? on my french keyboard (using the bépo layout)
        # this is required (Ctrl-Shift-'), else event.key() is equal to the key
        # DOWN.
        key = CHAR2KEY.get(text)
        if key is None:
            key = event.key()
            if key not in KEY2CHAR:
                return None

        modifiers = event.modifiers()

        return cls(
            key,
            bool(modifiers & Qt.ControlModifier),
            bool(modifiers & Qt.AltModifier),
            bool(modifiers & Qt.MetaModifier),
            is_one_letter_upcase(text)
        )

    @classmethod
    def from_str(cls, string):
        ctrl, alt, super = False, False, False
        left, _, text = string.rpartition("-")
        if text == "":
            text = "-"
        parts = left.split("-")
        for p in parts:
            if p == "":
                break
            elif p == "C":
                ctrl = True
            elif p == "M":
                alt = True
            elif p == "S":
                super = True
            else:
                raise Exception(
                    "Unknown key modifier: %s in key definition %s"
                    % (p, string)
                )

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

    def has_any_modifier(self):
        return (self.control_modifier or self.alt_modifier
                or self.super_modifier)

    def char(self):
        char = KEY2CHAR[self.key]
        if self.is_upper_case:
            return char.upper()
        return char

    def __str__(self):
        keyrepr = []

        if self.control_modifier:
            keyrepr.append("C")
        if self.alt_modifier:
            keyrepr.append("M")
        if self.super_modifier:
            keyrepr.append("S")

        keyrepr.append(self.char())

        return "-".join(keyrepr)

    def __repr__(self):
        return "<%s (%s)>" % (self.__class__.__name__, str(self))


KeymapLookupResult = namedtuple("KeymapLookupResult",
                                ("complete", "command", "keymap"))


class InternalKeymap(object):
    __slots__ = ("bindings", "parent")

    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent

    def _traverse_commands(self, prefix, acc_fn):
        for keypress, cmd in self.bindings.items():
            new_prefix = prefix + [keypress]
            if isinstance(cmd, InternalKeymap):
                cmd._traverse_commands(new_prefix, acc_fn)
            else:
                acc_fn(new_prefix, cmd)
        if self.parent:
            for keypress, cmd in self.parent.bindings.items():
                if keypress not in self.bindings:
                    new_prefix = prefix + [keypress]
                    if isinstance(cmd, InternalKeymap):
                        cmd._traverse_commands(new_prefix, acc_fn)
                    else:
                        acc_fn(new_prefix, cmd)

    def traverse_commands(self, acc_fn):
        self._traverse_commands([], acc_fn)

    def all_bindings(self, raw_fn=False):
        """
        Returns the list of bindings as (keychord, command-name) tuples.
        """
        acc = []

        def add(prefix, cmd):
            if isinstance(cmd, str):
                acc.append((" ".join(str(k) for k in prefix), cmd))
            elif raw_fn:
                acc.append((" ".join(str(k) for k in prefix), cmd.__name__))
        self.traverse_commands(add)
        return acc

    def _define_key(self, key, binding):
        keys = [KeyPress.from_str(k) for k in key.split()]
        assert keys, "key should not be empty"
        assert callable(binding) or isinstance(binding, str), \
            "binding should be callable or a command name"

        kmap = self
        for keypress in keys[:-1]:
            if keypress in kmap.bindings:
                othermap = kmap.bindings[keypress]
                if not isinstance(othermap, InternalKeymap):
                    othermap = InternalKeymap()
            else:
                othermap = InternalKeymap()
            kmap.bindings[keypress] = othermap
            kmap = othermap

        kmap.bindings[keys[-1]] = binding

    def define_key(self, key, binding=None):
        """
        Define a binding (callable or command name) for a key chord.

        :param key: a string representing the key chord, such as "C-c x".
        :param binding: A command name (a string), a callable, or None.
                        If None, it must be used as a function decorator.
        """
        if binding is None:
            def wrapper(func):
                self._define_key(key, func)
                return func
            return wrapper
        else:
            self._define_key(key, binding)

    def undefine_key(self, key):
        """
        Undefine the binding under a key chord.

        :param key: a string representing the key chord, such as "C-c x".
        """
        keys = [KeyPress.from_str(k) for k in key.split()]
        if not keys:
            return None
        res = self.lookup(keys)
        if res is not None and res.complete:
            del res.keymap.bindings[keys[-1]]
            return res.keymap
        return None

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
                    if isinstance(entry, InternalKeymap):
                        keymap = entry
                        partial_match = True
                        break
                    else:
                        return KeymapLookupResult(True, entry, keymap)
                keymap = keymap.parent

        if keymap is None:
            return None
        elif partial_match:
            return KeymapLookupResult(False, None, keymap)
        else:
            return None


class Keymap(InternalKeymap):
    __slots__ = InternalKeymap.__slots__ + ("name", "doc")

    def __init__(self, name, parent=None, doc=None):
        InternalKeymap.__init__(self, parent=parent)
        self.name = name
        self.doc = doc
        if self.name in KEYMAPS:
            raise ValueError("A keymap named %s already exists."
                             % self.name)
        KEYMAPS[self.name] = self

    def __str__(self):
        return self.name

    @property
    def brief_doc(self):
        if self.doc:
            return self.doc.split("\n", 1)[0]


EMPTY_KEYMAP = Keymap("empty")

GLOBAL_KEYMAP = Keymap("global", doc="""\
The global keymap is always active.

It act as a fallback to other keymaps, which are considered local. Only one
local keymap can be active at a time. A binding is first searched in the
currently active local keymap, and if not found the global keymap is used.

Only bindings with modifiers should be bound to it, else it will be impossible
to edit text inside the browser.""")

BUFFER_KEYMAP = Keymap("webbuffer", doc="""\
Local keymap activated when a web buffer is focused.\

A web buffer is focused when there is no text editing, no caret browsing, or
when the minibuffer input is not shown... It is enabled when no other local
keymap is enabled.""")

CONTENT_EDIT_KEYMAP = Keymap("webcontent-edit", doc="""\
Local keymap activated when a webcontent field (input, textarea, ...) is \
focused.""")

CARET_BROWSING_KEYMAP = Keymap("caret-browsing", doc="""\
Local keymap activated when you are navigating the webbuffer with a caret.\
""")

FULLSCREEN_KEYMAP = Keymap("video-fullscreen", doc="""\
Local Keymap activated when a video is played full screen.
""")


def global_keymap():
    """
    Returns the global :class:`Keymap`.

    It is almost always active, and act as a fallback if there is
    an active keymap.
    """
    warnings.warn(
        "global_keymap() is deprecated, use keymap('global') instead",
        DeprecationWarning
    )
    return GLOBAL_KEYMAP


def webbuffer_keymap():
    """
    Returns the :class:`Keymap` associated to web buffers.

    This keymap is active when there is no focus for an editable
    element in web contents.
    """
    warnings.warn(
        "webbuffer_keymap() is deprecated, use keymap('webbuffer') instead",
        DeprecationWarning
    )
    return BUFFER_KEYMAP


def content_edit_keymap():
    """
    Returns the :class:`Keymap` associated to content editing.

    Local keymap activated when a webcontent field (input, textarea,
    ...) is focused
    """
    warnings.warn(
        "content_edit_keymap() is deprecated, use keymap('webcontent-edit')"
        " instead",
        DeprecationWarning
    )
    return CONTENT_EDIT_KEYMAP


def keymap(name):
    """Get a keymap given its name."""
    return KEYMAPS[name]
