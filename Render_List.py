from PySide2.QtWidgets import (QWidget, QHBoxLayout, QListWidget,
                               QVBoxLayout, QLabel, QListWidgetItem,
                               QLineEdit, QPushButton)
from PySide2.QtCore import Qt, QMimeData, QUrl, QPoint, QSize
from PySide2.QtGui import QDrag, QIcon
import Global_Vars
from Global_Vars import gv
import os, re, json
from pathlib import Path

# pattern = r"^(.*?)(?:_v\d{3}\.\w+)$"
pattern_seq = re.compile(r'^(.*?_)(\d{4})\..*$')
base_dir = os.path.dirname(os.path.abspath(__file__))

class DraggableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
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
            path = self.get_Nuke_path(path)
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(path)])

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(item.icon().pixmap(50, 50))
        drag.setHotSpot(QPoint(25, 25))

        drop_action = drag.exec_(supportedActions)

    def get_Nuke_path(self,original_path):
        files_with_numbers = []
        directory = Path(original_path)
        for entry in directory.iterdir():
            if entry.is_file():  # 只处理文件，忽略文件夹
                match = pattern_seq.match(entry.name)
                if match:
                    prefix = match.group(1)  # 获取前缀部分（包括下划线）
                    number = int(match.group(2))  # 提取四位数字并转换为整数
                    suffix = entry.suffix  # 获取文件后缀名
                    files_with_numbers.append((prefix, number, suffix))
        if not files_with_numbers:
            print("没有符合条件的文件")
            return None
        min_file = min(files_with_numbers, key=lambda x: x[1])
        max_file = max(files_with_numbers, key=lambda x: x[1])

        result = f"{original_path}/{min_file[0]}%04d{min_file[2]} {min_file[1]}-{max_file[1]}"
        print(result)
        return result

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
        self.btn_refresh.setIcon(QIcon(os.path.join(base_dir,"icon","refresh.ico")))
        self.btn_refresh.setMinimumSize(QSize(40,40))
        self.btn_refresh.clicked.connect(self.update_render_list)

        btn_open = QPushButton()
        btn_open.setIcon(QIcon(os.path.join(base_dir,"icon","open.ico")))
        btn_open.setMinimumSize(QSize(40,40))
        btn_open.clicked.connect(lambda: os.startfile(
            os.path.join(Global_Vars.Project, "2.Project", Global_Vars.User, Global_Vars.task, "render")))

        self.label_project = QLineEdit("工程来源：")
        self.label_project.setEnabled(False)
        self.label_describe = QLineEdit()
        self.label_describe.editingFinished.connect(self.change_note)
        self.label_count = QLabel("渲染帧数")
        self.label_count.setEnabled(False)
        self.list_AOV = DraggableListWidget()

        tool_layout = QVBoxLayout()
        sublist_layer = QVBoxLayout()
        self.layout = QHBoxLayout()

        tool_layout.addWidget(self.btn_software_choose)
        tool_layout.addWidget(self.btn_refresh)
        tool_layout.addWidget(btn_open)
        tool_layout.addStretch()

        sublist_layer.addWidget(self.label_project)
        sublist_layer.addWidget(self.label_describe)
        sublist_layer.addWidget(self.label_count)
        sublist_layer.addWidget(self.list_AOV)

        self.layout.addLayout(tool_layout)
        self.layout.addWidget(self.list_render)
        self.layout.addLayout(sublist_layer)

        self.setLayout(self.layout)
        self.update_render_list()
        self.change_N2A()

    def update_render_list(self):
        self.list_render.clear()
        render_path = os.path.join(Global_Vars.Project, "2.Project", Global_Vars.User, Global_Vars.task,
                                   "render").replace('\\', "/")
        if render_path:
            json_path = self.create_Info()
            with open(json_path, "r+", encoding="utf-8") as f:
                infos = json.load(f)
                list = os.listdir(render_path)
                for i in list:
                    if not "metadata" in i:
                        existing = any(i == info['content'] for info in infos)
                        date = i.split("_")[0]
                        version = i.split("_")[-1]
                        project = i.split("_")[1:-2]
                        name = "_".join(project)
                        if not existing:
                            new_info = {
                                'content': i,
                                'path': os.path.join(render_path, i).replace("\\", "/"),
                                'notes': ""
                            }
                            infos.append(new_info)
                            item = QListWidgetItem(f'{name}版本{str(version).zfill(3)}')
                            item.setData(Qt.UserRole, new_info)
                            self.list_render.addItem(item)
                        else:
                            for info in infos:
                                if info["content"] == i:
                                    item = QListWidgetItem(f'{name}版本{str(version).zfill(3)}')
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
        item = self.list_render.currentItem()

        # print(info)
        if item:
            info = item.data(Qt.UserRole)
            file_name = os.path.basename(info["content"])
            print(f'工程来源：{"_".join(file_name.split("_")[1:-1])}')
            self.label_project.setText(f'工程来源：{"_".join(file_name.split("_")[1:-1])}')
            self.label_project.setProperty("content", file_name)
            # self.load_description(path)
            self.label_describe.setText(info['notes'])
            count = 0
            for i in os.scandir(info["path"]):
                if os.path.isdir(i):
                    path = i.path
                    name = i.name
                    aov_name = name.split("_")[-1]
                    item = QListWidgetItem(aov_name)
                    item.setData(Qt.UserRole, {"path": path})
                    self.list_AOV.addItem(item)
                else:
                    count += 1
                self.label_count.setText(str(count))

    def change_note(self):
        print("finish")
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
            for i in new:
                print(i)
            f.seek(0)
            f.truncate()
            json.dump(new, f, ensure_ascii=False, indent=4)
        self.update_render_list()

    def change_N2A(self):
        btn = self.btn_software_choose
        if btn.isChecked():
            btn.setIcon(QIcon(os.path.join(base_dir,"icon","Ae.ico")))
            self.out_Ae = True

        else:
            btn.setIcon(QIcon(os.path.join(base_dir, "icon", "Nuke.ico")))
            self.out_Ae = False

        self.list_render.out_Ae = self.out_Ae




