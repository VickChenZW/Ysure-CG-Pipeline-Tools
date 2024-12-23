import hou

import os, json, importlib

os.add_dll_directory("{}/bin".format(os.environ["HFS"]))

from PySide2.QtWidgets import (QWidget, QLabel, QComboBox, QPushButton,
                               QHBoxLayout, QVBoxLayout, QTabWidget,QTableView)
from PySide2.QtGui import QIcon, QFont, QPixmap
from PySide2.QtCore import QSize ,Qt, QMimeData
import project_manage
import rop_manager
# from project_manage import project_manage
base_dir = os.path.dirname(os.path.abspath(__file__))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        importlib.reload(project_manage)
        importlib.reload(rop_manager)

        title_Logo = QLabel()
        title_Logo.setPixmap(QPixmap(os.path.join(base_dir, "icon", "Y.ico")))
        title_Logo.setScaledContents(True)
        title_Logo.setAlignment(Qt.AlignLeft)
        title_Logo.setMaximumSize(QSize(50,50))
        title = QLabel("Ysure流程工具")

        title_fonts = QFont()
        title_fonts.setPointSize(20)
        title.setFont(title_fonts)
        title.setAlignment(Qt.AlignCenter)

        self.MainTab = QTabWidget()
        self.MainTab.addTab(project_manage.project_manage(), "工作文件管理")
        self.MainTab.addTab(rop_manager.rop_manager(),"ROP管理")

        title_layout = QHBoxLayout()
        self.layout = QVBoxLayout()

        title_layout.addWidget(title_Logo)
        title_layout.addWidget(title)
        self.layout.addLayout(title_layout)
        self.layout.addWidget(self.MainTab)
        self.setStyleSheet("""
                font-size: 20px;
                font-family: '黑体'
                border-radius: 5px;
            """)

        self.setLayout(self.layout)
        # importlib.reload(project_manage)
