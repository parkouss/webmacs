from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEnginePage


class WebBuffer(QWebEnginePage):
    """
    Represent some web page content.

    Note a parent is required, else a segmentation fault may happen when the
    application closes.
    """
    def __init__(self, parent):
        QWebEnginePage.__init__(self, parent)

    def load(self, url):
        if not isinstance(url, QUrl):
            url = QUrl(url)
        return QWebEnginePage.load(self, url)
