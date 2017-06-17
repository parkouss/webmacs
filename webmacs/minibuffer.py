from PyQt5.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QLabel


class Minibuffer(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.label = QLabel(self)
        layout.addWidget(self.label)

        self.line_edit = QLineEdit(self)
        layout.addWidget(self.line_edit)

        self.line_edit.hide()
