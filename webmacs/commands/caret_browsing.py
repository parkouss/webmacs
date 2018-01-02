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

from PyQt5.QtWebEngineWidgets import QWebEngineScript

from . import define_command
from .webbuffer import current_buffer


def call_js(script):
    current_buffer().runJavaScript(script, QWebEngineScript.ApplicationWorld)


@define_command("caret-browsing-init")
def init():
    call_js("CaretBrowsing.setInitialCursor();")


@define_command("caret-browsing-shutdown")
def shutdown():
    call_js("CaretBrowsing.toggle(false);")


@define_command("caret-browsing-down")
def down():
    call_js("CaretBrowsing.moveDown();")


@define_command("caret-browsing-up")
def up():
    call_js("CaretBrowsing.moveUp();")
