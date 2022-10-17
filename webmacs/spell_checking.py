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

from . import variables
from .task import Task

from PyQt6.QtNetwork import QNetworkRequest, QNetworkReply
from PyQt6.QtCore import QUrl

import os
import re
import json
import logging
import base64
from collections import namedtuple


RemoteBdic = namedtuple("RemoteBdic", ("name", "version", "extension"))

BDIC_FILES_URL = "https://chromium.googlesource.com/chromium/deps/hunspell_dictionaries.git/+/master/" # noqa


spell_checking_dictionaries = variables.define_variable(
    "spell-checking-dictionaries",
    "List of dictionaries to use for spell checking.",
    (),
    type=variables.List(variables.String()),
)


class Versions(dict):
    @classmethod
    def from_file(cls, path):
        if os.path.isfile(path):
            with open(path) as f:
                return cls(**json.load(f))
        else:
            return cls()

    def get_version(self, name):
        return self.get(name, [0, 0])

    def write(self, path):
        with open(path, "w") as f:
            json.dump(dict(**self), f)


class SpellCheckingTask(Task):
    def __init__(self, app, path):
        Task.__init__(self)
        self.app = app
        self.path = path
        self.__versions_path = os.path.join(self.path, "versions.json")
        self.__versions = None
        self.__modified = False
        self.__bdic_replies = {}

    def start(self):
        if not os.path.isdir(self.path):
            try:
                os.makedirs(self.path)
            except Exception as exc:
                logging.warning("Can not initialize spell checking dir %s: %s"
                                % (self.path, exc))
                return False
        self.__versions = Versions.from_file(self.__versions_path)
        self.__bdic_replies.clear()

        reply = self.app.network_manager.get(
            QNetworkRequest(QUrl(BDIC_FILES_URL + "?format=json")))
        reply.finished.connect(self._on_bdic_files_list)

    def _on_bdic_files_list(self):
        reply = self.sender()
        # A special 5-byte prefix must be stripped from the response
        # See: https://github.com/google/gitiles/issues/22
        #      https://github.com/google/gitiles/issues/82
        json_data = json.loads(bytes(reply.readAll())[5:].decode("utf-8"))

        re_bdic = re.compile(r"(.*)-(\d+-\d+)(\.bdic)$")
        remotes = {}
        for entry in json_data["entries"]:
            res = re_bdic.match(entry["name"])
            if res:
                name, version, extension = (res.group(1), res.group(2),
                                            res.group(3))
                version = [int(e) for e in version.split("-")]

                remotes[name] = RemoteBdic(name, version, extension)

        local_files = set(os.path.splitext(f)[0] for f in os.listdir(self.path)
                          if f.endswith(".bdic"))

        for name in spell_checking_dictionaries.value:
            try:
                r = remotes[name]
            except KeyError:
                logging.warning(
                    "No spell checking dict for %s. \nAvailable: %s"
                    % (name, list(remotes))
                )
                continue
            if name not in local_files:
                logging.info("Downloading dict %s" % name)
                self._install(r)

            elif r.version > self.__versions.get(name, [0, 0]):
                logging.info("Updating dict %s" % name)
                self._install(r)

        if not self.__bdic_replies:
            self.finished.emit()

    def _install(self, r):
        url = "{}{}-{}{}?format=TEXT".format(
            BDIC_FILES_URL,
            r.name,
            "-".join(str(v) for v in r.version),
            r.extension
        )
        dest = os.path.join(self.path, "{}{}".format(r.name, r.extension))

        reply = self.app.network_manager.get(QNetworkRequest(QUrl(url)))
        self.__bdic_replies[reply] = {"bdic": r, "dest": dest, "data": b""}
        reply.readyRead.connect(self._bdic_ready_read)
        reply.finished.connect(self._bdic_finished)

    def _bdic_ready_read(self):
        reply = self.sender()
        self.__bdic_replies[reply]["data"] += bytes(reply.readAll())

    def _bdic_finished(self):
        reply = self.sender()
        data = self.__bdic_replies.pop(reply)
        if reply.error() != QNetworkReply.NetworkError.NoError:
            if not self.error():
                self.set_error_message(reply.errorString())
                # abort other replies
                for r in self.__bdic_replies:
                    r.abort()
            if not self.__bdic_replies:
                self.finished.emit()
            return
        with open(data["dest"], 'bw') as f:
            f.write(base64.decodebytes(data["data"]))

        self.__versions[data["bdic"].name] = data["bdic"].version

        if not self.__bdic_replies:
            self.__versions.write(self.__versions_path)
            self.finished.emit()
