import hou, os, re, sys
import shutil
import glob
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *


# Create Dirs at HIP if they dont exist
class Lazyproj(QDialog):
    def __init__(self, parent=None):
        super(Lazyproj, self).__init__()
        self.setWindowTitle("Project Collection Settings")
        self.setGeometry(400, 200, 400, 100)

        self.setStyleSheet(hou.ui.qtStyleSheet())
        layout = QVBoxLayout()
        layout.setSizeConstraint(QLayout.SetMinimumSize)

        # File type list
        self.label_dirs = QLabel("Directories to Create")
        self.dirs = QLineEdit("abc geo tex render flip comp")
        layout_form = QFormLayout()
        layout_form.addRow(self.label_dirs, self.dirs)
        layout.addLayout(layout_form)

        # ButtonBox
        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bbox.setCenterButtons(True)
        bbox.setMinimumSize(0, 40)
        bbox.accepted.connect(self.makeDirs)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

        self.setLayout(layout)

    def makeDirs(self):
        createdirs = [x for x in self.dirs.text().split()]
        hip = hou.expandString('$HIP')
        for d in createdirs:
            dd = hip + "/" + d
            if not os.path.exists(dd):
                os.makedirs(dd)
        hou.putenv('$JOB', hip)
        super(Lazyproj, self).accept()


dialog = Lazyproj()
dialog.exec_()