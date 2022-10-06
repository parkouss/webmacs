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

from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineScript, \
    QWebEngineSettings
from PyQt6.QtCore import QFile, QTextStream

from .scheme_handlers import all_schemes
from .visited_links import VisitedLinks
from .ignore_certificates import IgnoredCertificates
from .bookmarks import Bookmarks
from .features import Features
from . import variables, version, require
from .password_manager import make_password_manager
from .variables import define_variable, Bool


THIS_DIR = os.path.dirname(os.path.realpath(__file__))


enable_javascript = define_variable(
    "enable-javascript",
    "Enable the running of javascript programs. Default to True.",
    True,
    type=Bool(),
)

enable_pdfviewer = define_variable(
    "enable-pdfviewer",
    "Specifies that PDF documents will be opened in the internal PDF viewer."
    " Default to False",
    False,
    type=Bool(),
)


def make_dir(*parts):
    path = os.path.join(*parts)
    os.makedirs(path, exist_ok=True)
    return path


class Profile(object):
    def __init__(self, name):
        self.name = name
        self.q_profile = QWebEngineProfile(name)
        self._scheme_handlers = {}  # keep a python reference

        app = require(".application").app()

        self.path = path = make_dir(app.profiles_path(), self.name)
        persistent_path = make_dir(path, "persistent")
        cache_path = make_dir(path, "cache")

        self.q_profile.setUrlRequestInterceptor(app.url_interceptor())

        for handler in all_schemes():
            h = handler(app)
            self._scheme_handlers[handler.scheme] = h
            self.q_profile.installUrlSchemeHandler(handler.scheme, h)

        self.q_profile.setPersistentStoragePath(persistent_path)
        self.q_profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        self.q_profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)

        if app.instance_name == "default":
            session_fname = "session.json"
        else:
            session_fname = "session-{}.json".format(app.instance_name)
        self.session_file = os.path.join(path, session_fname)

        self.visitedlinks \
            = VisitedLinks(os.path.join(path, "visitedlinks.db"))
        self.ignored_certs \
            = IgnoredCertificates(os.path.join(path, "ignoredcerts.db"))
        self.bookmarks \
            = Bookmarks(os.path.join(path, "bookmarks.db"))
        self.features \
            = Features(os.path.join(path, "features.db"))

        self.q_profile.setCachePath(cache_path)
        self.q_profile.downloadRequested.connect(
            app.download_manager().download_requested
        )
        self.password_manager = make_password_manager()

        self.update_spell_checking()

        def inject_js(filepath,
                      ipoint=QWebEngineScript.InjectionPoint.DocumentCreation,
                      iid=QWebEngineScript.ScriptWorldId.ApplicationWorld,
                      sub_frames=False,
                      script_transform=None):
            f = QFile(filepath)
            assert f.open(
                QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
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
        script.setInjectionPoint(
            QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setSourceCode("\n".join(contentjs))
        script.setWorldId(QWebEngineScript.ScriptWorldId.ApplicationWorld)
        script.setRunsOnSubFrames(True)
        self.q_profile.scripts().insert(script)

        inject_js(os.path.join(THIS_DIR, "scripts", "password_manager.js"))

        settings = self.q_profile.settings()
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LinksIncludedInFocusChain, False,
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.PluginsEnabled, True,
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True,
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True,
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.FocusOnNavigationEnabled, False,
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled,
            enable_javascript.value,
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.PdfViewerEnabled,
            enable_pdfviewer.value
        )

    def update_spell_checking(self):
        dicts = variables.get("spell-checking-dictionaries")
        self.q_profile.setSpellCheckEnabled(bool(dicts))
        self.q_profile.setSpellCheckLanguages(dicts)


def named_profile(name):
    return Profile(name)
