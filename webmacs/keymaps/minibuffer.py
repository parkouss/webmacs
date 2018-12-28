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

from . import MINIBUFFER_KEYMAP as KEYMAP


KEYMAP.define_key("Tab", "minibuffer-select-complete")
KEYMAP.define_key("C-n", "minibuffer-select-next")
KEYMAP.define_key("Down", "minibuffer-select-next")
KEYMAP.define_key("C-p", "minibuffer-select-prev")
KEYMAP.define_key("Up", "minibuffer-select-prev")
KEYMAP.define_key("M-<", "minibuffer-select-first")
KEYMAP.define_key("M->", "minibuffer-select-last")
KEYMAP.define_key("C-v", "minibuffer-select-next-page")
KEYMAP.define_key("M-v", "minibuffer-select-prev-page")
KEYMAP.define_key("M-n", "minibuffer-history-next")
KEYMAP.define_key("M-p", "minibuffer-history-prev")
KEYMAP.define_key("Return", "minibuffer-validate")
KEYMAP.define_key("C-g", "minibuffer-abort")
KEYMAP.define_key("Esc", "minibuffer-abort")
KEYMAP.define_key("M-Backspace", "minibuffer-delete-backward-word")
KEYMAP.define_key("C-Space", "minibuffer-mark")
KEYMAP.define_key("C-f", "minibuffer-forward-char")
KEYMAP.define_key("Right", "minibuffer-forward-char")
KEYMAP.define_key("C-b", "minibuffer-backward-char")
KEYMAP.define_key("Left", "minibuffer-backward-char")
KEYMAP.define_key("M-f", "minibuffer-forward-word")
KEYMAP.define_key("M-Right", "minibuffer-forward-word")
KEYMAP.define_key("M-b", "minibuffer-backward-word")
KEYMAP.define_key("M-Left", "minibuffer-backward-word")
KEYMAP.define_key("M-w", "minibuffer-copy")
KEYMAP.define_key("C-w", "minibuffer-cut")
KEYMAP.define_key("C-y", "minibuffer-paste")
KEYMAP.define_key("C-d", "minibuffer-delete-forward-char")
KEYMAP.define_key("M-d", "minibuffer-delete-forward-word")
KEYMAP.define_key("C-a", "minibuffer-beginning-of-line")
KEYMAP.define_key("C-e", "minibuffer-end-of-line")
KEYMAP.define_key("C-/", "minibuffer-undo")
KEYMAP.define_key("C-?", "minibuffer-undo")
