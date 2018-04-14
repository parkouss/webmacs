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

from . import CONTENT_EDIT_KEYMAP as KEYMAP


KEYMAP.define_key("C-g", "content-edit-cancel")
KEYMAP.define_key("C-n", "send-key-down")
KEYMAP.define_key("C-p", "send-key-up")
KEYMAP.define_key("C-Space", "content-edit-set-mark")
KEYMAP.define_key("C-f", "content-edit-forward-char")
KEYMAP.define_key("C-b", "content-edit-backward-char")
KEYMAP.define_key("M-f", "content-edit-forward-word")
KEYMAP.define_key("M-b", "content-edit-backward-word")
KEYMAP.define_key("C-a", "content-edit-beginning-of-line")
KEYMAP.define_key("C-e", "content-edit-end-of-line")
KEYMAP.define_key("C-d", "content-edit-delete-forward-char")
KEYMAP.define_key("M-d", "content-edit-delete-forward-word")
KEYMAP.define_key("M-Backspace", "content-edit-delete-backward-word")
KEYMAP.define_key("M-w", "content-edit-copy")
KEYMAP.define_key("C-w", "content-edit-cut")
KEYMAP.define_key("C-y", "webcontent-paste")
KEYMAP.define_key("M-u", "content-edit-upcase-forward-word")
KEYMAP.define_key("M-l", "content-edit-downcase-forward-word")
KEYMAP.define_key("M-c", "content-edit-capitalize-forward-word")
KEYMAP.define_key("C-x e", "content-edit-open-external-editor")
KEYMAP.define_key("C-x C-e", "content-edit-open-external-editor")
