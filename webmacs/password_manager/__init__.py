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


from .. import require, variables

import json

from PyQt5.QtCore import QObject
from PyQt5.QtWebEngineWidgets import QWebEngineScript
from collections import namedtuple


password_managers = {
    "none": lambda: BasePaswordManager(),
    "passwordstore":
        lambda: require("webmacs.password_manager.password_store").Pass()
}


password_manager = variables.define_variable(
    "password-manager",
    """Which password manager to use.

- none: no password manager
- passwordstore: the standard unix password manager.
    """,
    "none",
    type=variables.String(choices=password_managers.keys()),
)


def make_password_manager():
    return password_managers[password_manager.value]()


Credentials = namedtuple(
    "Credentials",
    ("username", "password", "fields")
)


class BasePaswordManager(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)

    def credential_for_url(self, url):
        "Get credentials for the given url"

    def complete_buffer(self, buffer, credential):
        """Fill buffer with the given credentials"""
        dct = json.dumps(credential._asdict())
        buffer.runJavaScript(
            f"password_manager.complete_form_data({dct})",
            QWebEngineScript.ApplicationWorld)
