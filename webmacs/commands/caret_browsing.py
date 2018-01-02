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
from .webbuffer import current_buffer, WebBuffer


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
    call_js("CaretBrowsing.move('forward', 'line');")


@define_command("caret-browsing-up")
def up():
    call_js("CaretBrowsing.move('backward', 'line');")


@define_command("caret-browsing-left-char")
def left_char():
    call_js("CaretBrowsing.move('backward', 'character');")


@define_command("caret-browsing-left-word")
def left_word():
    call_js("CaretBrowsing.move('backward', 'word');")


@define_command("caret-browsing-right-char")
def right_char():
    call_js("CaretBrowsing.move('forward', 'character');")


@define_command("caret-browsing-right-word")
def right_word():
    call_js("CaretBrowsing.move('forward', 'word');")


@define_command("caret-browsing-toggle-mark")
def toggle_mark():
    call_js("CaretBrowsing.toggleMark();")


@define_command("caret-browsing-cut")
def copy():
    call_js("CaretBrowsing.cutSelection();")


@define_command("caret-browsing-end-of-line")
def end_of_line():
    call_js("CaretBrowsing.move('forward', 'lineboundary');")


@define_command("caret-browsing-beginning-of-line")
def beginning_of_line():
    call_js("CaretBrowsing.move('backward', 'lineboundary');")


@define_command("caret-browsing-end-of-document")
def end_of_document():
    call_js("CaretBrowsing.move('forward', 'documentboundary');")


@define_command("caret-browsing-beginning-of-document")
def beginning_of_document():
    call_js("CaretBrowsing.move('backward', 'documentboundary');")


@define_command("caret-browsing-forward-paragraph")
def forward_paragraph():
    call_js("CaretBrowsing.move('forward', 'paragraphboundary');")


@define_command("caret-browsing-backward-paragraph")
def backward_paragraph():
    call_js("CaretBrowsing.move('backward', 'paragraphboundary');")
