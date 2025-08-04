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

import Project_Manage, Asset_Manage

pattern_name = r"^(.*?)(?:_v\d{3}\.\w+)$"
pattern_version = r'(?<=_v)\d+(?![\d_]*\b_v)'

base_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), '../../..'))
# 获取 Maya 主窗口指针的函数

def get_maya_main_window():
    """获取 Maya 主窗口的指针"""
    main_window_ptr = omui.MQtUtil.mainWindow()

    from shiboken2 import wrapInstance
    return wrapInstance(int(main_window_ptr), QWidget)


class MainUI(QWidget):
    """简单的流程工具 UI 类"""

    # 用于存储UI实例，防止重复打开
    tool_instance = None

    # 静态方法用于显示窗口，并确保只有一个实例
    @staticmethod
    def show_ui():
        if MainUI.tool_instance:
            if MainUI.tool_instance.isVisible():
                MainUI.tool_instance.raise_()
                MainUI.tool_instance.activateWindow()
            else:
                MainUI.tool_instance.show()
        else:
            MainUI.tool_instance = MainUI()
            MainUI.tool_instance.show()
        return MainUI.tool_instance

    def __init__(self, parent=get_maya_main_window()):
        """初始化 UI"""
        super(MainUI, self).__init__(parent)

        # 重新加载库
        importlib.reload(Project_Manage)
        importlib.reload(Asset_Manage)


        # 防止重复初始化实例变量
        if MainUI.tool_instance is not None:
             print("MainUI instance already exists. Reusing.")
             return # 直接返回，不执行后续初始化


        self.setWindowTitle("Ysure流程工具")
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
        self.setWindowIcon(QIcon(os.path.join(base_dir, "icon", "Y_black.ico")))
        self.setWindowFlags(Qt.Window)

        title_Logo = QLabel()
        title_Logo.setPixmap(QPixmap(os.path.join(base_dir, "icon", "Y.ico")))
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
        self.MainTab.addTab(Asset_Manage.AssetManage(), '资产管理')
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
        MainUI.tool_instance = None
        super(MainUI, self).closeEvent(event)


    # def set_project_from_scene(self):
    #     """将 Maya 项目设置为当前场景文件所在的文件夹"""
    #     scene_path = cmds.file(query=True, sceneName=True)
    #
    #     if not scene_path:
    #         QMessageBox.warning(self, "设置项目失败", "当前场景尚未保存，无法确定其所在文件夹。请先保存文件。")
    #         print("设置项目失败：文件未保存。")
    #         return
    #
    #     project_dir = os.path.dirname(scene_path)
    #     project_dir = project_dir.replace("\\", "/") # 确保路径使用正斜杠
    #
    #     if not os.path.exists(project_dir):
    #          QMessageBox.critical(self, "设置项目失败", f"错误：目录 '{project_dir}' 不存在！")
    #          print(f"设置项目失败：目录不存在 '{project_dir}'")
    #          return
    #
    #     try:
    #         # 设置项目工作区。openWorkspace=True 会尝试加载或创建 workspace.mel
    #         cmds.workspace(project_dir, openWorkspace=True)
    #         # 或者仅设置路径而不打开mel: cmds.workspace(directory=project_dir) 或 cmds.workspace(projectPath=project_dir)
    #         print(f"Maya 项目已设置为: {project_dir}")
    #         QMessageBox.information(self, "项目设置成功", f"Maya 项目已成功设置为:\n{project_dir}")
    #         # 可选：显示一个短暂的消息
    #         # cmds.inViewMessage(amg=f'项目已设置为: <hl>{project_dir}</hl>', pos='midCenter', fade=True, fadeStayTime=3000)
    #
    #     except RuntimeError as e:
    #         cmds.warning(f"设置项目时出错: {e}")
    #         QMessageBox.warning(self, "设置项目失败", f"设置项目到:\n{project_dir}\n\n时发生错误: {e}")


# class testUi(QWidget):
#     instance = []
#     def __init__(self, parent=None):
#         super(testUi, self).__init__(parent)
#         testUi.instance = self
#
#
#         self.setWindowFlags(Qt.Window)
#         self.setMinimumSize(QSize(300,400))
#         label = QLabel("hello")
#         layout = QHBoxLayout()
#         layout.addWidget(label)
#         self.setLayout(layout)

def showUi():
    try:
        # 先尝试关闭可能存在的旧窗口实例
        if MainUI.tool_instance is not None:
            print("Closing existing MainUI instance.")
            MainUI.tool_instance.close()

        # 使用静态方法显示 UI
        MainUI.show_ui()

    except Exception as e:
        # 打印更详细的错误信息
        import traceback
        traceback.print_exc()
        cmds.error(f"启动 SimplePipelineTool UI 时发生错误: {e}")


# # --- 启动 UI ---
if __name__ == "__main__":
    # try:
    #     # 先尝试关闭可能存在的旧窗口实例
    #     if MainUI.tool_instance is not None:
    #         print("Closing existing MainUI instance.")
    #         MainUI.tool_instance.close()
    #
    #     # 使用静态方法显示 UI
    #     MainUI.show_ui()
    #
    # except Exception as e:
    #     # 打印更详细的错误信息
    #     import traceback
    #     traceback.print_exc()
    #     cmds.error(f"启动 SimplePipelineTool UI 时发生错误: {e}")
    # # testUi.instance = testUi(parent=QApplication.activeWindow())
    # # testUi.instance.show()
    showUi()
