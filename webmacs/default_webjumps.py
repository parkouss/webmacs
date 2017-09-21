import json

from PyQt5.QtCore import QUrl

from .commands.webjump import define_webjump
from urllib.request import urlopen
from .minibuffer.prompt import FSModel
from .scheme_handlers.webmacs import PAGES as webmacs_pages


def google_complete(text):
    if not text:
        return []
    url = ("https://www.google.com/complete/search?client=firefox&q="
           + str(QUrl.toPercentEncoding(text), "utf-8"))
    with urlopen(url) as conn:
        return json.loads(str(conn.read(), "latin1"))[1]


define_webjump("google ",
               "https://www.google.fr/search?q=%s&ie=utf-8&oe=utf-8",
               "Google Search",
               complete_fn=google_complete)


def complete_fs():
    model = FSModel()

    def _complete(text):
        model.text_changed(text)
        return [model.data(model.index(i, 0))
                for i in range(model.rowCount())]

    return _complete


define_webjump("file://",
               "file://%s",
               "Local uris",
               complete_fn=complete_fs())


def complete_pages(text):
    return [p for p in webmacs_pages if text in p]


define_webjump("webmacs://",
               "webmacs://%s",
               "webmacs internal pages",
               complete_fn=complete_pages)


def complete_duckduckgo(text):
    if not text:
        return []
    url = ("https://www.duckduckgo.com/ac/?q={}&type=list".format(
        str(QUrl.toPercentEncoding(text), "utf-8"))
    )
    with urlopen(url) as conn:
        return json.loads(str(conn.read(), "utf-8"))[1]


define_webjump("duckduckgo ",
               "https://www.duckduckgo.com/?q=%s",
               "Duckduckgo Search",
               complete_fn=complete_duckduckgo)
