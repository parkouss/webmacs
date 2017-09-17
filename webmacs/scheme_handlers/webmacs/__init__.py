from PyQt5.QtCore import QT_VERSION_STR, QBuffer
from PyQt5.QtWebEngineCore import QWebEngineUrlSchemeHandler
from jinja2 import Environment, PackageLoader, TemplateNotFound
from ... import __version__


class WebmacsSchemeHandler(QWebEngineUrlSchemeHandler):
    def __init__(self, parent=None):
        QWebEngineUrlSchemeHandler.__init__(self, parent)
        self.env = Environment(
            autoescape=True,
            loader=PackageLoader(__name__),
        )

    def requestStarted(self, job):
        request = job.requestUrl().authority()

        try:
            template = self.env.get_template(request + ".html")
        except TemplateNotFound:
            return

        fn = getattr(self, "data_" + request, lambda: {})

        buffer = QBuffer(self)
        buffer.setData(template.render(**fn()).encode("utf-8"))
        job.reply(b"text/html", buffer)

    def data_version(self):
        return {
            "version": __version__,
            "qt_version": QT_VERSION_STR
        }
