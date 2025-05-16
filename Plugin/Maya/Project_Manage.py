import maya.cmds as cmds

import os, json, re

from datetime import datetime

# os.add_dll_directory("{}/bin".format(os.environ["HFS"]))

# from PySide2 import QtWidgets,QtCore,QtUiTools,QtGui
from PySide2.QtWidgets import *
from PySide2.QtGui import QIcon, QFont, QPixmap
from PySide2.QtCore import QSize ,Qt, QMimeData, QModelIndex

# base_dir = os.path.dirname(os.path.abspath(__file__))

pattern_name = r"^(.*?)(?:_v\d{3}\.\w+)$"
pattern_version = r'(?<=_v)\d+(?![\d_]*\b_v)'
pattern_flipbook = r'^(.*)_v(\d{3})_(.*?)$'

class InputDialog(QDialog):
    """
    用于获取单行文本输入的通用对话框。
    创建文件夹使用
    """

    def __init__(self, title, info, parent=None):
        super().__init__(parent)

        self.t = title
        self.i = info

        self.setWindowTitle(self.t)
        self.setMinimumSize(QSize(300, 200))

        layout = QVBoxLayout()

        self.label = QLabel(self.i)
        self.line_edit = QLineEdit()
        self.ok_button = QPushButton("升级")
        self.cancel_button = QPushButton("取消")

        self.ok_button.clicked.connect(self.accept_and_destroy)
        self.cancel_button.clicked.connect(self.reject)

        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.ok_button)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def accept_and_destroy(self):
        self.accept()  # 关闭对话框并返回 Accepted
        self.deleteLater()  # 销毁对话框

    def get_input(self):
        return self.line_edit.text()



