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

from . import call_later, BUFFERS
from .webview import WebView


class LayoutEntry(object):

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

        elif self.split == ViewGridLayout.VERTICAL:
            x = rect.x()
            width = rect.width() / len(self.children)
            for child in self.children:
                cr = QRect(x, rect.y(), width, rect.height())
                child.set_geometry(cr)
                x += width

        elif self.split == ViewGridLayout.HORIZONTAL:
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


class ViewGridLayout(QLayout):
    VERTICAL = 1
    HORIZONTAL = 2

    def __init__(self, window=None):
        QLayout.__init__(self)
        self._window = window
        main_view = WebView(window)
        # keep an ordered list of the widgets
        self._views = []
        self._current_view = main_view
        # to avoid asking reordering many times
        self.__view_sort_asked = False
        self._item_added = None
        self._root = LayoutEntry()
        self.add_view(main_view, self._root)

    def current_view(self):
        return self._current_view

    def set_current_view(self, widget):
        assert widget in self._views
        self._current_view = widget

    def views(self):
        return self._views

    def __sort_views_by_position(self):
        def top_top_bottom(w):
            return w.geometry().center().y()

        def left_to_right(w):
            return w.geometry().center().x()

        self._views = sorted(self._views, key=top_top_bottom)
        self._views = sorted(self._views, key=left_to_right)
        self.__view_sort_asked = False

    def _sort_views_by_position(self):
        # compress requests for reordering widgets
        if self.__view_sort_asked:
            return
        self.__view_sort_asked = True
        call_later(self.__sort_views_by_position)

    def add_view(self, widget, parent_entry, direction=None):
        self.addWidget(widget)
        self._views.append(widget)
        self._sort_views_by_position()
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
            self._views.remove(entry.item.widget())
            self._sort_views_by_position()
        return entry.pop()

    def sizeHint(self):
        size = QSize(0, 0)
        for entry in self.entries():
            size = size.expandedTo(entry.item.sizeHint())

        return size + self.count() * QSize(self.spacing(), self.spacing())

    def setGeometry(self, rect):
        self._root.set_geometry(rect)

    def split_view(self, direction, reference=None):
        widget = WebView(self._window)
        refindex = self.indexOf(reference or self._current_view)
        refitem = self.itemAt(refindex)
        for entry in self._root:
            if entry.item == refitem:
                self.add_view(widget, entry, direction)
                self.invalidate()
                break
        return widget

    def dump_state(self):
        def item_dump_state(entry):
            if entry.item is None:
                return {
                    "split": ("horizontal"
                              if entry.split == self.HORIZONTAL
                              else "vertical"),
                    "views": [item_dump_state(c) for c in entry.children]
                }
            else:
                view = entry.item.widget()
                buffer_index = BUFFERS.index(view.buffer())
                if view == self._current_view:
                    return {"buffer": buffer_index, "current": True}
                else:
                    return {"buffer": buffer_index}

        return item_dump_state(self._root)

    def restore_state(self, grid_data):
        buffers = list(BUFFERS)

        main_view = self._current_view

        def restore(data, view):
            split = data.get("split")

            if split is None:
                # attach the buffer to the view. Note the global variable
                # BUFFERS is modified by this call, we reset it later
                view.setBuffer(buffers[data["buffer"]])
                if data.get("current"):
                    self._current_view = view

            else:
                # we have splits to do.
                split = (self.HORIZONTAL if split == "horizontal"
                         else self.VERTICAL)

                # first split everything, to create the views
                rest = [(data["views"][0], view)]
                for wdata in data["views"][1:]:
                    view = self.split_view(split, view)
                    rest.append((wdata, view))

                # and now let's recurse to set nested buffers
                for wdata, view in rest:
                    restore(wdata, view)

        restore(grid_data, main_view)

        # put back buffer order
        BUFFERS.clear()
        BUFFERS.extend(buffers)

        # and update the focus of the views
        for w in self._views:
            w.show_focused(w == self._current_view)

        # required to have the right keyboard focus
        self._current_view.set_current()
