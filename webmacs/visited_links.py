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
from datetime import datetime
from . import variables


visited_links_display_limit = variables.define_variable(
    "visited-links-display-limit",
    "Limit the number of history elements displayed in the"
    " visited-links-history command.",
    2000,
    type=variables.Int(min=1)
)


class VisitedLinks(object):
    def __init__(self, dbbath):
        self._conn = sqlite3.connect(dbbath)
        self._conn.execute("""
        CREATE TABLE IF NOT EXISTS visitedlinks
        (url TEXT PRIMARY KEY, title TEXT, lastseen DATE);
        """)

    def visit(self, url, title):
        self._conn.execute("""
        INSERT OR REPLACE INTO visitedlinks (url, title, lastseen)
        VALUES (?, ?, ?)
        """, (url, title, datetime.now()))
        self._conn.commit()

    def visited_urls(self):
        return [(row[0], row[1]) for row in self._conn.execute(
            "select url, title from visitedlinks order by lastseen DESC"
            " LIMIT %d" % visited_links_display_limit.value
        )]

    def remove(self, url):
        self._conn.execute("""
        DELETE from visitedlinks WHERE url = ?
        """, (url,))
