import os
import time

from adblockparser import AdblockRules, AdblockRule
from concurrent.futures import ThreadPoolExecutor
import urllib.request

from PyQt5.QtCore import QRegExp

EASYLIST = (
    "https://easylist.to/easylist/easylist.txt",
    "https://easylist.to/easylist/easyprivacy.txt",
    "https://easylist.to/easylist/fanboy-annoyance.txt"
)


class BlockRule(AdblockRule):
    def _url_matches(self, url):
        if self.regex_re is None:
            self.regex_re = QRegExp(self.regex)
        return self.regex_re.indexIn(url) != -1


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
            with open(path, "w") as f:
                data = conn.read()
                f.write(data.decode("utf-8"))

    def _fetch_urls(self):
        to_download = [(url, path) for url, path in self._urls.items()
                       if not os.path.isfile(path)
                       or os.path.getmtime(path) > (time.time() + 3600)]
        if to_download:
            with ThreadPoolExecutor(max_workers=5) as executor:
                for url, path in to_download:
                    executor.submit(self._download_file, url, path)

    def generate_rules(self):
        self._fetch_urls()
        rules = []
        for path in self._urls.values():
            print (path)
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rules.append(line)
        return AdblockRules(rules, rule_cls=BlockRule)
