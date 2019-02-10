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
from .features import Features
from . import variables, version


THIS_DIR = os.path.dirname(os.path.realpath(__file__))


class Profile(object):
    def __init__(self, name, q_profile=None):
        self.name = name
        if q_profile is None:
            q_profile = QWebEngineProfile.defaultProfile()

        self.q_profile = q_profile

        self._scheme_handlers = {}  # keep a python reference

    def update_spell_checking(self):
        if version.min_qt_version < (5, 8):
            return
        dicts = variables.get("spell-checking-dictionaries")
        self.q_profile.setSpellCheckEnabled(bool(dicts))
        self.q_profile.setSpellCheckLanguages(dicts)

    def enable(self, app):
        cache_path = os.path.join(app.cache_path(), self.name)
        prof_path = os.path.join(app.profiles_path(), self.name)

        for path in [cache_path, prof_path]:
            if not os.path.isdir(path):
                os.makedirs(path)

        self.q_profile.setRequestInterceptor(app.url_interceptor())

        for handler in (WebmacsSchemeHandler,):
            h = handler(app)
            self._scheme_handlers[handler.scheme] = h
            self.q_profile.installUrlSchemeHandler(handler.scheme, h)

        self.q_profile.setPersistentStoragePath(prof_path)
        self.q_profile.setPersistentCookiesPolicy(
            QWebEngineProfile.ForcePersistentCookies)

        if app.instance_name == "default":
            session_fname = "session.json"
        else:
            session_fname = "session-{}.json".format(app.instance_name)
        self.session_file = os.path.join(prof_path, session_fname)

        self.visitedlinks \
            = VisitedLinks(os.path.join(prof_path, "visitedlinks.db"))
        self.autofill \
            = Autofill(PasswordDb(os.path.join(prof_path, "autofill.db")))
        self.ignored_certs \
            = IgnoredCertificates(os.path.join(prof_path, "ignoredcerts.db"))
        self.bookmarks \
            = Bookmarks(os.path.join(prof_path, "bookmarks.db"))
        self.features \
            = Features(os.path.join(prof_path, "features.db"))

        self.q_profile.setCachePath(cache_path)
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

        contentjs = ["WEBMACS_SECURE_ID = {};".format(str(id(self)))]
        with open(os.path.join(THIS_DIR, "scripts", "setup.js")) as f:
            contentjs.append(f.read())
        with open(os.path.join(THIS_DIR, "scripts", "textedit.js")) as f:
            contentjs.append(f.read())
        with open(os.path.join(THIS_DIR, "scripts", "hint.js")) as f:
            contentjs.append(f.read())
        with open(os.path.join(THIS_DIR, "scripts", "textzoom.js")) as f:
            contentjs.append(f.read())
        with open(os.path.join(THIS_DIR, "scripts", "caret_browsing.js")) as f:
            contentjs.append(f.read())

        script = QWebEngineScript()
        script.setInjectionPoint(QWebEngineScript.DocumentCreation)
        script.setSourceCode("\n".join(contentjs))
        script.setWorldId(QWebEngineScript.ApplicationWorld)
        script.setRunsOnSubFrames(True)
        self.q_profile.scripts().insert(script)

        inject_js(os.path.join(THIS_DIR, "scripts", "autofill.js"))


def default_profile():
    return Profile("default")
