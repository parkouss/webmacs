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

from . import call_later


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
        # keep an ordered list of the widgets
        self._widgets = []
        self._current_widget = main_widget
        # to avoid asking reordering many times
        self.__widget_sort_asked = False
        self._item_added = None
        self._root = LayoutEntry()
        self.add_widget(main_widget, self._root)

    def current_widget(self):
        return self._current_widget

    def set_current_widget(self, widget):
        self._current_widget = widget

    def widgets(self):
        return self._widgets

    def __sort_widgets_by_position(self):
        def top_top_bottom(w):
            return w.geometry().center().y()

        def left_to_right(w):
            return w.geometry().center().x()

        self._widgets = sorted(self._widgets, key=top_top_bottom)
        self._widgets = sorted(self._widgets, key=left_to_right)
        self.__widget_sort_asked = False

    def _sort_widgets_by_position(self):
        # compress requests for reordering widgets
        if self.__widget_sort_asked:
            return
        self.__widget_sort_asked = True
        call_later(self.__sort_widgets_by_position)

    def add_widget(self, widget, parent_entry, direction=None):
        self.addWidget(widget)
        self._widgets.append(widget)
        self._sort_widgets_by_position()
        item = self._item_added
        self._item_added = None
        if direction is not None:
            parent_entry.do_split(item, direction)
        else:
            parent_entry.item = item

    def entries(self):
        return [e for e in self._root if e.item]

    def addItem(self, item):
        self._item_added = item

    def count(self):
        return len(self.entries())

    def itemAt(self, index):
        try:
            return self.entries()[index].item
        except IndexError:
            return None

    def takeAt(self, index):
        entry = self.entries()[index]
        if entry.item:
            self._widgets.remove(entry.item.widget())
            self._sort_widgets_by_position()
        return entry.pop()

    def sizeHint(self):
        size = QSize(0, 0)
        for entry in self.entries():
            size = size.expandedTo(entry.item.sizeHint())

        return size + self.count() * QSize(self.spacing(), self.spacing())

    def setGeometry(self, rect):
        self._root.set_geometry(rect)

    def insert_widget_right(self, widget, reference=None):
        refindex = self.indexOf(reference or self._current_widget)
        refitem = self.itemAt(refindex)
        for entry in self._root:
            if entry.item == refitem:
                self.add_widget(widget, entry, entry.VERTICAL)
                self.invalidate()
                break

    def insert_widget_bottom(self, widget, reference=None):
        refindex = self.indexOf(reference or self._current_widget)
        refitem = self.itemAt(refindex)
        for entry in self._root:
            if entry.item == refitem:
                self.add_widget(widget, entry, entry.HORIZONTAL)
                self.invalidate()
                break
