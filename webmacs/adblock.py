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

import os
import logging
import time
import json

from datetime import datetime, timezone
import dateparser

from _adblock import AdBlock
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request
from . import variables
from .task import Task

from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply
from PyQt6.QtCore import QUrl, QThreadPool, pyqtSignal as Signal, Qt


DEFAULT_EASYLIST = [
    "https://easylist.to/easylist/easylist.txt",
    # easyprivacy blocks too much right now
    # "https://easylist.to/easylist/easyprivacy.txt",
    "https://easylist.to/easylist/fanboy-annoyance.txt"
]

adblock_urls_rules = variables.define_variable(
    "adblock-urls-rules",
    "A list of urls to get rules for ad-blocking (using the Adblock format)."
    " The default urls are taken from the easylist site https://easylist.to.",
    DEFAULT_EASYLIST,
    type=variables.List(variables.String()),
)


def cache_file(cache_path):
    return os.path.join(cache_path, "cache.dat")


class AdBlockUpdateTask(Task):
    adblock_ready = Signal(AdBlock)

    def __init__(self, app, cache_path, ):
        Task.__init__(self)
        self.app = app
        if not os.path.isdir(cache_path):
            os.makedirs(cache_path)
        self._cache_path = cache_path
        self._cached_urls_path = os.path.join(self._cache_path, "urls.json")
        self._cache_file = cache_file(cache_path)
        self._user_urls = {
            url: os.path.join(self._cache_path, url.rsplit("/", 1)[-1])
            for url in adblock_urls_rules.value
        }

        self.adblock_ready.connect(self._on_adblock_ready,
                                   Qt.ConnectionType.BlockingQueuedConnection)

        self._adblock = None
        self._replies = {}
        self._modified = False
        self.__thread_running = False

    def start(self):
        to_download = [(url, path) for url, path in self._user_urls.items()
                       if not os.path.isfile(path)
                       or (os.path.getmtime(path) + 3600) < time.time()]
        for url, path in to_download:
            reply = self.app.network_manager.get(QNetworkRequest(QUrl(url)))
            reply.readyRead.connect(self._dl_ready_read)
            reply.finished.connect(self._dl_finished)
            self._replies[reply] = {"path": path}
        self._maybe_finish()

    def _maybe_finish(self):
        if self._replies:
            return

        if not self._modified:
            try:
                with open(self._cached_urls_path) as f:
                    cached_urls = json.load(f)
            except FileNotFoundError:
                self._modified = True
            except Exception:
                logging.exception("Could not load cached urls. Removing %s."
                                  % self._cached_urls_path)
                os.unlink(self._cached_urls_path)
                self._modified = True
            else:
                if cached_urls != self._user_urls or not os.path.exists(self._cache_file):
                    self._modified = True

        self.__thread_running = True
        QThreadPool.globalInstance().start(
            self._parse_adblock_files if self._modified else self._adblock_from_cache)

    def _adblock_from_cache(self):
        adblock = AdBlock()
        adblock.load(self._cache_file)
        self.adblock_ready.emit(adblock)

    def _parse_adblock_files(self):
        adblock = AdBlock()
        for path in self._user_urls.values():
            logging.info("parsing adblock file: %s", path)
            try:
                with open(path) as f:
                    adblock.parse(f.read())
            except Exception:
                logging.exception(f"Unable to parse {f.name} adblock file")
            adblock.save(self._cache_file)
        self.adblock_ready.emit(adblock)

    def _on_adblock_ready(self, adblock):
        self.__thread_running = False
        with open(self._cached_urls_path, "w") as f:
            json.dump(self._user_urls, f)
        self._adblock = adblock
        self.finished.emit()

    def adblock(self):
        return self._adblock

    def _dl_ready_read(self):
        reply = self.sender()
        data = self._replies[reply]
        if "file" not in data:
            headers = {bytes(k).lower(): bytes(v)
                       for k, v in reply.rawHeaderPairs()}
            if os.path.isfile(data["path"]):
                try:
                    last_modified = dateparser.parse(
                        headers[b"last-modified"].decode("utf-8"),
                        languages=["en"])
                except Exception:
                    logging.exception(
                        "Unable to parse the last-modified header for %s",
                        reply.url().toString())
                else:
                    file_time = datetime.fromtimestamp(
                        os.path.getmtime(data["path"]), timezone.utc)
                    if last_modified < file_time:
                        logging.info("no need to download adblock rule: %s", reply.url)
                        # touch on the file
                        os.utime(data["path"], None)
                        self._close_reply(reply)
                        self._maybe_finish()
                        return
            logging.info("downloading adblock rule: %s", reply.url().toString())
            data["file"] = open(data["path"], "w")

        data["file"].write(bytes(reply.readAll()).decode("utf-8"))

    def _dl_finished(self):
        reply = self.sender()
        self._modified = True
        data = self._replies.pop(reply)
        data["file"].close()
        self._maybe_finish()

    def _close_reply(self, reply):
        del self._replies[reply]
        reply.readyRead.disconnect(self._dl_ready_read)
        reply.finished.disconnect(self._dl_finished)
        reply.close()

    def abort(self):
        for reply, data in list(self._replies.items()):
            self._close_reply(reply)
            if "file" in data:
                data["file"].close()
                os.unlink(data["path"])
        # wait for any thread to join
        if self.__thread_running:
            QThreadPool.globalInstance().waitForDone(1000)
