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


class Bookmarks(object):
    def __init__(self, dbbath):
        self._conn = sqlite3.connect(dbbath)
        self._conn.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks
        (url TEXT PRIMARY KEY, name TEXT);
        """)

    def set(self, url, name):
        self._conn.execute("""
        INSERT OR REPLACE INTO bookmarks (url, name)
        VALUES (?, ?)
        """, (url, name))
        self._conn.commit()

    def list(self):
        return [r for r in self._conn.execute(
            "select url, name from bookmarks order by name"
        )]

    def remove(self, url):
        self._conn.execute("""
        DELETE from bookmarks WHERE url = ?
        """, (url,))
        self._conn.commit()
