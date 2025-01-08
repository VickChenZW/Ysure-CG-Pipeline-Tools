from PySide2.QtWidgets import (QWidget, QHBoxLayout, QListWidget,
                               QVBoxLayout, QLabel, QListWidgetItem,
                               QLineEdit, QMenu, QAction, QPushButton)
from PySide2.QtCore import Qt, QMimeData, QUrl, QPoint, QSize
from PySide2.QtGui import QDrag, QIcon, QDropEvent, QDragLeaveEvent, QColor
from  scripts import Global_Vars
import os, re, json
from datetime import datetime
from pathlib import Path

# pattern = r"^(.*?)(?:_v\d{3}\.\w+)$"
pattern_seq = re.compile(r'^(.*?)(\d{4})\..*$')
base_dir = os.path.dirname(os.path.abspath(__file__))


def get_Nuke_path(original_path):
    result = original_path
    file_count = sum(1 for item in os.listdir(original_path) if not os.path.isdir(os.path.join(original_path,item)) and not item.startswith('.'))
    print(file_count)
    for i in os.listdir(original_path):
        if os.path.isdir(os.path.join(original_path, i)):
            pass
        else:
            match = pattern_seq.match(i)
            if match:
                prefix = match.group(1)  # 获取前缀部分（包括下划线）
                number = int(match.group(2))  # 提取四位数字并转换为整数
                suffix = '.' + i.split('.')[-1]  # 获取文件后缀名
                if file_count == 1:
                    result = f"{original_path}/{i}"
                else:
                    result = f"{original_path}/{prefix}%04d{suffix}"
                break
    return result
class DraggableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(False)
        self.setDragEnabled(True)
        self.out_Ae = True

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is None:
            return

        info = item.data(Qt.UserRole)
        path = info['path']
        if self.out_Ae:
            pass
        else:
            path = get_Nuke_path(path)
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

        self.out_Ae = True

        self.list_render = DraggableListWidget()
        self.list_render.setStyleSheet("font-size:20px;}")
        self.list_render.currentItemChanged.connect(self.update_sub)

        self.btn_software_choose = QPushButton()
        self.btn_software_choose.setCheckable(True)
        self.btn_software_choose.setMinimumSize(QSize(40,40))
        self.btn_software_choose.clicked.connect(self.change_N2A)

        self.btn_refresh = QPushButton()
        self.btn_refresh.setIcon(QIcon(os.path.join(base_dir, "../icon", "refresh.ico")))
        self.btn_refresh.setMinimumSize(QSize(40,40))
        self.btn_refresh.clicked.connect(self.update_render_list)

        btn_open = QPushButton()
        btn_open.setIcon(QIcon(os.path.join(base_dir, "../icon", "open.ico")))
        btn_open.setMinimumSize(QSize(40,40))
        btn_open.clicked.connect(lambda: os.startfile(
            os.path.join(Global_Vars.Project, "2.Project", Global_Vars.User, Global_Vars.task, "render")))

        self.label_project = QLineEdit("工程来源：")
        self.label_project.setEnabled(False)
        self.label_describe = QLineEdit()
        self.label_describe.editingFinished.connect(self.change_note)
        self.label_name = QLabel()
        self.label_count = QLabel("渲染帧数")
        self.label_count.setEnabled(False)
        self.list_take = DraggableListWidget()
        self.list_take.setHidden(True)
        self.list_AOV = DraggableListWidget()


        tool_layout = QVBoxLayout()
        sublist_layer = QVBoxLayout()
        self.layout = QHBoxLayout()
        list_layout = QHBoxLayout()

        tool_layout.addWidget(self.btn_software_choose)
        tool_layout.addWidget(self.btn_refresh)
        tool_layout.addWidget(btn_open)
        tool_layout.addStretch()

        list_layout.addWidget(self.list_take)
        list_layout.addWidget(self.list_AOV)

        sublist_layer.addWidget(self.label_project)
        sublist_layer.addWidget(self.label_name)
        sublist_layer.addWidget(self.label_describe)
        sublist_layer.addWidget(self.label_count)
        sublist_layer.addLayout(list_layout)



        self.layout.addLayout(tool_layout)
        self.layout.addWidget(self.list_render)
        self.layout.addLayout(sublist_layer)

        Global_Vars.gv.user_changed.connect(self.update_render_list)

        self.setLayout(self.layout)
        self.update_render_list()
        self.change_N2A()

    def update_render_list(self):
        self.list_render.clear()
        file_list = []
        render_path = os.path.join(Global_Vars.Project, "2.Project", Global_Vars.User, Global_Vars.task,
                                   "render").replace('\\', "/")
        if render_path :
            json_path = self.create_Info()
            if os.path.exists(json_path):
                with open(json_path, "r+", encoding="utf-8") as f:
                    infos = json.load(f)
                    list = os.listdir(render_path)
                    for i in list:
                        if "metadata" not in i and ".DS_Store" not in i:
                            create_time = os.path.getctime(os.path.join(render_path,i))
                            min_time = datetime.fromtimestamp(create_time)
                            sort_info = {
                                'name': i,
                                'mtime': min_time
                            }
                            file_list.append(sort_info)
                    file_list.sort(key= lambda x: x['mtime'], reverse=True)

                    for file in file_list:
                        take = False
                        i = file['name']
                        if  "metadata" not in i and ".DS_Store" not in i:
                            existing = any(i == info['content'] for info in infos)
                            date = i.split("_")[0]
                            version = i.split("_")[-1]
                            if '.take' in i:
                                project = i.split("_")[1:-3]
                                take = True
                            else:
                                project = i.split("_")[1:-2]
                            name = "_".join(project)
                            modify_time = os.path.getctime(os.path.join(render_path,i))

                            mtime = datetime.fromtimestamp(int(modify_time)).strftime('%m%d')
                            if not existing:
                                new_info = {
                                    'content': i,
                                    'path': os.path.join(render_path, i).replace("\\", "/"),
                                    'notes': "",
                                    'take': str(take)
                                }
                                infos.append(new_info)
                                if '.take' in i:
                                    tag = f'{mtime} {name}版本{str(version).zfill(3)}(有场次)'
                                else:
                                    tag = f'{mtime} {name}版本{str(version).zfill(3)}'
                                item = QListWidgetItem(tag)
                                item.setData(Qt.UserRole, new_info)
                                self.list_render.addItem(item)
                            else:
                                for info in infos:
                                    if info["content"] == i:
                                        if info['take'] == "True":
                                            tag = f'{mtime} {name}版本{str(version).zfill(3)}(有场次)'
                                        else:
                                            tag = f'{mtime} {name}版本{str(version).zfill(3)}'
                                        item = QListWidgetItem(tag)
                                        item.setData(Qt.UserRole, info)
                                        self.list_render.addItem(item)
                    f.seek(0)
                    json.dump(infos, f, ensure_ascii=False, indent=4)

    def create_Info(self):
        info_path = os.path.join(Global_Vars.Project, "2.Project", Global_Vars.User, Global_Vars.task, "render",
                                 "metadata").replace('\\', "/")
        json_path = os.path.join(info_path, "render_info.json")
        if not os.path.exists(info_path):
            os.makedirs(info_path)

        if not os.path.exists(json_path):
            with open(json_path, "w", encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)
        return json_path

    def update_sub(self):
        self.list_AOV.clear()
        self.list_take.clear()
        item = self.list_render.currentItem()
        self.list_take.currentItemChanged.connect(None)

        if item:
            info = item.data(Qt.UserRole)
            file_name = os.path.basename(info["content"])

            self.label_project.setProperty("content", file_name)

            self.label_describe.setText(info['notes'])
            if ".take" in file_name:
                self.list_take.setHidden(False)
                self.label_project.setText(f'工程来源：{"_".join(file_name.split("_")[1:-2])}')
                self.update_take()
                self.list_take.currentItemChanged.connect(self.update_aov_list)

            else:
                self.list_take.currentItemChanged.connect(None)
                self.label_project.setText(f'工程来源：{"_".join(file_name.split("_")[1:-1])}')
                self.list_take.setHidden(True)
                self.update_aov_list(self.list_render.currentItem())


    def update_take(self):
        self.list_AOV.clear()
        self.list_take.clear()
        item = self.list_render.currentItem()
        self.list_take.currentItemChanged.connect(None)

        if item:
            info = item.data(Qt.UserRole)
            count = 0
            render_name = ""
            root_path = info['path']
            for n in os.listdir(root_path):
                if os.listdir(os.path.join(root_path,n)):
                    path = os.path.join(root_path,n).replace('\\','/')
                    name = n
                    item_take = QListWidgetItem(name)
                    item_take.setData(Qt.UserRole, {'path': path})
                    self.list_take.addItem(item_take)
            self.list_take.currentItemChanged.connect(self.update_aov_list)
            self.label_count.setText(f'帧数:{str(count)}')
            self.label_name.setText(f'渲染名:{render_name}')

    def update_aov_list(self, value):
        self.list_AOV.clear()
        if value:
            data = value.data(Qt.UserRole)
            path = data['path']
            count = 0
            render_name = ''
            for i in os.scandir(path):
                if os.path.isdir(i):
                    path = i.path
                    name = i.name
                    aov_name = name.split("_")[-1]
                    item = QListWidgetItem(aov_name)
                    item.setData(Qt.UserRole, {"path": path})
                    self.list_AOV.addItem(item)
                else:
                    count += 1
                    render_name = pattern_seq.match(i.name).group(1)[0:-1]
                    # print(i.name)
            self.label_count.setText(f'帧数:{str(count)}')
            self.label_name.setText(f'渲染名:{render_name}')
        else:
            pass

    def change_note(self):
        name = self.label_project.property("content")
        info_path = os.path.join(Global_Vars.Project, "2.Project", Global_Vars.User, Global_Vars.task, "render",
                                 "metadata").replace('\\', "/")
        json_path = os.path.join(info_path, "render_info.json")
        value = self.label_describe.text()
        if not value is None:
            new_notes = value
        else:
            new_notes = ""
        with open(json_path, "r+", encoding='utf-8') as f:
            new = []
            infos = json.load(f)
            for info in infos:
                if info["content"] == name:
                    info["notes"] = new_notes
                new.append(info)
            f.seek(0)
            f.truncate()
            json.dump(new, f, ensure_ascii=False, indent=4)
        self.update_render_list()

    def change_N2A(self):
        btn = self.btn_software_choose
        if btn.isChecked():
            btn.setIcon(QIcon(os.path.join(base_dir, "../icon", "Ae.ico")))
            self.out_Ae = True

        else:
            btn.setIcon(QIcon(os.path.join(base_dir, "../icon", "Nuke.ico")))
            self.out_Ae = False

        self.list_render.out_Ae = self.out_Ae
        self.list_AOV.out_Ae = self.out_Ae
        self.list_take.out_Ae = self.out_Ae




