import os
import sys
from PySide2.QtWidgets import (
    QMainWindow, QApplication,
    QLabel, QHBoxLayout,
    QVBoxLayout, QWidget, QTabWidget, QPushButton,
    QFileDialog, QLineEdit, QListWidget, QDialog, QDialogButtonBox, QAction, QStatusBar

)
from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import QFont, QDropEvent, QDragLeaveEvent, QIcon, QPixmap, QDragEnterEvent
import qdarktheme
from scripts.Work_Project import Work_Project
from scripts.Project_Manage import project_manager
from scripts.file_exchange import File_Exchange
from scripts.Render_List import render_list
from scripts.Global_Vars import gv

from scripts import address_trans, Global_Vars, Function, Temp_update

## header with logo

base_dir = os.path.dirname(os.path.abspath(__file__))

class PluginManage(QWidget):
    def __init__(self):
        super().__init__()

        self.plugin_path = {
                          'houdini': "",

                        }