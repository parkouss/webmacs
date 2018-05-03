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

import collections
from PyQt5.QtCore import QDataStream, QByteArray, QIODevice

KILLED_BUFFERS = collections.deque()


class KilledBuffer(object):
    def __init__(self, url, title, icon, history_data):
        self.url = url
        self.title = title
        self.icon = icon
        self.history_data = history_data
        KILLED_BUFFERS.appendleft(self)

    @classmethod
    def from_buffer(cls, buff):
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)
        stream << buff.history()

        return cls(
            buff.url(),
            buff.title(),
            buff.icon(),
            data
        )

    def revive(self, buff):
        buff.load(self.url)
        stream = QDataStream(self.history_data, QIODevice.ReadOnly)
        stream >> buff.history()
        KILLED_BUFFERS.remove(self)
