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

from PyQt5.QtWebEngineWidgets import QWebEngineProfile, QWebEngineScript
from PyQt5.QtCore import QFile, QTextStream

from .scheme_handlers.webmacs import WebmacsSchemeHandler
from .visited_links import VisitedLinks
from .autofill import Autofill
from .autofill.db import PasswordDb
from .ignore_certificates import IgnoredCertificates
from .bookmarks import Bookmarks
from . import variables


THIS_DIR = os.path.dirname(os.path.realpath(__file__))


class Profile(object):
    def __init__(self, name, q_profile=None):
        self.name = name
        if q_profile is None:
            q_profile = QWebEngineProfile.defaultProfile()

        self.q_profile = q_profile

        self._scheme_handlers = {}  # keep a python reference

    def update_spell_checking(self):
        dicts = variables.get("spell-checking-dictionaries")
        self.q_profile.setSpellCheckEnabled(bool(dicts))
        self.q_profile.setSpellCheckLanguages(dicts)

    def enable(self, app):
        path = os.path.join(app.profiles_path(), self.name)
        if not os.path.isdir(path):
            os.makedirs(path)

        self.q_profile.setRequestInterceptor(app.url_interceptor())

        for handler in (WebmacsSchemeHandler,):
            h = handler(app)
            self._scheme_handlers[handler.scheme] = h
            self.q_profile.installUrlSchemeHandler(handler.scheme, h)

        self.q_profile.setPersistentStoragePath(path)
        self.q_profile.setPersistentCookiesPolicy(
            QWebEngineProfile.ForcePersistentCookies)

        self.session_file = os.path.join(path, "session.json")

        self.visitedlinks \
            = VisitedLinks(os.path.join(path, "visitedlinks.db"))
        self.autofill \
            = Autofill(PasswordDb(os.path.join(path, "autofill.db")))
        self.ignored_certs \
            = IgnoredCertificates(os.path.join(path, "ignoredcerts.db"))
        self.bookmarks \
            = Bookmarks(os.path.join(path, "bookmarks.db"))

        self.q_profile.setCachePath(os.path.join(path, "cache"))
        self.q_profile.downloadRequested.connect(
            app.download_manager().download_requested
        )

        self.update_spell_checking()

        def inject_js(filepath, ipoint=QWebEngineScript.DocumentCreation,
                      iid=QWebEngineScript.ApplicationWorld, sub_frames=False,
                      script_transform=None):
            f = QFile(filepath)
            assert f.open(QFile.ReadOnly | QFile.Text)
            src = QTextStream(f).readAll()
            if script_transform:
                src = script_transform(src)

            script = QWebEngineScript()
            script.setInjectionPoint(ipoint)
            script.setSourceCode(src)
            script.setWorldId(iid)
            script.setRunsOnSubFrames(sub_frames)
            self.q_profile.scripts().insert(script)

        inject_js(":/qtwebchannel/qwebchannel.js")
        inject_js(
            os.path.join(THIS_DIR, "scripts", "setup.js"),
            sub_frames=True,
            script_transform=lambda src: src.replace("{{WEBMACS_SECURE_ID}}",
                                                     str(id(self))))
        inject_js(os.path.join(THIS_DIR, "scripts", "hint.js"))
        inject_js(os.path.join(THIS_DIR, "scripts", "textedit.js"))
        inject_js(os.path.join(THIS_DIR, "scripts", "autofill.js"))
        inject_js(os.path.join(THIS_DIR, "scripts", "caret_browsing.js"))
        inject_js(os.path.join(THIS_DIR, "scripts", "textzoom.js"))


def default_profile():
    return Profile("default")
