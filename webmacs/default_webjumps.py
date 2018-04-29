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

from PyQt5.QtCore import QUrl

from .commands.webjump import define_webjump, define_protocol, \
    webjump_default, WebJumpRequestCompleter
from .minibuffer.prompt import FSModel
from .scheme_handlers.webmacs import PAGES as webmacs_pages


# ----------- doc example

def complete_google(text):
    if not text:
        return None

    url = ("https://www.google.com/complete/search?client=firefox&q="
           + str(QUrl.toPercentEncoding(text), "utf-8"))

    def extract_completions(response):
        return json.loads(str(response, "utf-8"))[1]

    return WebJumpRequestCompleter(url, extract_completions)


define_webjump("google",
               "https://www.google.com/search?q=%s&ie=utf-8&oe=utf-8",
               "Google Search",
               complete_fn=complete_google)

# ----------- end of doc example


def complete_fs():
    model = FSModel()

    def _complete(text):
        model.text_changed(text)
        return [model.data(model.index(i, 0))
                for i in range(model.rowCount())]

    return _complete


define_protocol("file",
                "Local uris",
                complete_fn=complete_fs())


def complete_pages(text):
    return [p for p in webmacs_pages if text in p]


define_protocol("webmacs",
                "webmacs internal pages",
                complete_fn=complete_pages)


def complete_protocol(protocol):

    def complete(text):
        completer = complete_google(protocol + text)
        extract_fn = completer.extract_completions_fn

        completer.extract_completions_fn \
            = lambda data: [r[len(protocol):]
                            for r in extract_fn(data)
                            if r.startswith(protocol)]
        return completer
    return complete


define_protocol("http",
                "web sites",
                complete_fn=complete_protocol("http://"))

define_protocol("https",
                "secure web sites",
                complete_fn=complete_protocol("https://"))


def complete_duckduckgo(text):
    if not text:
        return None
    url = ("https://www.duckduckgo.com/ac/?q={}&type=list".format(
        str(QUrl.toPercentEncoding(text), "utf-8"))
    )

    def extract_completions(response):
        return json.loads(str(response, "utf-8"))[1]

    return WebJumpRequestCompleter(url, extract_completions)


define_webjump("duckduckgo",
               "https://www.duckduckgo.com/?q=%s",
               "Duckduckgo Search",
               complete_fn=complete_duckduckgo)

webjump_default.set_value("duckduckgo")
