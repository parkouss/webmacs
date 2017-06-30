import sqlite3
from datetime import datetime


class VisitedLinks(object):
    def __init__(self, dbbath):
        self._conn = sqlite3.connect(dbbath)
        self._conn.execute("""
        CREATE TABLE IF NOT EXISTS visitedlinks
        (url TEXT PRIMARY KEY, lastseen DATE);
        """)

    def visit(self, url):
        self._conn.execute("""
        INSERT OR REPLACE INTO visitedlinks (url, lastseen)
        VALUES (?, ?)
        """, (url, datetime.now()))
        self._conn.commit()

    def visited_urls(self):
        return [row[0] for row in self._conn.execute(
            "select url from visitedlinks order by lastseen DESC"
        )]
