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

from . import FULLSCREEN_KEYMAP
from .. import current_window

from PyQt5.QtWebEngineWidgets import QWebEnginePage


@FULLSCREEN_KEYMAP.define_key("q")
@FULLSCREEN_KEYMAP.define_key("C-g")
@FULLSCREEN_KEYMAP.define_key("Esc")
def exit_full_screen(ctx):
    fw = current_window().fullscreen_window
    if fw:
        fw.internal_view.triggerPageAction(QWebEnginePage.ExitFullScreen)
