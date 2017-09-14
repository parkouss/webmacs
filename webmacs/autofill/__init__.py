from PyQt5.QtCore import QUrl

from collections import namedtuple

FormData = namedtuple(
    "FormData",
    ("url", "username", "password", "data")
)

PasswordEntry = namedtuple(
    "PasswordEntry",
    ("id", "host", "username", "password", "data", "updated")
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
