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

from ..keymaps import global_keymap

KEYMAP = global_keymap()


KEYMAP.define_key("C-x C-c", "quit")
KEYMAP.define_key("M-x", "M-x")
KEYMAP.define_key("C-x C-f", "go-to-new-buffer")
KEYMAP.define_key("C-x b", "switch-buffer")
KEYMAP.define_key("C-x o", "other-view")
KEYMAP.define_key("C-x 3", "split-view-right")
KEYMAP.define_key("C-x 2", "split-view-bottom")
KEYMAP.define_key("C-x 0", "close-view")
KEYMAP.define_key("C-x 1", "maximise-view")
KEYMAP.define_key("C-x k", "close-buffer")
KEYMAP.define_key("C-h v", "describe-variable")
KEYMAP.define_key("C-h c", "describe-command")
