from PySide2.QtWidgets import (QWidget, QHBoxLayout, QListWidget,
                               QVBoxLayout, QLabel,QListWidgetItem,
                               QLineEdit, QPushButton)
from PySide2.QtCore import Qt, QMimeData, QUrl, QPoint
from PySide2.QtGui import QDrag
import Global_Vars
from Global_Vars import gv
import os, re, json
pattern = r"^(.*?)(?:_v\d{3}\.\w+)$"
class DraggableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is None:
            return

        path = item.data(Qt.UserRole)
        # file_path = project
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(path)])

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(item.icon().pixmap(50, 50))
        drag.setHotSpot(QPoint(25, 25))

        drop_action = drag.exec_(supportedActions)

class render_list(QWidget):
    def __init__(self):
        super().__init__()
        self.list_render = DraggableListWidget()
        self.list_render.setStyleSheet("font-size:20px;}")
        self.list_render.currentItemChanged.connect(self.update_sub)

        self.btn_refresh = QPushButton("refresh")
        self.btn_refresh.clicked.connect(self.update_render_list)

        self.label_project = QLineEdit("工程来源：")
        self.label_project.setEnabled(False)
        self.label_discribe = QLineEdit()
        self.label_discribe.textChanged.connect(self.change_note)
        self.label_count = QLabel("渲染帧数")
        self.label_count.setEnabled(False)
        self.list_AOV = DraggableListWidget()

        tool_layout = QVBoxLayout()
        sublist_layer = QVBoxLayout()
        self.layout = QHBoxLayout()

        tool_layout.addWidget(self.btn_refresh)

        sublist_layer.addWidget(self.label_project)
        sublist_layer.addWidget(self.label_discribe)
        sublist_layer.addWidget(self.label_count)
        sublist_layer.addWidget(self.list_AOV)

        self.layout.addLayout(tool_layout)
        self.layout.addWidget(self.list_render)
        self.layout.addLayout(sublist_layer)


        self.setLayout(self.layout)
        self.update_render_list()
    def update_render_list(self):
        self.list_render.clear()
        render_path = os.path.join(Global_Vars.Project,"2.Project", Global_Vars.User, Global_Vars.task, "render").replace('\\', "/")
        print(render_path)
        if render_path:
            list = os.listdir(render_path)
            for i in list:
                if not "metadata" in i:
                    date = i.split("_")[0]
                    version = i.split("_")[-1]
                    project = i.split("_")[1:-2]
                    name = "_".join(project)
                    
                    item = QListWidgetItem(f'{name}版本{str(version).zfill(3)}')
                    item.setData(Qt.UserRole,os.path.join(render_path,i).replace("\\","/"))
                    self.list_render.addItem(item)


    def update_sub(self,value):
        self.list_AOV.clear()
        item:QListWidgetItem = value
        path = item.data(Qt.UserRole)
        # print(os.path.basename(path))
        file_name = os.path.basename(path)
        # self.create_Info(path)
        self.label_project.setText(f'工程来源：{"_".join(file_name.split("_")[1:-1])}')
        count = 0
        for i in os.scandir(path):
            if os.path.isdir(i):
                path = i.path
                name = i.name
                aov_name = name.split("_")[-1]
                item = QListWidgetItem(aov_name)
                item.setData(Qt.UserRole,path)
                self.list_AOV.addItem(item)
            else:
                count+=1
            self.label_count.setText(str(count))
                # self.create_Info(path)

    def create_Info(self,path):
        info_path = os.path.join(Global_Vars.Project,"2.Project", Global_Vars.User, Global_Vars.task, "render","metadata").replace('\\', "/")
        # print(info_path)
        json_path = os.path.join(info_path,"render_info.json")
        if not os.path.exists(info_path):
            os.makedirs(info_path)

        if not os.path.exists(json_path):
            with open(json_path,"w",encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)

        file_name = os.path.basename(path)
        with open(json_path,"r+",encoding='utf-8') as f:
            render_infos = json.load(f)
            existing = any(file_name == ri['content'] for ri in render_infos)
            if not existing:
                new_info = {
                    'content': file_name,
                    'path': path,
                    'notes': ""
                }
                f.seek(0)
                render_infos.append(new_info)
                json.dump(render_infos, f, ensure_ascii=False, indent=4)
                f.truncate()
        f.close()

    def change_note(self,value):
        item = self.list_render.currentItem()
        path = item.data(Qt.UserRole)
        nfo_path = os.path.join(Global_Vars.Project, "2.Project", Global_Vars.User, Global_Vars.task, "render","metadata").replace('\\', "/")
        json_path = os.path.join(info_path, "render_info.json")
        with open(json_path,"r+",encoding='utf-8') as f:
            new = []
            infos = json.load(f)
            for info in infos:
                if info["path"] == path:
                    info["note"] = value
                new.append(info)
            f.seek(0)
            json.dump(new, f, ensure_ascii=False, indent=4)









