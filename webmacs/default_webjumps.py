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

from .commands.webjump import define_webjump, define_protocol, \
    webjump_default, WebJumpRequestCompleter, SyncWebJumpCompleter
from .minibuffer.prompt import FSModel
from .scheme_handlers.webmacs import PAGES as webmacs_pages


# ----------- doc example

def complete_google():
    return WebJumpRequestCompleter(
        "https://www.google.com/complete/search?client=firefox&q=%s",
        lambda response: json.loads(str(response, "utf-8"))[1]
    )


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

    return SyncWebJumpCompleter(_complete)


define_protocol("file",
                "Local uris",
                complete_fn=complete_fs)


def complete_pages():
    return SyncWebJumpCompleter(
        lambda text: [p for p in webmacs_pages if text in p]
    )


define_protocol("webmacs",
                "webmacs internal pages",
                complete_fn=complete_pages)


def complete_protocol(protocol):

    def complete():
        completer = complete_google()
        extract_fn = completer.extract_completions_fn
        complete = completer.complete

        completer.extract_completions_fn \
            = lambda data: [r[len(protocol):]
                            for r in extract_fn(data)
                            if r.startswith(protocol)]

        completer.complete \
            = lambda text: complete(protocol + text)
        return completer
    return complete


define_protocol("http",
                "web sites",
                complete_fn=complete_protocol("http://"))

define_protocol("https",
                "secure web sites",
                complete_fn=complete_protocol("https://"))


def complete_duckduckgo():
    return WebJumpRequestCompleter(
        "https://www.duckduckgo.com/ac/?q=%s&type=list",
        lambda response: json.loads(str(response, "utf-8"))[1]
    )


define_webjump("duckduckgo",
               "https://www.duckduckgo.com/?q=%s",
               "Duckduckgo Search",
               complete_fn=complete_duckduckgo)

webjump_default.set_value("duckduckgo")
