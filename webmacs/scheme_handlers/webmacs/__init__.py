import os
from PyQt5.QtCore import QT_VERSION_STR, QBuffer, QFile
from PyQt5.QtWebEngineCore import QWebEngineUrlSchemeHandler
from jinja2 import Environment, PackageLoader
from ... import __version__


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
            "version": __version__,
            "qt_version": QT_VERSION_STR
        }

    @register_page
    def downloads(self):
        return {}
