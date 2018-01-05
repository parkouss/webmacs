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

from . import Keymap

KEYMAP = Keymap("Caret Browsing")


KEYMAP.define_key("C-n", "caret-browsing-down")
KEYMAP.define_key("n", "caret-browsing-down")
KEYMAP.define_key("Down", "caret-browsing-down")
KEYMAP.define_key("C-p", "caret-browsing-up")
KEYMAP.define_key("p", "caret-browsing-up")
KEYMAP.define_key("Up", "caret-browsing-up")
KEYMAP.define_key("C-g", "caret-browsing-shutdown")
KEYMAP.define_key("Esc", "caret-browsing-shutdown")
KEYMAP.define_key("C-f", "caret-browsing-forward-char")
KEYMAP.define_key("f", "caret-browsing-forward-char")
KEYMAP.define_key("Right", "caret-browsing-forward-char")
KEYMAP.define_key("C-b", "caret-browsing-backward-char")
KEYMAP.define_key("b", "caret-browsing-backward-char")
KEYMAP.define_key("Left", "caret-browsing-backward-char")
KEYMAP.define_key("M-f", "caret-browsing-forward-word")
KEYMAP.define_key("C-Right", "caret-browsing-forward-word")
KEYMAP.define_key("M-b", "caret-browsing-backward-word")
KEYMAP.define_key("C-Left", "caret-browsing-backward-word")
KEYMAP.define_key("C-Space", "caret-browsing-toggle-mark")
KEYMAP.define_key("M-w", "caret-browsing-cut")
KEYMAP.define_key("C-a", "caret-browsing-beginning-of-line")
KEYMAP.define_key("C-e", "caret-browsing-end-of-line")
KEYMAP.define_key("M-<", "caret-browsing-beginning-of-document")
KEYMAP.define_key("M->", "caret-browsing-end-of-document")
KEYMAP.define_key("M-{", "caret-browsing-backward-paragraph")
KEYMAP.define_key("M-}", "caret-browsing-forward-paragraph")
KEYMAP.define_key("C-s", "i-search-forward")
KEYMAP.define_key("C-r", "i-search-backward")
