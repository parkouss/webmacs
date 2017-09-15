import logging

from PyQt5.QtCore import QUrl, QObject
from PyQt5.QtWebEngineWidgets import QWebEngineScript

from collections import namedtuple

from .db import PasswordEntry

FormData = namedtuple(
    "FormData",
    ("url", "username", "password", "data")
)


def create_host(url):
    host = url.host()

    if not host:
        host = url.toString()

    if url.port() != -1:
        host += ":%d" % url.port()

    return host


def url_encode_password(password):
    return QUrl.toPercentEncoding(password) \
               .replace(" ", "+") \
               .replace("~", "%6E")


class Autofill(QObject):
    def __init__(self, db, parent=None):
        QObject.__init__(self, parent)
        self._db = db

    def add_form_entry(self, url, formdata):
        host = create_host(url)
        logging.info("Saving password entry for %s", host)
        self._db.add_entry(
            PasswordEntry(host=host,
                          username=formdata.username,
                          password=formdata.password,
                          data=formdata.data)
        )

    def update_form_entry_for_url(self, url, formdata, passwords):
        for pwd in passwords:
            if formdata.username == pwd.username:
                pass

    def passwords_for_url(self, url):
        return self._db.get_entries(create_host(url))

    def complete_buffer(self, buffer, url):
        host = create_host(url)
        logging.info("checking autofill for %s", host)
        passwords = self._db.get_entries(host)
        if passwords:
            logging.info("autofilling for %s", host)
            buffer.runJavaScript("complete_form_data('%s')"
                                 % passwords[0].data.replace("'", "\\'"),
                                 QWebEngineScript.ApplicationWorld)
