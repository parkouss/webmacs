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
import re
from PyQt5.QtCore import QBuffer, QFile
from PyQt5.QtWebEngineCore import QWebEngineUrlSchemeHandler
from jinja2 import Environment, PackageLoader
from ... import version, COMMANDS
from ...variables import VARIABLES


PAGES = []
_REQUESTS_HANDLER = []
THIS_DIR = os.path.dirname(os.path.realpath(__file__))


def register_page(match_url=None, visible=True):
    def wrapper(meth):
        if visible:
            PAGES.append(meth.__name__)
        if match_url is None:
            match = re.compile(r"^(%s)$" % re.escape(meth.__name__))
        elif isinstance(match_url, str):
            match = re.compile(match_url)
        else:
            match = match_url

        _REQUESTS_HANDLER.append((match, meth))

        return meth
    return wrapper


class WebmacsSchemeHandler(QWebEngineUrlSchemeHandler):
    scheme = b"webmacs"

    def __init__(self, parent=None):
        QWebEngineUrlSchemeHandler.__init__(self, parent)
        self.env = Environment(
            autoescape=True,
            loader=PackageLoader(__name__),
        )

    def reply_template(self, job, tpl_name, data):
        template = self.env.get_template(tpl_name + ".html")
        buffer = QBuffer(self)
        buffer.setData(template.render(**data).encode("utf-8"))
        job.reply(b"text/html", buffer)

    def requestStarted(self, job):
        url = job.requestUrl()
        url_s = url.toString()[10:]  # strip webmacs://

        for re_match, meth in _REQUESTS_HANDLER:
            res = re_match.match(url_s)
            if res:
                meth(self, job, url, *res.groups())
                return

    @register_page(match_url=r"^/js/(.+\.js)$", visible=False)
    def to_js(self, job, _, path):
        js_path = os.path.join(THIS_DIR, "js", path)
        if os.path.isfile(js_path):
            f = QFile(js_path, self)
            job.reply(b"application/javascript", f)

    @register_page()
    def version(self, job, _, name):
        self.reply_template(job, name, {
            "versions": (
                ("Webmacs version", version.WEBMACS_VERSION_STR),
                ("Qt version", version.QT_VERSION_STR),
                ("Chromium version", version.chromium_version()),
                ("Opengl vendor", version.opengl_vendor()),
            )
        })

    @register_page()
    def downloads(self, job, _, name):
        self.reply_template(job, name, {})

    @register_page()
    def commands(self, job, _, name):
        self.reply_template(job, name, {"commands": COMMANDS})

    @register_page()
    def variables(self, job, _, name):
        self.reply_template(job, name, {"variables": VARIABLES})
