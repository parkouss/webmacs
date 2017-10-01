import os
import logging

from PyQt5.QtWebEngineWidgets import QWebEngineProfile, QWebEngineScript, \
    QWebEngineSettings
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QFile, QTextStream

from . import require
from .keyboardhandler import KeyEater
from .adblock import EASYLIST, Adblocker
from .visited_links import VisitedLinks
from .commands import COMMANDS
from .autofill import Autofill
from .autofill.db import PasswordDb
from .scheme_handlers.webmacs import WebmacsSchemeHandler
from .download_manager import DownloadManager
from .minibuffer import current_minibuffer


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

        self._setup_default_profile()

        key_eater = KeyEater(COMMANDS)
        key_eater.on_keychord.connect(
            lambda kc: self.minibuffer_show_info(
                " ".join((str(k) for k in kc))
            )
        )
        self.installEventFilter(key_eater)

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

        require(".keymaps.global")

        require(".commands.follow")
        require(".commands.buffer_history")
        require(".commands.global")
        require(".commands.isearch")
        require(".commands.webbuffer")

        require(".default_webjumps")

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
        return self._visitedlinks

    def autofill(self):
        return self._autofill

    def url_interceptor(self):
        return self._interceptor

    def download_manager(self):
        return self._download_manager

    def minibuffer_show_info(self, text):
        current_minibuffer().show_info(text)

    def _setup_default_profile(self):
        default_profile = QWebEngineProfile.defaultProfile()
        default_profile.setRequestInterceptor(self._interceptor)

        self._scheme_handlers = {}  # keep a python reference
        for handler in (WebmacsSchemeHandler,):
            h = handler(self)
            self._scheme_handlers[handler.scheme] = h
            default_profile.installUrlSchemeHandler(handler.scheme, h)

        path = self.profiles_path()
        profile_path = os.path.join(path, "default")
        default_profile.setPersistentStoragePath(profile_path)
        default_profile.setPersistentCookiesPolicy(
            QWebEngineProfile.ForcePersistentCookies)
        self._visitedlinks = VisitedLinks(os.path.join(profile_path,
                                                       "visitedlinks.db"))
        self._autofill = Autofill(PasswordDb(os.path.join(profile_path,
                                                          "autofill.db")))
        default_profile.setCachePath(os.path.join(path, "cache"))
        default_profile.downloadRequested.connect(
            self._download_manager.download_requested
        )

        def inject_js(src, ipoint=QWebEngineScript.DocumentCreation,
                      iid=QWebEngineScript.ApplicationWorld):
            script = QWebEngineScript()
            script.setInjectionPoint(ipoint)
            script.setSourceCode(src)
            script.setWorldId(iid)
            default_profile.scripts().insert(script)

        for script in (":/qtwebchannel/qwebchannel.js",
                       os.path.join(THIS_DIR, "scripts", "textedit.js"),
                       os.path.join(THIS_DIR, "scripts", "autofill.js"),
                       os.path.join(THIS_DIR, "scripts", "setup.js"),):
            f = QFile(script)
            assert f.open(QFile.ReadOnly | QFile.Text)
            inject_js(QTextStream(f).readAll())
