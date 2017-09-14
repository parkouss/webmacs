import sqlite3
from datetime import datetime
from . import create_host, PasswordEntry


class PasswordDb(object):
    def __init__(self, dbpath):
        self._conn = sqlite3.connect(dbpath)
        self._conn.execute("""
        CREATE TABLE IF NOT EXISTS autofill
        (id INTEGER PRIMARY KEY AUTOINCREMENT, host TEXT,
         username TEXT, password TEXT,  data TEXT, updated DATE)
        """)

    def add_entry(self, pe):
        self._conn.execute("""
        INSERT INTO autofill (host, username, password, data, updated)
        VALUES (?, ?, ?, ?, ?)
        """, (pe.host, pe.username, pe.password, pe.data, datetime.now()))

    def get_entries(self, url):
        return [
            PasswordEntry(*row)
            for row in self._conn.execute("""
        SELECT id, host, username, password, data, updated FROM autofill
        WHERE host=? ORDER BY last_used DESC
        """, (create_host(url),))
        ]
