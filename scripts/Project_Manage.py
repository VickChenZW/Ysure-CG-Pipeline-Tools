import os
from PySide2.QtWidgets import (QHBoxLayout,
                               QVBoxLayout, QWidget,
                               QPushButton, QLineEdit, QTextEdit, QListWidget, QListWidgetItem, QDialog, QMessageBox
                               )
from PySide2.QtGui import QIcon
from scripts import Function, Global_Vars
from scripts.Global_Vars import gv

base_dir = os.path.dirname(os.path.abspath(__file__))
_user = ["Neo", "Vick", "YL", "Jie", "K", "O"]
about = "制作：Vick   测试版beta v0.1"


class ListItemWithPath(QListWidgetItem):
    def __init__(self, name, path, parent=None):
        super().__init__(name, parent)
        self.project_path = path


class ProjectList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.itemDoubleClicked.connect(self.open_path)

    @staticmethod
    def open_path(item):
        path = ''
        if isinstance(item, ListItemWithPath):
            path = item.project_path
        if path:
            os.startfile(path)


class OpenSub(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("打开子文件夹")
        self.layout = QVBoxLayout()
        self.setWindowIcon(QIcon(os.path.join(base_dir, "../icon", "version.ico")))
        assets = ["Documents", "HDRI", "Image", "Model", "PS+AI", "Temp", "Texture", "Video"]
        for asset in assets:
            open_btn = QPushButton(asset)
            self.layout.addWidget(open_btn)
            open_btn.setCheckable(False)
            open_btn.setChecked(False)
            open_btn.pressed.connect(
                lambda checked=False, a=asset: os.startfile(os.path.join(Global_Vars.Project, '1.File', a)))
        self.setLayout(self.layout)


class ProjectManager(QWidget):
    def __init__(self, class_instance, header):
        super().__init__()
        self.wm = class_instance
        self.header = header

        # add widgets
        self.name_lab = QLineEdit("输入名字")
        self.en_name_lab = QLineEdit("输入英文名字")
        self.describe_lab = QTextEdit("输入描述")
        self.prj_list = ProjectList()
        btn_create_path = QPushButton("创建目录")
        btn_create_path.pressed.connect(self.create_new_project_file)
        btn_refresh = QPushButton("刷新列表")
        btn_refresh.pressed.connect(self.refresh)

        btn_set_project = QPushButton("")
        btn_set_project.setIcon(QIcon(os.path.join(base_dir, "../icon", "right.ico")))
        btn_set_project.pressed.connect(self.change_project)
        btn_edit_file = QPushButton("")
        btn_edit_file.setIcon(QIcon(os.path.join(base_dir, "../icon", "edit_file.ico")))
        btn_open_sub = QPushButton("")
        btn_open_sub.setIcon(QIcon(os.path.join(base_dir, "../icon", "version.ico")))
        btn_open_sub.pressed.connect(self.open_sub)

        # layout
        layout_create = QVBoxLayout()
        layout_list = QVBoxLayout()
        layout_main = QHBoxLayout()
        layout_set = QVBoxLayout()

        # add widget
        layout_create.addWidget(self.name_lab)
        layout_create.addWidget(self.en_name_lab)
        layout_create.addWidget(self.describe_lab)
        layout_create.addWidget(btn_create_path)

        layout_list.addWidget(self.prj_list)
        layout_list.addWidget(btn_refresh)

        layout_set.addWidget(btn_set_project)
        layout_set.addWidget(btn_open_sub)
        layout_set.addStretch()

        layout_main.addLayout(layout_create)
        layout_main.addLayout(layout_list)
        layout_main.addLayout(layout_set)

        self.List_update()
        self.setLayout(layout_main)

        gv.root_changed.connect(self.List_update)

    def create_new_project_file(self):
        name = self.name_lab.text()
        date = Function.get_date()
        en_name = self.en_name_lab.text()
        if is_chinese(en_name):
            error("英文名字不为英文！！")
        else:
            des = self.describe_lab.toPlainText()
            new_path = Global_Vars.Root + "/" + date + "_" + en_name
            Function.create_path(new_path)
            Function.create_sub_folders(new_path)
            Function.create_project_info(name, en_name, des, new_path)
        self.List_update()

    def List_update(self):
        self.prj_list.clear()
        infos = Function.get_Project_info(Global_Vars.Root)
        for info in infos:
            item = ListItemWithPath(info["name"] + "(" + info["describe"] + ")", info["path"], self.prj_list)
            self.prj_list.addItem(item)

    def refresh(self):
        self.List_update()

    def change_project(self):
        current_item = self.prj_list.currentItem()
        if isinstance(current_item, ListItemWithPath):
            print(current_item.project_path)
            _Work_Path = current_item.project_path
            self.wm.load_projects()
            Global_Vars.Project = current_item.project_path
            gv.project = current_item.project_path
            self.header.project_change(current_item.project_path)

    @staticmethod
    def open_sub():
        sub_window = OpenSub()
        sub_window.exec_()


def error(message):
    """
    报错界面显示
    :param message: 显示的报错信息
    :return: QMessageBox
    """
    
    dig = QMessageBox()
    dig.setWindowTitle("error")
    dig.setText(message)
    # button = dig.exec_()


def is_chinese(string):
    """
    检查整个字符串是否包含中文
    :param string: 需要检查的字符串
    :return: bool
    """
    for ch in string:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True

    return False
