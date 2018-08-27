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

from .import BUFFERS, windows, current_window
from .webbuffer import create_buffer, QUrl, DelayedLoadingUrl, close_buffer
from .window import Window


FORMAT_VERSION = 2


def _session_load(stream):
    data = json.load(stream)
    version = data.get("version", 0)
    urls = data["urls"]
    if version < 2:
        urls = reversed(urls)

    # apply the session config

    # now, load urls in buffers
    for url in urls:
        if isinstance(url, str):
            # old format, no delay loading support
            # TODO must be removed after some time
            create_buffer(url)
        else:
            # new format, url must be a dict
            buff = create_buffer(DelayedLoadingUrl(
                url=QUrl(url["url"]),
                title=url["title"]
            ))
            if version >= 2:
                buff.last_use = url["last_use"]

    if version > 0:
        def create_window(wdata):
            win = Window()
            win.restore_state(wdata, version)
            win.show()

        current_index = data.get("current-window", 0)
        for i, wdata in enumerate(data["windows"]):
            if i != current_index:
                create_window(wdata)

        # create the current last, so it has focus and is on top
        create_window(data["windows"][current_index])

    else:
        cwin = Window()
        cwin.showMaximized()

        # and open the first buffer in the view
        if BUFFERS:
            cwin.current_webview().setBuffer(BUFFERS[0])


def _session_save(stream):
    urls = [{
        "url": b.url().toString(),
        "title": b.title(),
        "last_use": b.last_use,
    } for b in BUFFERS]

    json.dump({
        "version": FORMAT_VERSION,
        "urls": urls,
        "windows": [w.dump_state() for w in windows()],
        "current-window": windows().index(current_window()),
    }, stream)


def session_clean():
    # clean every opened buffers and windows
    for window in windows():
        window.quit_if_last_closed = False
        window.close()
        for view in window.webviews():
            view.setBuffer(None)

    for buffer in BUFFERS:
        close_buffer(buffer)


def session_load(session_file):
    """
    Try to load the session, given the profile.

    Must be called at application startup, when no buffers nor views is set up
    already.
    """
    try:
        with open(session_file, "r") as f:
            _session_load(f)
    except Exception:
        logging.exception("Unable to load the session from %s.",
                          session_file)
        session_clean()
        raise


def session_save(session_file):
    """
    Save the session for the given profile.
    """
    with open(session_file, "w") as f:
        _session_save(f)
