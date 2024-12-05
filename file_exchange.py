import os, json, sys
from PySide2.QtWidgets import (QWidget, QListWidget,
                               QLabel, QLineEdit, QMainWindow,
                                QHBoxLayout, QVBoxLayout,QPushButton
                            )
from PySide2.QtGui import QIcon, QPixmap, Qt
from PySide2.QtCore import Qt, QSize
import Function, Global_Vars

root, project, user = Function.get_ini()
dic = {
    'file_name': "",
    'version': 0,
    'date': "",
    'from': "",
    'to': "",
    'type': ""
}
Types = ['obj', 'fbx', 'abc', 'vdb', 'rs', 'usd']


class File_Exchange(QWidget):
    def __init__(self):
        super().__init__()
        self.list_In = QListWidget()
        self.task_label = QLabel(Global_Vars.task)
        btn_refresh = QPushButton("refresh")
        btn_refresh.pressed.connect(self.load_files)


        tool_layout = QVBoxLayout()
        layout = QHBoxLayout()


        tool_layout.addWidget(btn_refresh)
        layout.addLayout(tool_layout)
        layout.addWidget(self.list_In)
        self.setLayout(layout)



    def load_files(self):
        path = f'{Global_Vars.Project}/2.Project/{Global_Vars.User}/{Global_Vars.task}/__IN__'
        print(path)
        self.list_In.clear()
        for file in os.listdir(path):
            if file:
                self.list_In.addItem(file)





