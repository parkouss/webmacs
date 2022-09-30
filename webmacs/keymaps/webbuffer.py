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

from . import BUFFER_KEYMAP as KEYMAP


KEYMAP.define_key("g", "go-to")
KEYMAP.define_key("s", "search-default")
KEYMAP.define_key("G", "go-to-alternate-url")
KEYMAP.define_key("b", "buffer-history")
KEYMAP.define_key("F", "go-forward")
KEYMAP.define_key("B", "go-backward")
KEYMAP.define_key("C-s", "i-search-forward")
KEYMAP.define_key("C-r", "i-search-backward")
KEYMAP.define_key("C-v", "scroll-page-down")
KEYMAP.define_key("M-v", "scroll-page-up")
KEYMAP.define_key("M->", "scroll-bottom")
KEYMAP.define_key("M-<", "scroll-top")
KEYMAP.define_key("f", "follow")
KEYMAP.define_key("c l", "copy-link")
KEYMAP.define_key("c c", "copy-current-link")
KEYMAP.define_key("c t", "copy-current-buffer-title")
KEYMAP.define_key("c u", "copy-current-buffer-url")
KEYMAP.define_key("M-w", "webcontent-copy")
KEYMAP.define_key("r", "reload-buffer")
KEYMAP.define_key("R", "reload-buffer-no-cache")
KEYMAP.define_key("h", "visited-links-history")
KEYMAP.define_key("q", "close-buffer")
KEYMAP.define_key("C-x h", "select-buffer-content")
KEYMAP.define_key("C", "caret-browsing-init")
KEYMAP.define_key("m", "bookmark-open")
KEYMAP.define_key("M", "bookmark-add")
KEYMAP.define_key("C-+", "text-zoom-in")
KEYMAP.define_key("C--", "text-zoom-out")
KEYMAP.define_key("C-=", "text-zoom-reset")
KEYMAP.define_key("+", "zoom-in")
KEYMAP.define_key("-", "zoom-out")
KEYMAP.define_key("=", "zoom-normal")
KEYMAP.define_key("C-n", "send-key-down")
KEYMAP.define_key("n", "send-key-down")
KEYMAP.define_key("C-p", "send-key-up")
KEYMAP.define_key("p", "send-key-up")
KEYMAP.define_key("P", "password-manager-fill-buffer")
KEYMAP.define_key("C-f", "send-key-right")
KEYMAP.define_key("C-b", "send-key-left")
KEYMAP.define_key("C-g", "buffer-escape")
KEYMAP.define_key("C-x p", "print-buffer")
