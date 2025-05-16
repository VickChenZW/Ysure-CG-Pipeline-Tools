# -*- coding: utf-8 -*-

import maya.cmds as cmds
import maya.OpenMayaUI as omui
import os
import re
import sys
import json
import importlib

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

import Project_Manage

pattern_name = r"^(.*?)(?:_v\d{3}\.\w+)$"
pattern_version = r'(?<=_v)\d+(?![\d_]*\b_v)'

# base_dir = os.path.dirname(os.path.abspath(__file__))
# 获取 Maya 主窗口指针的函数

def get_maya_main_window():
    """获取 Maya 主窗口的指针"""
    main_window_ptr = omui.MQtUtil.mainWindow()

    from shiboken2 import wrapInstance
    return wrapInstance(int(main_window_ptr), QWidget)


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


class SimplePipelineToolUI(QWidget):
    """简单的流程工具 UI 类"""

    # 用于存储UI实例，防止重复打开
    tool_instance = None

    # 静态方法用于显示窗口，并确保只有一个实例
    @staticmethod
    def show_ui():
        if SimplePipelineToolUI.tool_instance:
            if SimplePipelineToolUI.tool_instance.isVisible():
                SimplePipelineToolUI.tool_instance.raise_()
                SimplePipelineToolUI.tool_instance.activateWindow()
            else:
                SimplePipelineToolUI.tool_instance.show()
        else:
            SimplePipelineToolUI.tool_instance = SimplePipelineToolUI()
            SimplePipelineToolUI.tool_instance.show()
        return SimplePipelineToolUI.tool_instance

    def __init__(self, parent=get_maya_main_window()):
        """初始化 UI"""
        super(SimplePipelineToolUI, self).__init__(parent)

        importlib.reload(Project_Manage)


        # 防止重复初始化实例变量
        if SimplePipelineToolUI.tool_instance is not None:
             print("SimplePipelineToolUI instance already exists. Reusing.")
             return # 直接返回，不执行后续初始化


        self.setWindowTitle("Ysure流程工具")
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
        # # 设置窗口标志，使其感觉像Maya工具窗口
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Tool)
        #
        # # 创建布局
        # self.main_layout = QVBoxLayout(self)
        #
        # # 创建按钮
        # self.inc_save_button = QPushButton("递增保存")
        # self.set_project_button = QPushButton("设置项目到当前文件目录")
        #
        # # 添加按钮到布局
        # self.main_layout.addWidget(self.inc_save_button)
        # self.main_layout.addWidget(self.set_project_button)
        #
        # # 连接信号和槽（按钮点击事件）
        # self.inc_save_button.clicked.connect(self.incremental_save)
        # self.set_project_button.clicked.connect(self.set_project_from_scene)
        #
        # # 应用布局
        # self.setLayout(self.main_layout)
        #
        # # 确保关闭窗口时，实例被正确清理
        # self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        title_Logo = QLabel()
        # title_Logo.setPixmap(QPixmap(os.path.join(base_dir, "icon", "Y.ico")))
        title_Logo.setScaledContents(True)
        title_Logo.setAlignment(Qt.AlignLeft)
        title_Logo.setMaximumSize(QSize(50, 50))
        title = QLabel("Ysure流程工具")

        title_fonts = QFont()
        title_fonts.setPointSize(20)
        title.setFont(title_fonts)
        title.setAlignment(Qt.AlignCenter)

        self.MainTab = QTabWidget()
        self.MainTab.addTab(Project_Manage.project_manage(), "工作文件管理")
        # self.MainTab.addTab(rop_manager.rop_manager(), "ROP管理")
        self.MainTab.addTab(asset_manage.AssetManage(), '资产管理')
        # self.MainTab.addTab(reference_manage.ReferenceWidget(), '引用管理')

        title_layout = QHBoxLayout()
        self.layout = QVBoxLayout()

        title_layout.addWidget(title_Logo)
        title_layout.addWidget(title)
        self.layout.addLayout(title_layout)
        self.layout.addWidget(self.MainTab)
        self.setStyleSheet("""
                       font-size: 20px;
                       font-family: '黑体'
                       border-radius: 5px;
                   """)

        self.setLayout(self.layout)



    def closeEvent(self, event):
        """重写 closeEvent 以清除静态实例引用"""
        SimplePipelineToolUI.tool_instance = None
        super(SimplePipelineToolUI, self).closeEvent(event)


    def incremental_save(self):
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

                    except RuntimeError as e:
                        cmds.warning(f"保存文件时出错: {e}")
                        QMessageBox.warning(self, "保存失败", f"无法保存文件到:\n{new_filepath}\n\n错误: {e}")



        # --- 执行保存 ---

    def set_project_from_scene(self):
        """将 Maya 项目设置为当前场景文件所在的文件夹"""
        scene_path = cmds.file(query=True, sceneName=True)

        if not scene_path:
            QMessageBox.warning(self, "设置项目失败", "当前场景尚未保存，无法确定其所在文件夹。请先保存文件。")
            print("设置项目失败：文件未保存。")
            return

        project_dir = os.path.dirname(scene_path)
        project_dir = project_dir.replace("\\", "/") # 确保路径使用正斜杠

        if not os.path.exists(project_dir):
             QMessageBox.critical(self, "设置项目失败", f"错误：目录 '{project_dir}' 不存在！")
             print(f"设置项目失败：目录不存在 '{project_dir}'")
             return

        try:
            # 设置项目工作区。openWorkspace=True 会尝试加载或创建 workspace.mel
            cmds.workspace(project_dir, openWorkspace=True)
            # 或者仅设置路径而不打开mel: cmds.workspace(directory=project_dir) 或 cmds.workspace(projectPath=project_dir)
            print(f"Maya 项目已设置为: {project_dir}")
            QMessageBox.information(self, "项目设置成功", f"Maya 项目已成功设置为:\n{project_dir}")
            # 可选：显示一个短暂的消息
            # cmds.inViewMessage(amg=f'项目已设置为: <hl>{project_dir}</hl>', pos='midCenter', fade=True, fadeStayTime=3000)

        except RuntimeError as e:
            cmds.warning(f"设置项目时出错: {e}")
            QMessageBox.warning(self, "设置项目失败", f"设置项目到:\n{project_dir}\n\n时发生错误: {e}")


# # --- 启动 UI ---
if __name__ == "__main__":
    try:
        # 先尝试关闭可能存在的旧窗口实例
        if SimplePipelineToolUI.tool_instance is not None:
            print("Closing existing SimplePipelineToolUI instance.")
            SimplePipelineToolUI.tool_instance.close()

        # 使用静态方法显示 UI
        SimplePipelineToolUI.show_ui()

    except Exception as e:
        # 打印更详细的错误信息
        import traceback
        traceback.print_exc()
        cmds.error(f"启动 SimplePipelineTool UI 时发生错误: {e}")