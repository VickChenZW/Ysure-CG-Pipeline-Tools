import sys
from PySide2.QtWidgets import (QApplication, QDialog, QVBoxLayout,
                               QLineEdit, QPushButton, QLabel,
                               QWidget, QVBoxLayout, QMainWindow)
from PySide2.QtCore import QSize

class InputDialog(QDialog):
    def __init__(self, title, info, parent=None):
        super().__init__(parent)
        # self.init_ui()
        self.t = title
        self.i = info



        self.setWindowTitle(self.t)
        self.setMinimumSize(QSize(300,200))

        layout = QVBoxLayout()

        self.label = QLabel(self.i)
        self.line_edit = QLineEdit()
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")

        self.ok_button.clicked.connect(self.accept_and_destroy)
        self.cancel_button.clicked.connect(self.reject)

        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.ok_button)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def accept_and_destroy(self):
        self.accept()  # 关闭对话框并返回 Accepted
        self.deleteLater()  # 销毁对话框

    def get_input(self):
        return self.line_edit.text()