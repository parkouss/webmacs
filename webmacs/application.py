import os
import logging

from PyQt5.QtWebEngineWidgets import QWebEngineProfile, QWebEngineScript, \
    QWebEngineSettings
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot

from . import require
from .websocket import WebSocketClientWrapper
from .keyboardhandler import KEY_EATER
from .adblock import EASYLIST, Adblocker
from .visited_links import VisitedLinks


THIS_DIR = os.path.dirname(os.path.realpath(__file__))


class UrlInterceptor(QWebEngineUrlRequestInterceptor):
    visited_link = Signal(str)

    def __init__(self, app):
        QWebEngineUrlRequestInterceptor.__init__(self)
        self.app = app
        generator = Adblocker(app.adblock_path())
        for url in EASYLIST:
            generator.register_filter_url(url)
        self._adblock = generator.generate_rules()
        self._use_adblock = True
        self._current_host = ""

    def toggle_use_adblock(self):
        self._use_adblock = not self._use_adblock

    def interceptRequest(self, request):
        url = request.requestUrl().toString()
        if request.resourceType() == request.ResourceTypeMainFrame:
            host = request.requestUrl().host()
            if host.startswith("www."):
                host = host[4:]
            self._current_host = host
            self.visited_link.emit(url)
        elif self._use_adblock and self._adblock.matches(url,
                                                         self._current_host):
            logging.info("filtered: %s", url)
            request.block(True)


class Application(QApplication):
    INSTANCE = None

    def __init__(self, args):
        QApplication.__init__(self, args)
        self.__class__.INSTANCE = self

        with open(os.path.join(THIS_DIR, "app_style.css")) as f:
            self.setStyleSheet(f.read())
        self._setup_websocket()

        self._setup_conf_paths()

        self._interceptor = UrlInterceptor(self)
        self._interceptor.visited_link.connect(self._on_visited_link)
        self._setup_default_profile(self.sock_client.port)

        self.installEventFilter(KEY_EATER)

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

    def _setup_websocket(self):
        """
        An internal websocket is used to communicate between web page content
        (using javascript) and the python code.
        """
        self.sock_client = WebSocketClientWrapper()

    def visitedlinks(self):
        return self._visitedlinks

    @Slot(str)
    def _on_visited_link(self, url):
        if self._visitedlinks:
            self._visitedlinks.visit(url)

    def url_interceptor(self):
        return self._interceptor

    def _setup_default_profile(self, port):
        default_profile = QWebEngineProfile.defaultProfile()
        default_profile.setRequestInterceptor(self._interceptor)
        path = self.profiles_path()
        profile_path = os.path.join(path, "default")
        default_profile.setPersistentStoragePath(profile_path)
        self._visitedlinks = VisitedLinks(os.path.join(profile_path,
                                                       "visitedlinks.db"))
        default_profile.setCachePath(os.path.join(path, "cache"))

        def inject_js(src, ipoint=QWebEngineScript.DocumentCreation,
                      iid=QWebEngineScript.ApplicationWorld):
            script = QWebEngineScript()
            script.setInjectionPoint(ipoint)
            script.setSourceCode(src)
            script.setWorldId(iid)
            default_profile.scripts().insert(script)

        for script in ("qwebchannel.js", "textedit.js", "setup.js"):
            with open(os.path.join(THIS_DIR, script)) as f:
                src = f.read()
            if script == "setup.js":
                src = ("var webmacsBaseUrl = 'ws://localhost:%d';\n%s"
                       % (port, src))
            inject_js(src)
        # do not let the focus on the web page if it request it. It is
        # annoying, and it causes trouble when we open new webviews.
        inject_js(
            "if (document.activeElement) { document.activeElement.blur(); }",
            QWebEngineScript.Deferred,
            QWebEngineScript.MainWorld
        )
