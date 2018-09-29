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


def call_js(ctx, script):
    ctx.buffer.runJavaScript(script, QWebEngineScript.ApplicationWorld)


@define_command("caret-browsing-init")
def init(ctx):
    """
    Init caret browsing in the current buffer.
    """
    call_js(ctx, "CaretBrowsing.setInitialCursor();")


@define_command("caret-browsing-shutdown")
def shutdown(ctx):
    """
    Shutdown caret browsing in current buffer.
    """
    call_js(ctx, "CaretBrowsing.shutdown();")


@define_command("caret-browsing-down")
def down(ctx):
    """
    Move the caret down a line.
    """
    call_js(ctx, "CaretBrowsing.move('forward', 'line');")


@define_command("caret-browsing-up")
def up(ctx):
    """
    Move the caret up a line.
    """
    call_js(ctx, "CaretBrowsing.move('backward', 'line');")


@define_command("caret-browsing-backward-char")
def left_char(ctx):
    """
    Move the caret one character backward.
    """
    call_js(ctx, "CaretBrowsing.move('backward', 'character');")


@define_command("caret-browsing-backward-word")
def left_word(ctx):
    """
    Move the caret one word backward.
    """
    call_js(ctx, "CaretBrowsing.move('backward', 'word');")


@define_command("caret-browsing-forward-char")
def right_char(ctx):
    """
    Move the caret one character forward.
    """
    call_js(ctx, "CaretBrowsing.move('forward', 'character');")


@define_command("caret-browsing-forward-word")
def right_word(ctx):
    """
    Move the caret one word forward.
    """
    call_js(ctx, "CaretBrowsing.move('forward', 'word');")


@define_command("caret-browsing-toggle-mark")
def toggle_mark(ctx):
    """
    Set or unset (toggle) the mark where the point is.
    """
    call_js(ctx, "CaretBrowsing.toggleMark();")


@define_command("caret-browsing-cut")
def copy(ctx):
    """
    Cut the current caret selection.
    """
    call_js(ctx, "CaretBrowsing.cutSelection();")


@define_command("caret-browsing-end-of-line")
def end_of_line(ctx):
    """
    Move the caret to the end of the current line.
    """
    call_js(ctx, "CaretBrowsing.move('forward', 'lineboundary');")


@define_command("caret-browsing-beginning-of-line")
def beginning_of_line(ctx):
    """
    Move the caret to the beginning of the current line.
    """
    call_js(ctx, "CaretBrowsing.move('backward', 'lineboundary');")


@define_command("caret-browsing-end-of-document")
def end_of_document(ctx):
    """
    Move the caret to the end of the document.
    """
    call_js(ctx, "CaretBrowsing.move('forward', 'documentboundary');")


@define_command("caret-browsing-beginning-of-document")
def beginning_of_document(ctx):
    """
    Move the caret to the beginning of the document.
    """
    call_js(ctx, "CaretBrowsing.move('backward', 'documentboundary');")


@define_command("caret-browsing-forward-paragraph")
def forward_paragraph(ctx):
    """
    Move the caret to the next paragraph (TODO FIXME not working yet)
    """
    call_js(ctx, "CaretBrowsing.move('forward', 'paragraphboundary');")


@define_command("caret-browsing-backward-paragraph")
def backward_paragraph(ctx):
    """
    Move the caret to the previous paragraph (TODO FIXME not working yet)
    """
    call_js(ctx, "CaretBrowsing.move('backward', 'paragraphboundary');")
