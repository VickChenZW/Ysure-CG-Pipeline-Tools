import os
import hou
from PySide2 import QtWidgets

class ProjectManage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        
        # create widgets
        self.label=QtWidgets.QLabel("Hello")
        self.textbox=QtWidgets.QInputDialog("D:/source/HoudiniPackages/VickHoudiniTool/scripts/python/ProjectSetting/test.ui")
        
        # MainLayout
        mainLayout=QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.textbox)

        # # Add Layout
        # mainLayout.addWidget(self.label)
        # mainLayout.addWidget(self.textbox)

        # # set Layout
        self.setLayout(mainLayout)

        self.debug()

    def debug(self):
        self.text=self.textbox
        # print (self.text)
        
