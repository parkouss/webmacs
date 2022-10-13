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
from .runnable import Runner


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


class Adblocker(object):
    def __init__(self, cache_path):
        if not os.path.isdir(cache_path):
            os.makedirs(cache_path)
        self._cache_path = cache_path
        self._urls = {}
        self.register_filter_urls()
        self.cached_urls_path = os.path.join(self._cache_path, "urls.json")

    def register_filter_urls(self):
        """
        Register urls from the adblock_rules variable.
        """
        for url in adblock_urls_rules.value:
            self.register_filter_url(url)

    def register_filter_url(self, url, destfile=None):
        if destfile is None:
            destfile = url.rsplit("/", 1)[-1]
        self._urls[url] = os.path.join(self._cache_path, destfile)

    def load_cached_urls(self):
        if not os.path.isfile(self.cached_urls_path):
            return None
        try:
            with open(self.cached_urls_path) as f:
                return json.load(f)
        except Exception:
            logging.exception("Could not load cached urls. Removing %s."
                              % self.cached_urls_path)
            os.unlink(self.cached_urls_path)
            return None

    def save_cached_urls(self, cached_urls):
        with open(self.cached_urls_path, "w") as f:
            json.dump(cached_urls, f)

    def _download_file(self, url, path):
        headers = {'User-Agent': "Magic Browser"}
        req = urllib.request.Request(url, None, headers)
        try:
            with urllib.request.urlopen(req, timeout=320) as conn:
                if os.path.isfile(path):
                    # check if the file on the server is newer than what we have
                    file_time = datetime.fromtimestamp(os.path.getmtime(path),
                                                       timezone.utc)
                    try:
                        last_modified = dateparser.parse(
                            conn.info()["last-modified"],
                            languages=["en"])
                    except Exception:
                        logging.exception(
                            "Unable to parse the last-modified header for %s",
                            url)
                    else:
                        if last_modified < file_time:
                            logging.info("no need to download adblock rule: %s",
                                         url)
                            # touch on the file
                            os.utime(path, None)
                            return False
                logging.info("downloading adblock rule: %s", url)
                with open(path, "w") as f:
                    data = conn.read()
                    f.write(data.decode("utf-8"))
                return True
        except Exception:
            logging.exception(f"Error using adblock list from {url}")

    def _fetch_urls(self):
        modified = False
        # do not try to download if files are less than a day old
        to_download = [(url, path) for url, path in self._urls.items()
                       if not os.path.isfile(path)
                       or (os.path.getmtime(path) + 3600) < time.time()]
        if to_download:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(self._download_file, url, path)
                           for url, path in to_download]

                for future in as_completed(futures):
                    if future.result():
                        modified = True

        return modified

    def cache_file(self):
        return os.path.join(self._cache_path, "cache.dat")

    def local_adblock(self):
        adblock = AdBlock()
        cache = self.cache_file()
        if os.path.isfile(cache):
            logging.info("loading adblock cached data: %s", cache)
            adblock.load(cache)
        return adblock

    def maybe_update_adblock(self):
        adblock = AdBlock()
        cache = self.cache_file()
        cached_urls = self.load_cached_urls()
        if cached_urls != self._urls:
            self._fetch_urls()
            modified = True
        else:
            modified = self._fetch_urls()
        if modified or not os.path.isfile(cache):
            for path in self._urls.values():
                logging.info("parsing adblock file: %s", path)
                try:
                    with open(path) as f:
                        adblock.parse(f.read())
                except Exception:
                    logging.exception(f"Unable to parse {f.name} adblock file")
            adblock.save(cache)
            logging.info("updating adblock cache file %s." % cache)
            self.save_cached_urls(self._urls)
            return adblock


class AdblockUpdateRunner(Runner):
    description = "adblock updater"

    def __init__(self, adblocker, **kwargs):
        Runner.__init__(self, **kwargs)
        self.adblocker = adblocker

    def run_in_thread(self):
        return self.adblocker.maybe_update_adblock()
