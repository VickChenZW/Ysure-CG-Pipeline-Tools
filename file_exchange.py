import os, json, sys
from PySide2.QtWidgets import (QWidget, QListWidget,
                               QLabel, QLineEdit, QMainWindow,
                                QHBoxLayout, QVBoxLayout,QPushButton,QListWidgetItem
                            )
from PySide2.QtGui import QIcon, QPixmap, Qt, QDrag
from PySide2.QtCore import Qt, QSize, QUrl, QMimeData, QPoint
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
base_dir = os.path.dirname(os.path.abspath(__file__))

class DraggableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is None:
            return

        project = item.data(Qt.UserRole)
        file_path = project['path']
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(file_path)])

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(item.icon().pixmap(50, 50))
        drag.setHotSpot(QPoint(25, 25))

        drop_action = drag.exec_(supportedActions)



class File_Exchange(QWidget):
    def __init__(self):
        super().__init__()
        self.list_In = DraggableListWidget()
        self.list_In.currentItemChanged.connect(self.changetext)





        btn_refresh = QPushButton()
        btn_refresh.setIcon(QIcon(os.path.join(base_dir,"icon","refresh.ico")))
        btn_refresh.setToolTip("刷新")
        btn_refresh.pressed.connect(self.load_files)
        btn_refresh.setMinimumSize(QSize(40,40))
        btn_open = QPushButton()
        btn_open.clicked.connect(lambda: os.startfile(f'{Global_Vars.Project}/2.Project/{Global_Vars.User}/{Global_Vars.task}/__IN__/'))
        btn_open.setIcon(QIcon(QIcon(os.path.join(base_dir,"icon","open.ico"))))
        btn_open.setToolTip("打开文件夹")
        btn_refresh.setMinimumSize(QSize(40,40))

        self.from_tex = QLineEdit()
        self.from_tex.setEnabled(False)
        self.make_tex = QLineEdit()
        self.des_lab = QLabel()

        tool_layout = QVBoxLayout()
        lab_layout = QVBoxLayout()
        layout = QHBoxLayout()


        tool_layout.addWidget(btn_refresh)
        tool_layout.addWidget(btn_open)
        lab_layout.addWidget(self.from_tex)
        lab_layout.addWidget(self.make_tex)
        lab_layout.addWidget(self.des_lab)


        layout.addLayout(tool_layout)
        layout.addWidget(self.list_In)
        layout.addLayout(lab_layout)
        self.setLayout(layout)



    def load_files(self):
        path = f'{Global_Vars.Project}/2.Project/{Global_Vars.User}/{Global_Vars.task}/__IN__/'
        # print(path)
        self.list_In.clear()
        if os.path.exists(os.path.join(path,"metadata","in.json")):
            with open(os.path.join(path,"metadata","in.json"), "r", encoding='utf-8') as f:
                files = json.load(f)

                for file in files:
                    if file:
                        item = QListWidgetItem(file['file_name'])
                        file.update({"path": path+file["file_name"]})
                        item.setData(Qt.UserRole, file)
                        # print(path + file["file_name"])
                        self.list_In.addItem(item)
        else:
            os.makedirs(os.path.join(path,"metadata"))
            with open(os.path.join(path,"metadata","in.json"),"w",encoding='utf-8') as f:
                json.dump([],f,ensure_ascii=False,indent=4)

    def changetext(self):
        item = self.list_In.currentItem()
        file = item.data(Qt.UserRole)
        self.from_tex.setText(f'发送自：{file["from"]}')
        self.make_tex.setText(f'{os.path.dirname(file["make"]).split("/")[-1]}中的{file["make"].split("/")[-1]}')
        self.des_lab.setText(file["describe"])








