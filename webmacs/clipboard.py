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

from PyQt5.QtGui import QClipboard

from . import variables, minibuffer_show_info


_CLIPBOARD = None
_COPY_MODE = None


def _clipboard():
    global _CLIPBOARD
    if _CLIPBOARD is None:
        from .application import app
        _CLIPBOARD = app().clipboard()
    return _CLIPBOARD


class Mode:
    PRIMARY = 1 << 0
    SELECTION = 1 << 1
    BOTH = PRIMARY | SELECTION

    _from_str = {
        "primary": PRIMARY,
        "selection": SELECTION,
        "both": BOTH,
    }


def _copy_mode_from_var(v):
    global _COPY_MODE
    _COPY_MODE = Mode._from_str[v.value]


clipboard_copy = variables.define_variable(
    "clipboard-copy",
    "Where to copy text. Allowed values are 'primary', 'selection' or 'both'"
    " Defaults to primary, which is the global clipboard. selection is for"
    " clipboard mouse selection, and both will copy to both clipboards.",
    "primary",
    type=variables.String(choices=tuple(Mode._from_str.keys())),
    callbacks=(_copy_mode_from_var,)
)

_copy_mode_from_var(clipboard_copy)


def set_text(text, mode=None):
    cb = _clipboard()
    if mode is None:
        mode = _COPY_MODE

    if mode & Mode.PRIMARY:
        cb.setText(text)

    if mode & Mode.SELECTION:
        cb.setText(text, QClipboard.Selection)

    minibuffer_show_info("Copied: {}".format(text))
