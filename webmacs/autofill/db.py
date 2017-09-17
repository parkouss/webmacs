import sqlite3
from datetime import datetime


class PasswordEntry(object):
    __slots__ = ("id", "host", "username", "password", "data", "updated")

    def __init__(self, id=None, host=None, username=None, password=None,
                 data=None, updated=None):
        self.id = id
        self.host = host
        self.username = username
        self.password = password
        self.data = data
        self.updated = updated


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
        self._conn.commit()

    def _get_entries(self, host, where):
        return [
            PasswordEntry(*row)
            for row in self._conn.execute("""
        SELECT id, host, username, password, data, updated FROM autofill
        WHERE host=? %s ORDER BY updated DESC
        """ % where, (host,))
        ]

    def get_form_entries(self, host):
        return self._get_entries(host, where="AND data IS NOT NULL")

    def get_auth_entries(self, host):
        return self._get_entries(host, where="AND data IS NULL")
