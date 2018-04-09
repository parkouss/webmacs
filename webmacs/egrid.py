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

from PyQt5.QtWidgets import QLayout
from PyQt5.QtCore import QRect, QSize


class LayoutEntry(object):
    VERTICAL = 1
    HORIZONTAL = 2

    def __init__(self, parent=None, item=None):
        self.parent = parent
        self.item = item
        self.split = None
        self.children = []

    def do_split(self, item, direction):
        assert self.item
        if self.parent and self.parent.split == direction:
            index = self.parent.children.index(self)
            self.parent.children.insert(
                index+1,
                LayoutEntry(parent=self.parent, item=item))
        else:
            self.split = direction
            self.children.append(LayoutEntry(parent=self, item=self.item))
            self.children.append(LayoutEntry(parent=self, item=item))
            self.item = None

    def pop(self):
        assert self.parent
        parent = self.parent
        parent.children.remove(self)
        # if there is only one sibling left, replace the parent by
        # this sibling.
        if len(parent.children) == 1:
            other = parent.children[0]
            parent.item = other.item
            parent.split = other.split
            parent.children = other.children
            parent.parent = other.parent
            for child in parent.children:
                child.parent = parent

    def set_geometry(self, rect):
        if self.item:
            self.item.setGeometry(rect)

        elif self.split == self.VERTICAL:
            x = rect.x()
            width = rect.width() / len(self.children)
            for child in self.children:
                cr = QRect(x, rect.y(), width, rect.height())
                child.set_geometry(cr)
                x += width

        elif self.split == self.HORIZONTAL:
            y = rect.y()
            height = rect.height() / len(self.children)
            for child in self.children:
                cr = QRect(rect.x(), y, rect.width(), height)
                child.set_geometry(cr)
                y += height

    def __iter__(self):
        entries = [self]
        while entries:
            entry = entries.pop(0)
            yield entry
            entries.extend(entry.children)

    def entry_for_item(self, item):
        for entry in self:
            if entry.item == item:
                return entry
        return None


class EGridLayout(QLayout):
    def __init__(self, main_widget, parent=None):
        QLayout.__init__(self, parent)
        self._item_added = None
        self._root = LayoutEntry()
        self.add_widget(main_widget, self._root)

    def add_widget(self, widget, parent_entry, direction=None):
        self.addWidget(widget)
        item = self._item_added
        self._item_added = None
        if direction is not None:
            parent_entry.do_split(item, direction)
        else:
            parent_entry.item = item

    def entries(self):
        return [e for e in self._root if e.item]

    def items(self):
        return [e.item for e in self._root if e.item]

    def addItem(self, item):
        self._item_added = item

    def count(self):
        return len(self.items())

    def itemAt(self, index):
        try:
            return self.items()[index]
        except IndexError:
            return None

    def takeAt(self, index):
        return self.entries()[index].pop()

    def sizeHint(self):
        size = QSize(0, 0)
        for item in self.items():
            size = size.expandedTo(item.sizeHint())

        return size + self.count() * QSize(self.spacing(), self.spacing())

    def setGeometry(self, rect):
        self._root.set_geometry(rect)

    def insert_widget_right(self, reference, widget):
        refindex = self.indexOf(reference)
        refitem = self.itemAt(refindex)
        for entry in self._root:
            if entry.item == refitem:
                self.add_widget(widget, entry, entry.VERTICAL)
                self.invalidate()
                break

    def insert_widget_bottom(self, reference, widget):
        refindex = self.indexOf(reference)
        refitem = self.itemAt(refindex)
        for entry in self._root:
            if entry.item == refitem:
                self.add_widget(widget, entry, entry.HORIZONTAL)
                self.invalidate()
                break
