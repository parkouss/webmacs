import os
import re
import json
import logging
import urllib.request
import base64

from . import variables, version
from .runnable import Runner
from collections import namedtuple


RemoteBdic = namedtuple("RemoteBdic", ("name", "version", "extension"))

BDIC_FILES_URL = "https://chromium.googlesource.com/chromium/deps/hunspell_dictionaries.git/+/master/" # noqa


spell_checking_dictionaries = variables.define_variable(
    "spell-checking-dictionaries",
    "List of dictionaries to use for spell checking. Only usable on Qt >= 5.8",
    (),
    conditions=(
        variables.condition(
            lambda v: isinstance(v, (list, tuple)),
            "must be a list of strings"
        ) if version.qt_version >= (5, 8) else variables.condition(
            lambda v: not bool(v),
            "Can't be set for Qt < 5.8"
        ),
    ),
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


class SpellCheckingUpdater(object):
    def __init__(self, path):
        self.path = path

    @property
    def _versions_path(self):
        return os.path.join(self.path, "versions.json")

    def _list_remote(self):
        with urllib.request.urlopen(BDIC_FILES_URL + "?format=json") as f:
            # A special 5-byte prefix must be stripped from the response
            # See: https://github.com/google/gitiles/issues/22
            #      https://github.com/google/gitiles/issues/82
            json_data = json.loads(f.read()[5:].decode("utf-8"))

        re_bdic = re.compile(r"(.*)-(\d+-\d+)(\.bdic)$")
        files = {}
        for entry in json_data["entries"]:
            res = re_bdic.match(entry["name"])
            if res:
                name, version, extension = (res.group(1), res.group(2),
                                            res.group(3))
                version = [int(e) for e in version.split("-")]

                files[name] = RemoteBdic(name, version, extension)
        return files

    def _install(self, r):
        url = "{}{}-{}{}?format=TEXT".format(
            BDIC_FILES_URL,
            r.name,
            "-".join(str(v) for v in r.version),
            r.extension
        )
        dest = os.path.join(self.path, "{}{}".format(r.name, r.extension))

        with urllib.request.urlopen(url) as response:
            decoded = base64.decodebytes(response.read())
            with open(dest, 'bw') as dict_file:
                dict_file.write(decoded)

    def update(self):
        if not os.path.isdir(self.path):
            try:
                os.makedirs(self.path)
            except Exception as exc:
                logging.warning("Can not initialize spell checking dir %s: %s"
                                % (self.path, exc))
                return False
        versions = Versions.from_file(self._versions_path)

        remotes = self._list_remote()
        local_files = set(os.path.splitext(f)[0] for f in os.listdir(self.path)
                          if f.endswith(".bdic"))

        modified = False
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
                versions[name] = r.version
                modified = True
            elif r.version > versions.get(name, [0, 0]):
                logging.info("Updating dict %s" % name)
                self._install(r)
                versions[name] = r.version
                modified = True

        if modified:
            versions.write(self._versions_path)


class SpellCheckingUpdateRunner(Runner):
    description = "spell checking update"

    def __init__(self, path, **kwargs):
        Runner.__init__(self, **kwargs)
        self.path = path

    def run_in_thread(self):
        spcu = SpellCheckingUpdater(self.path)
        spcu.update()
