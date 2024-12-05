import os, json,shutil
from PySide2.QtWidgets import (
    QLabel, QTabWidget, QWidget, QPushButton,
    QHBoxLayout, QVBoxLayout, QStackedLayout, QLineEdit, QListWidget,
    QComboBox, QDialog, QDialogButtonBox,
    QTextEdit, QListWidgetItem, QMessageBox
)
from PySide2.QtCore import QSize, Qt, QMimeData, QUrl, QPoint
from PySide2.QtGui import QFont, QIcon, QDrag

from diglog import InputDialog

import Function

import Global_Vars




# 本地变量
_DCC_ = ["Blender", "C4d", "Houdini", "Maya"]
base_dir = os.path.dirname(os.path.abspath(__file__))
_format_ = ({"Blender": ".blend", "C4d": ".c4d", "Houdini": ".hip", "Maya": ".ma"})
_list =["__IN__", "tex", "geo", "abc", "vdb", "usd", "render", "flipbook", "metadata"]

class CustomButton(QPushButton):
    def __init__(self, text, index):
        super().__init__(text)
        self.index = index

class editnotesDialog(QDialog):
    def __init__(self, initial_notes):
        super().__init__()
        self.setWindowTitle("编辑备注")
        self.layout = QVBoxLayout()

        self.notes_label = QLabel("备注:")
        self.layout.addWidget(self.notes_label)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlainText(initial_notes)
        self.layout.addWidget(self.notes_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout.addWidget(button_box)

        self.setLayout(self.layout)

class ProjectDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("创建新工程")
        self.layout = QVBoxLayout()

        self.content_label = QLabel("内容名称:")
        self.layout.addWidget(self.content_label)

        self.content_edit = QLineEdit()
        self.layout.addWidget(self.content_edit)

        self.dcc_label = QLabel("使用软件：")
        self.layout.addWidget(self.dcc_label)

        self.dcc_select = QComboBox()
        for key in _format_:
            self.dcc_select.addItem(key)
        self.layout.addWidget(self.dcc_select)

        self.notes_label = QLabel("备注:")
        self.layout.addWidget(self.notes_label)

        self.notes_edit = QTextEdit()
        self.layout.addWidget(self.notes_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout.addWidget(button_box)

        self.setLayout(self.layout)

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
        file_path = project["path"]
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(file_path)])

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(item.icon().pixmap(50, 50))
        drag.setHotSpot(QPoint(25, 25))

        drop_action = drag.exec_(supportedActions)

class ProjectVersionDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("version")
        self.layout = QHBoxLayout()

        self.list = DraggableListWidget()


        self.layout.addWidget(self.list)

        self.setLayout(self.layout)

    def addItem(self,projects,content_name):
        self.list.clear()
        for project in projects:
            if project["content"] == content_name:
                item = QListWidgetItem(f"版本：{str(project['version']).zfill(3)}  {project['notes']}")
                item.setData(Qt.UserRole,project)
                self.list.addItem(item)

    # def add_Item(self, version, describe):
    #     item_text = f"版本 {version}: {describe}"
    #     self.list.addItem(item_text)

    # def add_Item(self,version,describe):
    #     self.list.addItem(version+"  "+describe)

