import os
import logging

from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtWidgets import QApplication

from . import require
from .keyboardhandler import KeyEater
from .adblock import EASYLIST, Adblocker
from .commands import COMMANDS
from .download_manager import DownloadManager
from .minibuffer import current_minibuffer
from .profile import default_profile


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
        return self.profile.visitedlinks

    def autofill(self):
        return self.profile.autofill

    def url_interceptor(self):
        return self._interceptor

    def download_manager(self):
        return self._download_manager

    def ignored_certs(self):
        return self.profile.ignored_certs

    def minibuffer_show_info(self, text):
        current_minibuffer().show_info(text)
