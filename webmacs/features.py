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

import sqlite3
from PyQt5.QtWebEngineWidgets import QWebEnginePage


class Features(object):
    def __init__(self, db_path):
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("""
        CREATE TABLE IF NOT EXISTS features
        (url TEXT,
        feature NUMBER,
        permission NUMBER,
        PRIMARY KEY(url, feature));
        """)

    def set_permission(self, url, feature, permission):
        self._conn.execute("""
        INSERT OR REPLACE INTO features (url, feature, permission)
        VALUES (?, ?, ?)
        """, (url, feature, permission))
        self._conn.commit()

    def get_permission(self, url, feature):
        permission = self._conn.execute(
            "SELECT permission FROM features WHERE url = ? AND feature = ?",
            (url, feature)).fetchone()

        if permission:
            return permission[0]
        else:
            return QWebEnginePage.PermissionUnknown
