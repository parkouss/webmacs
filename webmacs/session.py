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

import json

from .import BUFFERS, current_window, windows
from .webbuffer import (create_buffer, close_buffer, QUrl,
                        DelayedLoadingUrl)


def session_load(stream):
    data = json.load(stream)
    urls = data["urls"]

    # apply the session config
    cwin = current_window()

    # close any opened window other than the current one
    for win in windows():
        if win != cwin:
            win.close()

    # close any webview except the current one
    cwin.close_other_views()

    # and close all the buffers
    for buff in BUFFERS:
        close_buffer(buff, keep_one=False)

    # now, load urls in buffers
    for url in reversed(urls):
        if isinstance(url, str):
            # old format, no delay loading support
            # TODO must be removed after some time
            create_buffer(url)
        else:
            # new format, url must be a dict
            create_buffer(DelayedLoadingUrl(
                url=QUrl(url["url"]),
                title=url["title"]
            ))

    # and open the first buffer in the view
    if BUFFERS:
        cwin.current_web_view().setBuffer(BUFFERS[0])


def session_save(stream):
    urls = [{
        "url": b.url().toString(),
        "title": b.title()
    } for b in BUFFERS]

    json.dump({"urls": urls}, stream)