class Work_Project(QWidget):
    def __init__(self):
        super().__init__()
        self.data_file = ""
        self.current_file = ""

        main_layout = QVBoxLayout()
        name_layout = QHBoxLayout()
        layout = QHBoxLayout()
        layout_tools = QVBoxLayout()


        project_lab = QLabel("Project name")
        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(500)
        self.change_combo()
        self.project_combo.currentIndexChanged.connect(self.load_projects)
        self.project_combo.setStyleSheet("font-size:20px;}")
        project_add = QPushButton("add")
        project_add.pressed.connect(self.add_name_input)

        btn_add_folder = QPushButton()
        btn_add_folder.setIcon(QIcon(os.path.join(base_dir,"icon","add.ico")))
        btn_add_folder.pressed.connect(self.add_path_list)
        btn_add_folder.setToolTip("增加工程文件夹层级")


        self.list_project = DraggableListWidget()
        self.list_project.doubleClicked.connect(self.edit_notes)
        self.list_project.currentItemChanged.connect(self.get_describe)
        self.list_project.setStyleSheet("font-size:20px;}")

        btn_new = QPushButton()
        btn_new.setIcon(QIcon(os.path.join(base_dir,"icon","new.ico")))
        btn_new.setMinimumSize(QSize(40,40))
        btn_new.setToolTip("新建文件")
        btn_new.pressed.connect(self.create_new_project)

        btn_open_project =QPushButton()
        btn_open_project.setIcon(QIcon(os.path.join(base_dir,"icon","open.ico")))
        btn_open_project.setToolTip("打开文件")
        btn_open_project.setMinimumSize(QSize(40,40))
        btn_open_project.pressed.connect(lambda: print(Global_Vars.Root+Global_Vars.User+Global_Vars.Project))

        btn_update = QPushButton()
        btn_update.setIcon(QIcon(os.path.join(base_dir,"icon","updata.ico")))
        btn_update.setMinimumSize(QSize(40,40))
        btn_update.setToolTip("版本升级")
        btn_update.pressed.connect(self.upgrade_selected_project)

        btn_list = QPushButton()
        btn_list.setIcon(QIcon(os.path.join(base_dir,"icon","version.ico")))
        btn_list.setMinimumSize(QSize(40,40))
        btn_list.setToolTip("查看所有版本")
        btn_list.pressed.connect(self.show_all_versions)

        btn_refresh = QPushButton()
        btn_refresh.setIcon(QIcon(os.path.join(base_dir,"icon","refresh.ico")))
        btn_refresh.setMinimumSize(QSize(40,40))
        btn_refresh.setToolTip("刷新")
        btn_refresh.pressed.connect(self.load_projects)

        self.des_lab = QLabel("describe")
        self.des_lab.setMinimumWidth(150)

        name_layout.addWidget(project_lab)
        name_layout.addWidget(self.project_combo)
        name_layout.addWidget(project_add)
        name_layout.addWidget(btn_add_folder)

        layout_tools.addWidget(btn_new)
        layout_tools.addWidget(btn_open_project)
        layout_tools.addWidget(btn_update)
        layout_tools.addWidget(btn_list)
        layout_tools.addWidget(btn_refresh)
        layout_tools.addStretch()

        # layout.addLayout(layout_btn)
        layout.addLayout(layout_tools)
        layout.addWidget(self.list_project)
        layout.addWidget(self.des_lab)


        main_layout.addLayout(name_layout)
        main_layout.addLayout(layout)

        Global_Vars.task = self.project_combo.currentText()
        self.setLayout(main_layout)

        self.get_work_path(Global_Vars.Project)
        self.load_projects()

    def get_work_path(self,text):
        self.des_lab.setText(text)
        Global_Vars.Project = text

    def add_path_list(self):
        path = Global_Vars.Project
        name = self.project_combo.currentText()
        self.data_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User+"/" + self.project_combo.currentText() + "/metadata/project.json"
        if path:
            Function.create_work_Folder(path, Global_Vars.User, name, _list)
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', encoding='utf-8') as file:
                json.dump([], file, ensure_ascii=False, indent=4)

    def add_name_input(self):
        di = InputDialog("add!", "name?")
        if di.exec_() == QDialog.Accepted:
            value = di.get_input()
            self.project_combo.addItem(value)
            if self.project_combo.count():
                self.project_combo.setCurrentIndex(1+self.project_combo.currentIndex())
            else:
                self.project_combo.setCurrentIndex(0)

    def change_combo(self):
        self.project_combo.clear()
        path = Global_Vars.Project + "/2.Project/" + Global_Vars.User
        if os.path.exists(path):
            projs = os.listdir(path)
            for proj in projs:
                self.project_combo.addItem(proj)

    # def auto_refresh_list(self):
    #     if not self.path_label:
    #         self.load_projects()
    def load_projects(self):
        # self.change_combo()
        Global_Vars.task = self.project_combo.currentText()
        self.list_project.clear()
        projects_info = {}
        self.data_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User+"/" + self.project_combo.currentText() + "/metadata/project.json"
        # print(self.data_file)
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as file:
                projects = json.load(file)

            for project in projects:
                content_name = project['content']
                version = project['version']

                if content_name not in projects_info or projects_info[content_name]['version'] < version:
                    projects_info[content_name] = {
                        'version': version,
                        'project': project
                    }
                else:
                    QMessageBox.warning(self, "警告", "工程已经存在")


            for content_name, info in projects_info.items():
                item_text = f"{content_name} v{info['version']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, info['project'])
                self.list_project.addItem(item)

    def create_new_project(self):
        self.current_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self.project_combo.currentText()
        self.data_file = self.current_file + "/metadata/project.json"
        if not os.path.exists(self.current_file):
            QMessageBox.warning(self, "警告", "请创建文件夹")
        else:
            dialog = ProjectDialog()
            if dialog.exec_() == QDialog.Accepted:
                content_name = dialog.content_edit.text().strip()
                version = 1
                dcc = dialog.dcc_select.currentText()
                format = _format_[dcc]
                notes = dialog.notes_edit.toPlainText().strip()

                if not content_name:
                    QMessageBox.warning(self, "警告", "内容名称不能为空")
                    return

                full_name = content_name+"_v" + str(version).zfill(3) + format
                self.current_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self.project_combo.currentText()
                self.data_file = self.current_file + "/metadata/project.json"
                self.copy_and_rename(dcc + format, self.current_file + "/", full_name)

                new_project = {
                    'content': content_name,
                    'version': version,
                    'user': Global_Vars.User,
                    'dcc': dcc,
                    'path': self.current_file+"/"+full_name,
                    'notes': notes
                }


            with open(self.data_file, 'r+', encoding='utf-8') as file:
                projects = json.load(file)
                projects.append(new_project)
                file.seek(0)
                json.dump(projects, file, ensure_ascii=False, indent=4)

            self.load_projects()

    def upgrade_selected_project(self):
        selected_item = self.list_project.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "警告", "请选择一个工程")
            return

        item_text = selected_item.text()
        content_name = item_text.split(' ')[0]

        self.current_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self.project_combo.currentText()
        self.data_file = self.current_file + "/metadata/project.json"
        with open(self.data_file, 'r+', encoding='utf-8') as file:
            projects = json.load(file)
            latest_project = None

            for project in projects:
                if project['content'] == content_name and (
                        latest_project is None or project['version'] > latest_project['version']):
                    latest_project = project


            if latest_project:
                new_version = latest_project['version'] + 1
                current_notes = latest_project['notes']
                dialog = editnotesDialog(current_notes)
                old_path = latest_project['path']
                new_name = content_name+"_v"+str(new_version).zfill(3)+_format_[latest_project['dcc']]
                shutil.copy(old_path,self.current_file+"/"+new_name)
                if dialog.exec_() == QDialog.Accepted:
                    new_notes = dialog.notes_edit.toPlainText().strip()
                new_project = {
                    'content': content_name,
                    'version': new_version,
                    'user': Global_Vars.User,
                    'dcc': latest_project['dcc'],
                    'path': self.current_file+"/"+new_name,
                    'notes': new_notes
                }
                projects.append(new_project)
                file.seek(0)
                json.dump(projects, file, ensure_ascii=False, indent=4)

        self.load_projects()


    def edit_notes(self, item):
        project_data = item.data(Qt.UserRole)
        index = self.list_project.currentIndex()
        content_name = project_data['content']
        version = project_data['version']
        current_notes = project_data.get('notes', '')

        dialog = editnotesDialog(current_notes)
        if dialog.exec_() == QDialog.Accepted:
            new_notes = dialog.notes_edit.toPlainText().strip()

            self.current_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self.project_combo.currentText()
            self.data_file = self.current_file + "/metadata/project.json"
            with open(self.data_file, 'r+', encoding='utf-8') as file:
                projects = json.load(file)
                updated_projects = []

                for project in projects:
                    if project['content'] == content_name and project['version'] == version:
                        project['notes'] = new_notes
                    updated_projects.append(project)
                file.seek(0)
                json.dump(updated_projects, file, ensure_ascii=False, indent=4)

            self.load_projects()
        self.list_project.setCurrentIndex(index)

    def show_all_versions(self):
        selected_item = self.list_project.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "警告", "请选择一个工程")
            return

        dialog = ProjectVersionDialog()
        item_text = selected_item.text()
        content_name = item_text.split(' ')[0]

        self.current_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self.project_combo.currentText()
        self.data_file = self.current_file + "/metadata/project.json"
        with open(self.data_file, 'r', encoding='utf-8') as file:
            projects = json.load(file)


        dialog.addItem(projects,content_name)
        dialog.list.doubleClicked.connect(self.edit_notes)
        dialog.exec_()

    def get_describe(self,item):
        if item:
            project = item.data(Qt.UserRole)
            describe = project['notes']
            self.des_lab.setText(describe)

    def copy_and_rename(self,old_name,path,newname):
        src = os.path.join(base_dir,"templates",old_name)
        des = os.path.join(path,newname)
        shutil.copy(src,des)






