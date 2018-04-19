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
from PyQt5.QtCore import QBuffer, QFile
from PyQt5.QtWebEngineCore import QWebEngineUrlSchemeHandler
from jinja2 import Environment, PackageLoader
from ... import version


PAGES = {}
THIS_DIR = os.path.dirname(os.path.realpath(__file__))


def register_page(meth):
    PAGES[meth.__name__] = meth
    return meth


class WebmacsSchemeHandler(QWebEngineUrlSchemeHandler):
    scheme = b"webmacs"
    pages = {}

    def __init__(self, parent=None):
        QWebEngineUrlSchemeHandler.__init__(self, parent)
        self.env = Environment(
            autoescape=True,
            loader=PackageLoader(__name__),
        )

    def requestStarted(self, job):
        url = job.requestUrl()
        request = url.authority()

        if request not in PAGES:
            path = url.path()
            if path.startswith("/js/"):
                js_path = os.path.join(THIS_DIR, "js", path[4:])
                if os.path.isfile(js_path):
                    f = QFile(js_path, self)
                    job.reply(b"application/javascript", f)

            return

        template = self.env.get_template(request + ".html")

        fn = PAGES[request]

        buffer = QBuffer(self)
        buffer.setData(template.render(**fn(self)).encode("utf-8"))
        job.reply(b"text/html", buffer)

    @register_page
    def version(self):
        return {
            "versions": (
                ("Webmacs version", version.WEBMACS_VERSION_STR),
                ("Qt version", version.QT_VERSION_STR),
                ("Chromium version", version.chromium_version()),
                ("Opengl vendor", version.opengl_vendor()),
            )
        }

    @register_page
    def downloads(self):
        return {}
