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

import re

from .keymaps import BUFFER_KEYMAP, CONTENT_EDIT_KEYMAP, \
    CARET_BROWSING_KEYMAP, EMPTY_KEYMAP, FULLSCREEN_KEYMAP

from . import variables


MODES = {}


class Mode(object):
    KEYMAP_NORMAL = 1
    KEYMAP_CONTENT_EDIT = 2
    KEYMAP_CARET_BROWSING = 3
    KEYMAP_FULLSCREEN = 4

    def __init__(self, name, description):
        self.name = name
        self.description = description
        self._mode_to_km = {
            self.KEYMAP_NORMAL: self.keymap,
            self.KEYMAP_CONTENT_EDIT: self.content_edit_keymap,
            self.KEYMAP_CARET_BROWSING: self.caret_browsing_keymap,
            self.KEYMAP_FULLSCREEN: self.fullscreen_keymap,
        }

    def keymap(self):
        return BUFFER_KEYMAP

    def content_edit_keymap(self):
        return CONTENT_EDIT_KEYMAP

    def caret_browsing_keymap(self):
        return CARET_BROWSING_KEYMAP

    def keymap_for_mode(self, mode):
        return self._mode_to_km[mode]()

    def fullscreen_keymap(self):
        return FULLSCREEN_KEYMAP

    def __str__(self):
        return self.name


def get_mode(name):
    return MODES[name]


def define_mode(mode):
    assert mode.name not in MODES
    MODES[mode.name] = mode


define_mode(Mode("standard-mode", "standard navigation mode"))


class EmptyMode(Mode):

    def keymap(self):
        return EMPTY_KEYMAP

    content_edit_keymap = keymap
    caret_browsing_keymap = keymap
    fullscreen_keymap = keymap


define_mode(EmptyMode("no-keybindings", "no-keybindings navigation mode"))


AUTO_MODES = []


def get_auto_modename_for_url(url, default="standard-mode"):
    for reg, mode in AUTO_MODES:
        if reg.match(url):
            return mode

    return default


def _set_auto_buffer_modes(modes):
    global AUTO_MODES
    AUTO_MODES = [((
        re.compile(reg) if isinstance(reg, str) else reg),
        mode
    ) for reg, mode in modes.value]


auto_buffer_modes = variables.define_variable(
    "auto-buffer-modes",
    "List of tuple of regexes and mode name to automatically associate"
    " web pages to some mode. If nothing matches the url, standard-mode is"
    " used.",
    (),
    conditions=(
        variables.condition(
            lambda v: isinstance(v, (tuple, list))
            and all(isinstance(e, tuple) for e in v)
            and all((isinstance(e[0], str) or hasattr(e[0], "match"))
                    and e[1] in MODES for e in v),
            "Must be a list of tuple (regexes, modename)."),
    ),
    callbacks=(
        _set_auto_buffer_modes,
    ),
)
