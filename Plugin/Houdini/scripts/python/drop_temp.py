import sys
import os
import hou
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
import shutil

base_dir = os.path.dirname(os.path.abspath(__file__))


class Drop(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.drop_label)

        self.setLayout(self.layout)
