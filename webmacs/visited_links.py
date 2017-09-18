import sqlite3
from datetime import datetime


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
        )]

    def remove(self, url):
        self._conn.execute("""
        DELETE from visitedlinks WHERE url = ?
        """, (url,))
