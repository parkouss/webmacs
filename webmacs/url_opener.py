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

from .webbuffer import create_buffer
from .window import Window


def url_open(ctx, url, instance=None, new_window=False, new_buffer=False):
    """
    Open an url.
    """
    assert instance is None  # TODO FIXME implement later

    buffer = None

    if new_buffer or new_window:
        buffer = create_buffer()
        if new_window:
            w = Window()
            w.current_webview().setBuffer(buffer)
            buffer.load(url)  # load before showing
            w.show()
            w.activateWindow()
            return
        else:
            ctx.view.setBuffer(buffer)
    else:
        buffer = ctx.buffer

    buffer.load(url)
