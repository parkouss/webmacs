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
import logging
import os

from .import BUFFERS, windows
from .webbuffer import create_buffer, QUrl, DelayedLoadingUrl
from .window import Window


FORMAT_VERSION = 1


def _session_load(stream):
    data = json.load(stream)
    version = data.get("version", 0)
    urls = data["urls"]

    # apply the session config

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

    if version > 0:
        # only one window supported for now
        wdata = data["windows"][0]
        cwin = Window()
        cwin.restore_state(wdata, version)
        cwin.show()
    else:
        cwin = Window()
        cwin.showMaximized()

    # and open the first buffer in the view
    if BUFFERS:
        cwin.current_webview().setBuffer(BUFFERS[0])


def _session_save(stream):
    urls = [{
        "url": b.url().toString(),
        "title": b.title()
    } for b in BUFFERS]

    json.dump({
        "version": FORMAT_VERSION,
        "urls": urls,
        "windows": [w.dump_state() for w in windows()]
    }, stream)


def session_load(profile, opts):
    """
    Try to load the session, given the profile.

    Must be called at application startup, when no buffers nor views is set up
    already.
    """
    if os.path.exists(profile.session_file):
        try:
            with open(profile.session_file, "r") as f:
                _session_load(f)
                return True
        except Exception:
            logging.exception("Unable to load the session (%s)",
                              profile.session_file)
    window = Window()
    buffer = create_buffer(opts.url or "http://duckduckgo.com/")
    window.current_webview().setBuffer(buffer)
    window.showMaximized()


def session_save(profile):
    """
    Save the session for the given profile.
    """
    with open(profile.session_file, "w") as f:
        _session_save(f)
