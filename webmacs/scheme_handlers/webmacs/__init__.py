from PyQt5.QtCore import QT_VERSION_STR, QBuffer
from PyQt5.QtWebEngineCore import QWebEngineUrlSchemeHandler
from jinja2 import Environment, PackageLoader
from ... import __version__


PAGES = {}


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
        request = job.requestUrl().authority()

        if request not in PAGES:
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
