import sqlite3


class IgnoredCertificates(object):
    def __init__(self, dbbath):
        self._conn = sqlite3.connect(dbbath)
        self._conn.execute("""
        CREATE TABLE IF NOT EXISTS ignorecerts
        (url TEXT PRIMARY KEY);
        """)

    def is_ignored(self, url):
        return self._conn.execute("""
        SELECT url from ignorecerts WHERE url = ?
        """, (url,)).fetchone() is not None

    def ignore(self, url):
        self._conn.execute("""
        INSERT OR REPLACE INTO ignorecerts (url)
        VALUES (?)
        """, (url,))
        self._conn.commit()

    def remove(self, url):
        self._conn.execute("""
        DELETE from ignorecerts WHERE url = ?
        """, (url,))
