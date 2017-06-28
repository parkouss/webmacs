import json

from PyQt5.QtCore import QUrl

from .commands.webjump import define_webjump
from urllib.request import urlopen


def google_complete(text):
    if not text:
        return []
    url = ("https://www.google.com/complete/search?client=firefox&q="
           + str(QUrl.toPercentEncoding(text), "utf-8"))
    with urlopen(url) as conn:
        return json.loads(str(conn.read(), "latin1"))[1]

define_webjump("google",
               "https://www.google.fr/search?q=%s&ie=utf-8&oe=utf-8",
               "Google Search",
               complete_fn=google_complete)
