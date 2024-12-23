import hou, os, json

class global_Var():
    def __int__(self):
        self._project, self._user =""
        self.change_value()

    def change_value(self):
        path = hou.hipFile.path()
        self._project = os.path.dirname(path)
        self._user = path.split("/")[4]
