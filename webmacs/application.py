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
import logging

from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtWidgets import QApplication

from . import require, GLOBAL_EVENT_FILTER
from .adblock import EASYLIST, Adblocker
from .download_manager import DownloadManager
from .profile import default_profile

try:
    # on some graphic cards (at least Intel HD Graphics 620 (Kabylake GT2))
    # without this line trying to show a QWebEngineView does segfault.
    # see https://github.com/spyder-ide/spyder/issues/4495
    # for now I don't require that as an install dependencies (pip install
    # pyopengl) but I let that code here to remember and to let the user a
    # chance to fix the issue by just installing pyopengl.
    from OpenGL import GL # noqa
except ImportError:
    pass


THIS_DIR = os.path.dirname(os.path.realpath(__file__))


class UrlInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, app):
        QWebEngineUrlRequestInterceptor.__init__(self)
        self.app = app
        generator = Adblocker(app.adblock_path())
        for url in EASYLIST:
            generator.register_filter_url(url)
        self._adblock = generator.generate_rules()
        self._use_adblock = True

    def toggle_use_adblock(self):
        self._use_adblock = not self._use_adblock

    def interceptRequest(self, request):
        url = request.requestUrl()
        url_s = url.toString()
        if self._use_adblock and self._adblock.matches(
                url_s,
                request.firstPartyUrl().toString(),):
            logging.info("filtered: %s", url_s)
            request.block(True)


def app():
    return Application.INSTANCE


def _app_requires():
    require(".keymaps.global")
    require(".keymaps.caret_browsing")

    require(".commands.follow")
    require(".commands.buffer_history")
    require(".commands.global")
    require(".commands.isearch")
    require(".commands.webbuffer")
    require(".commands.caret_browsing")

    require(".default_webjumps")


class Application(QApplication):
    INSTANCE = None

    def __init__(self, args):
        QApplication.__init__(self, args)
        self.__class__.INSTANCE = self

        with open(os.path.join(THIS_DIR, "app_style.css")) as f:
            self.setStyleSheet(f.read())

        self._setup_conf_paths()

        self._interceptor = UrlInterceptor(self)
        self._download_manager = DownloadManager(self)

        self.profile = default_profile()
        self.profile.enable(self)

        self.aboutToQuit.connect(self.profile.save_session)

        self.installEventFilter(GLOBAL_EVENT_FILTER)

        settings = QWebEngineSettings.globalSettings()
        settings.setAttribute(
            QWebEngineSettings.LinksIncludedInFocusChain, False,
        )
        settings.setAttribute(
            QWebEngineSettings.PluginsEnabled, True,
        )
        settings.setAttribute(
            QWebEngineSettings.FullScreenSupportEnabled, True,
        )
        settings.setAttribute(
            QWebEngineSettings.JavascriptCanOpenWindows, True,
        )

        _app_requires()

    def _setup_conf_paths(self):
        self._conf_path = os.path.join(os.path.expanduser("~"), ".webmacs")

        def mkdir(path):
            if not os.path.isdir(path):
                os.makedirs(path)

        mkdir(self.conf_path())
        mkdir(self.profiles_path())

    def conf_path(self):
        return self._conf_path

    def profiles_path(self):
        return os.path.join(self.conf_path(), "profiles")

    def adblock_path(self):
        return os.path.join(self.conf_path(), "adblock")

    def visitedlinks(self):
        return self.profile.visitedlinks

    def autofill(self):
        return self.profile.autofill

    def url_interceptor(self):
        return self._interceptor

    def download_manager(self):
        return self._download_manager

    def ignored_certs(self):
        return self.profile.ignored_certs
