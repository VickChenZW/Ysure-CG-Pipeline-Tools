import os
from PySide2.QtCore import QObject, Signal
from scripts import Function
Root, Project, User = Function.get_ini()

task = ""

_user = ["Neo", "Vick", "YL", "Jie", "K", "O"]

class global_Var(QObject):
    root_changed = Signal(str)
    project_changed = Signal(str)
    user_changed = Signal(str)
    task_changed = Signal(str)
    or_changed = Signal(str)
    def __init__(self):
        super().__init__()
        self._root, self._project, self._user = Function.get_ini()

    @property
    def root(self):
        return self._root


    @root.setter
    def root(self,value):
        if self._root != value:
            self._root = value
            self.root_changed.emit(value)
            self.or_changed.emit(value)

    @property
    def project(self):
        return self._project


    @project.setter
    def project(self,value):
        if self._project != value:
            self._project = value
            self.project_changed.emit(value)
            self.or_changed.emit(value)

    @property
    def user(self):
        return self._root


    @user.setter
    def user(self,value):
        if self._user != value:
            self._user = value
            self.user_changed.emit(value)
            self.or_changed.emit(value)




gv = global_Var()
