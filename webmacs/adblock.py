import os
import logging
import time

from datetime import datetime, timezone
import dateparser

from _adblock import AdBlock
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request


EASYLIST = (
    "https://easylist.to/easylist/easylist.txt",
    "https://easylist.to/easylist/easyprivacy.txt",
    "https://easylist.to/easylist/fanboy-annoyance.txt"
)


class Adblocker(object):
    def __init__(self, cache_path):
        if not os.path.isdir(cache_path):
            os.makedirs(cache_path)
        self._cache_path = cache_path
        self._urls = {}

    def register_filter_url(self, url, destfile=None):
        if destfile is None:
            destfile = url.rsplit("/", 1)[-1]
        self._urls[url] = os.path.join(self._cache_path, destfile)

    def _download_file(self, url, path):
        headers = {'User-Agent': "Magic Browser"}
        req = urllib.request.Request(url, None, headers)
        with urllib.request.urlopen(req, timeout=5) as conn:
            if os.path.isfile(path):
                # check if the file on the server is newer than what we have
                file_time = datetime.fromtimestamp(os.path.getmtime(path),
                                                   timezone.utc)
                try:
                    last_modified = dateparser.parse(
                        conn.info()["last-modified"],
                        languages=["en"])
                except:
                    logging.exception(
                        "Unable to parse the last-modified header for %s",
                        url)
                else:
                    print(last_modified, file_time)
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

    def _fetch_urls(self):
        modified = False
        # do not try to download if files are less than a day old
        to_download = [(url, path) for url, path in self._urls.items()
                       if not os.path.isfile(path)
                       or os.path.getmtime(path) > (time.time() + 3600)]
        if to_download:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(self._download_file, url, path)
                           for url, path in to_download]

                for future in as_completed(futures):
                    if future.result():
                        modified = True

        return modified

    def generate_rules(self):
        adblock = AdBlock()
        cache = os.path.join(self._cache_path, "cache.dat")
        modified = self._fetch_urls()
        if modified or not os.path.isfile(cache):
            for path in self._urls.values():
                logging.info("parsing adblock file: %s", path)
                with open(path) as f:
                    adblock.parse(f.read())
            adblock.save(cache)
        else:
            logging.info("loading adblock cached data: %s", cache)
            adblock.load(cache)
        return adblock
