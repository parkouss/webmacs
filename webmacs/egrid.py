from PyQt5.QtWidgets import QLayout
from PyQt5.QtCore import QRect, QSize


class EGridLayout(QLayout):
    def __init__(self, main_widget, parent=None):
        QLayout.__init__(self, parent)
        self._items = []
        self.add_widget(main_widget, 0, 0)

    def add_widget(self, widget, row, col):
        self.addWidget(widget)
        item = self._items[-1]
        item._row = row
        item._col = col

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        try:
            return self._items[index]
        except IndexError:
            return None

    def takeAt(self, index):
        return self._items.pop(index)

    def sizeHint(self):
        size = QSize(0, 0)
        for item in self._items:
            size = size.expandedTo(item.sizeHint())

        return size + self.count() * QSize(self.spacing(), self.spacing())

    def setGeometry(self, rect):
        QLayout.setGeometry(self, rect)
        col_offset = {}
        row_offset = {}
        for item in self._items:
            nb_in_row = len([i for i in self._items if i._row == item._row])
            nb_in_col = len([i for i in self._items if i._col == item._col])
            x_step = rect.width() / nb_in_row
            y_step = rect.height() / nb_in_col
            try:
                start_x = row_offset[item._row]
            except KeyError:
                start_x = rect.x()
            try:
                start_y = col_offset[item._col]
            except KeyError:
                start_y = rect.y()
            ir = QRect(start_x, start_y, x_step, y_step)
            item.setGeometry(ir)
            row_offset[item._row] = start_x + x_step
            col_offset[item._col] = start_y + y_step

    def insert_widget_right(self, reference, widget):
        refindex = self.indexOf(reference)
        refitem = self.itemAt(refindex)
        self.add_widget(widget, refitem._row, refitem._col + 1)
        self.invalidate()

    def insert_widget_bottom(self, reference, widget):
        refindex = self.indexOf(reference)
        refitem = self.itemAt(refindex)
        self.add_widget(widget, refitem._row + 1, refitem._col)
        self.invalidate()
