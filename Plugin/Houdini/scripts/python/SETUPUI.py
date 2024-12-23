from functools import cache
import os
import hou
import datetime
import toolutils
from PySide2 import QtWidgets,QtCore,QtUiTools,QtGui
try:
    import VickTools
except:
    from ProjectSetting import VickTools

class SetUpUI(VickTools.vicktools):
    
    def __init__(self):
        super().__init__()
        super().SetUI()