class project_manage(QWidget):
    def __init__(self):
        super().__init__()

        self.var_content = {
                    'project_name' : '',
                    'project_path' : '',
                    'data_path' : '',
                    'content_name' : '',
                    'current_version' : ''
                    }
        self.change_var()


        path_label = QLabel("工程名称")
        self.path_combo = QComboBox()
        self.path_combo.setMinimumWidth(300)
        self.path_combo.currentIndexChanged.connect(self.load_projects)

        icon_size = QSize(50,50)

        update_button = QPushButton("升级")
        # update_button.setIcon(QIcon(os.path.join(base_dir,"icon","updata.ico")))
        # update_button.setMinimumSize(icon_size)
        update_button.clicked.connect(self.update_project)

        path_refresh = QPushButton("刷新")
        # path_refresh.setIcon(QIcon(os.path.join(base_dir,"icon","refresh.ico")))
        path_refresh.setToolTip("刷新")
        path_refresh.pressed.connect(self.change_combo)


        new_button = QPushButton("新建")
        # new_button.setIcon(QIcon(os.path.join(base_dir,"icon","new.ico")))
        new_button.setMinimumSize(icon_size)
        new_button.setToolTip("新建文件")

        load_button = QPushButton("打开")
        # load_button.setIcon(QIcon(os.path.join(base_dir,"icon","open.ico")))
        load_button.setMinimumSize(icon_size)
        load_button.clicked.connect(self.open_folder)

        self.list_project = QListWidget()
        self.list_project.doubleClicked.connect(self.open_hip)
        self.list_project.currentItemChanged.connect(self.change_label)

        self.notes_label = QLineEdit()
        self.notes_label.setMinimumHeight(150)
        self.notes_label.setAlignment(Qt.AlignTop)
        self.notes_label.editingFinished.connect(self.change_notes)

        self.modify_label = QLineEdit()

        self.flipbook_list = QListWidget()
        self.flipbook_list.setMinimumHeight(400)

        path_layout = QHBoxLayout()
        tool_layout = QVBoxLayout()
        list_layout = QHBoxLayout()
        info_layout = QVBoxLayout()
        self.layout = QVBoxLayout()

        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_combo)
        path_layout.addStretch()
        path_layout.addWidget(update_button)
        path_layout.addWidget(path_refresh)

        tool_layout.addWidget(load_button)
        tool_layout.addWidget(new_button)
        # tool_layout.addWidget(update_button)
        # tool_layout.addStretch()

        info_layout.addWidget(self.modify_label)
        info_layout.addWidget(self.notes_label)
        info_layout.addWidget(self.flipbook_list)
        info_layout.addStretch()


        list_layout.addLayout(tool_layout)
        list_layout.addWidget(self.list_project)
        list_layout.addLayout(info_layout)

        self.layout.addLayout(path_layout)
        self.layout.addLayout(list_layout)

        self.setLayout(self.layout)

        # self.change_combo()

    def change_combo(self):
        self.path_combo.clear()
        self.change_var()
        data_file = self.var_content['data_path']
        path = cmds.file(query=True, sceneName=True)
        content_name = re.match(pattern_name, os.path.basename(path)).group(1)
        print(path)
         # = re.match(pattern_name, hou.hipFile.basename()).group(1)
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as file:
                projects = json.load(file)
                unique_contents = set(item['content'] for item in projects if 'content' in item and item.get('dcc') == 'Maya')
                index = 0
                for content in unique_contents:
                    self.path_combo.addItem(content)
                    if content == content_name:
                        self.path_combo.setCurrentIndex(index)
                    index += 1

    def change_var(self):
        # path = hou.hipFile.path()
        # name = hou.hipFile.basename()
        path = cmds.file(query=True, sceneName=True)
        name = os.path.basename(path)
        # print(name)
        if re.match(pattern_name, name):
            print('ok')
            content_name = re.match(pattern_name,name).group(1)
            version = int(re.findall(pattern_version,name)[-1])
            data_path = os.path.join(os.path.dirname(path),'metadata','project.json')
            self.var_content={
                'project_name': name,
                'project_path': path,
                'data_path': data_path,
                'content_name': content_name,
                'current_version': version
            }
            # print(self.var_content)
        return self.var_content

    def load_projects(self):
        self.change_var()
        project_name = self.path_combo.currentText()
        self.list_project.clear()
        data_file = self.var_content['data_path']
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as file:
                projects = json.load(file)

            for project in projects:
                content_name = project['content']
                version = project['version']
                notes = project['notes']
                path = project['path']
                project_info = {}
                if content_name ==project_name:
                    project_info = {
                        'content': content_name,
                        'version': version,
                        'path': path,
                        'notes': notes
                    }
                    item_text = f"{content_name} v{version}"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole,project_info)
                    self.list_project.addItem(item)

    def open_hip(self,value:QModelIndex):
        data = value.data(Qt.UserRole)
        name = value.data(Qt.DisplayRole)
        path = data['path']
        # print(path)
        # if hou.ui.displayMessage(f'是否打开{name}？', buttons = ("是","不打开"), close_choice=1) == 0:
        #     hou.hipFile.load(path)


    def change_label(self,value):
        if value:
            data = value.data(Qt.UserRole)
            self.notes_label.setProperty("path",data['path'])
            self.notes_label.setText(data['notes'])
            modify_time = os.path.getmtime(data['path'])
            mtime = datetime.fromtimestamp(int(modify_time))
            self.modify_label.setText(str(mtime))

            self.flipbook_list.clear()
            content_name = data['content']
            version = data['version']
            flipbook_path = os.path.join(os.path.dirname(data['path']), 'flipbook', content_name)
            if os.path.exists(flipbook_path):
                files = sorted((f for f in os.listdir(flipbook_path)),
                               key=lambda f: os.path.getmtime(os.path.join(flipbook_path, f)), reverse=True)
                for i in files:
                    match = re.match(pattern_flipbook, i)
                    flip_ver = match.group(2)
                    if int(flip_ver) == int(version):
                        ftime = match.group(3).split('.')[0]
                        item = QListWidgetItem(ftime)
                        dic = {
                            'path': os.path.join(flipbook_path,i)
                        }
                        item.setData(Qt.UserRole, dic)
                        self.flipbook_list.addItem(item)
            self.flipbook_list.itemDoubleClicked.connect(lambda value:os.startfile(value.data(Qt.UserRole)['path']))

    def change_notes(self):
        value = self.notes_label.text()
        data_file = self.var_content['data_path']
        with open(data_file, 'r+', encoding='utf-8') as file:
            projects = json.load(file)
            updated_projects = []
            # if value is None:
            #     new_text = ""
            for project in projects:
                if project['path'] == self.notes_label.property('path'):
                    project['notes'] = value
                updated_projects.append(project)
                file.seek(0)
                file.truncate()
                json.dump(updated_projects, file, ensure_ascii=False, indent=4)
        self.load_projects()

    # def update_project(self):
    #     content_name = self.var_content['content_name']
    #     data_file = self.var_content['data_path']
    #     if hou.ui.displayMessage("确认升级吗?", buttons=("确认", "取消")) == 0:
    #         with open(data_file, 'r+', encoding='utf-8') as file:
    #             projects = json.load(file)
    #             latest_project = None
    #
    #             for project in projects:
    #                 if project['content'] == content_name and (
    #                         latest_project is None or project['version'] > latest_project['version']):
    #                     latest_project = project
    #
    #             if latest_project:
    #                 new_version = latest_project['version'] + 1
    #                 current_notes = latest_project['notes']
    #                 new_notes = hou.ui.readInput("输入新的描述",buttons=("确定","取消"),title="输入新的描述", initial_contents=current_notes)
    #                 new_path = os.path.join(os.path.dirname(self.var_content['project_path']),f'{self.var_content["content_name"]}_v{str(new_version).zfill(3)}.hip').replace("\\", "/")
    #                 if new_notes[0] ==0:
    #                     new_project = {
    #                         'content': content_name,
    #                         'version': new_version,
    #                         'user': latest_project['user'],
    #                         'dcc': latest_project['dcc'],
    #                         'path': new_path,
    #                         'notes': new_notes[1]
    #                     }
    #                     projects.append(new_project)
    #                     file.seek(0)
    #                     json.dump(projects, file, ensure_ascii=False, indent=4)
    #                     try:
    #                         hou.hipFile.save(new_path)
    #                         hou.ui.displayMessage("更新成功")
    #                     except hou.OperationFailed as e:
    #                         hou.ui.displayMessage(e)

        self.load_projects()

    def update_project(self):
        """执行递增保存操作"""

        scene_path = cmds.file(query=True, sceneName=True)
        content_name = re.match(pattern_name, os.path.basename(scene_path)).group(1)
        # version = int(re.findall(pattern_version,os.path.basename(scene_path))[-1])


        # 获取文件类型 (mayaAscii 或 mayaBinary)
        current_file_type = cmds.file(query=True, type=True)
        if not current_file_type: # 如果是新场景，可能没有类型
             current_file_type = ['mayaAscii'] # 默认为 ma
        # 确保拿到的是字符串
        if isinstance(current_file_type, list):
            current_file_type = current_file_type[0]

        # 根据类型确定扩展名
        file_extension = ".ma" if current_file_type == "mayaAscii" else ".mb"


        scene_dir = os.path.dirname(scene_path)
        filename = os.path.basename(scene_path)

        data_file = os.path.join(os.path.dirname(scene_path), 'metadata', 'project.json').replace('//', '/')
        with open(data_file, 'r+', encoding='utf-8') as file:
            projects = json.load(file)
            latest_project = None
            for project in projects:
                if project['content'] == content_name and (
                        latest_project is None or project['version'] > latest_project['version']):
                    latest_project = project

            if latest_project:
                new_version = latest_project['version'] + 1
                new_filepath = os.path.join(scene_dir, f'{content_name}_v{str(new_version).zfill(3)}{file_extension}').replace('\\', '/')
                print(new_filepath)
                current_notes = latest_project['notes']

                input_box = InputDialog("输入备注", current_notes)
                if input_box.exec_() == InputDialog.Accepted:
                    new_notes = input_box.get_input()
                    new_project = {
                        'content': content_name,
                        'version': new_version,
                        'user': latest_project['user'],
                        'dcc': 'Maya',
                        'path': new_filepath,
                        'notes': new_notes
                    }
                    print(new_project)
                    projects.append(new_project)
                    try:
                        # 先重命名，再保存。这会更新Maya窗口标题栏
                        cmds.file(rename=new_filepath)
                        saved_path = cmds.file(save=True, type=current_file_type)
                        print(f"文件已成功保存到: {saved_path}")
                        # 可选：显示一个短暂的消息
                        # cmds.inViewMessage(amg='文件已保存: <hl>{}</hl>'.format(os.path.basename(saved_path)), pos='midCenter', fade=True, fadeStayTime=2000)
                        file.seek(0)
                        json.dump(projects, file, ensure_ascii=False, indent=4)

                        self.load_projects()

                    except RuntimeError as e:
                        cmds.warning(f"保存文件时出错: {e}")
                        QMessageBox.warning(self, "保存失败", f"无法保存文件到:\n{new_filepath}\n\n错误: {e}")



        # --- 执行保存 ---

    def open_folder(self):
        os.startfile(os.path.dirname(cmds.file(query=True, sceneName=True)))

    # def debug(self):
    #     value = hou.hipFile.path()
    #     # print(value)
    #     self.load_projects()