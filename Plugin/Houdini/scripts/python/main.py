import hou, toolutils

import os, json, importlib, re

os.add_dll_directory("{}/bin".format(os.environ["HFS"]))

from PySide2.QtWidgets import (QWidget, QLabel, QComboBox, QPushButton,
                               QHBoxLayout, QVBoxLayout, QTabWidget, QTableView)
from PySide2.QtGui import QIcon, QFont, QPixmap, QDropEvent, QDragEnterEvent, QDragMoveEvent, QDragLeaveEvent
from PySide2.QtCore import QSize, Qt, QMimeData
import project_manage, rop_manager, asset_manage, reference_manage

# from project_manage import project_manage
base_dir = os.path.dirname(os.path.abspath(__file__))





class LoadFile(object):
    def __init__(self,path):
        self.path = path

        self.load_drops()

    def replace_chinese_to_underscore(self, text):
        """
        将字符串中的中文字符替换为下划线 '_'
        :param text: 需要处理的字符串
        :return: 处理后的字符串
        """
        # 中文字符的 Unicode 范围是 \u4e00-\u9fff（基本汉字区块）
        # 使用正则表达式匹配中文字符并替换为下划线
        return re.sub(r'[\u4e00-\u9fff]+', '_', text)

    def load_drops(self):
        current_panel: hou.NetworkEditor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        active_node: hou.Node = current_panel.pwd()
        if self.path:
            if os.path.isfile(self.path):
                file_name = os.path.basename(self.path)
                name = self.replace_chinese_to_underscore(os.path.splitext(file_name)[0])
                ext = os.path.splitext(file_name)[1].lower()

                if active_node.path() == '/obj':
                    geo_node: hou.Node = active_node.createNode('geo', name)
                else:
                    geo_node: hou.Node = active_node

                if ext in {'.fbx', '.obj'}:
                    file_node = geo_node.createNode('file', name)
                    file_node.parm('file').set(self.path)
                elif ext in {'.abc'}:
                    file_node = geo_node.createNode('alembic', name)
                    file_node.parm('fileName').set(self.path)
                elif ext in {'.usd', '.usda', '.usdc'}:
                    file_node = geo_node.createNode('usdimport', name)
                    file_node.parm('filepath1').set(self.path)
                elif ext in {'.ai', '.png', '.jpg', '.jpeg', '.tif'}:
                    file_node = geo_node.createNode('trace', name)
                    file_node.parm('file').set(self.path)

class DropWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setAcceptDrops(True)

        # 创建提示Label
        self.drop_label = QLabel(self)
        self.drop_label.setText("松开加载文件")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet(
            "QLabel {"
            "background-color: rgba(217, 237, 153, 0.5);"
            "border: 2px dashed #00ff00;"
            "border-radius: 10px;"
            "color: #006400;"
            "font-size: 50px;"
            "font-family: '黑体';"
            "padding: 20px;"
            "}"
        )
        self.drop_label.hide()  # 初始隐藏

        # 设置Label的大小与窗口一致
        # self.drop_label.setGeometry(self.rect())

        self.resizeEvent(None)  # 初始化时调用一次

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 使Label始终填充整个窗口
        self.drop_label.setGeometry(self.rect())

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        # 检测是否是文件拖拽
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_label.show()  # 显示提示Label
            self.drop_label.raise_()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_label.raise_()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self.drop_label.hide()  # 离开时隐藏Label
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        event.acceptProposedAction()
        self.drop_label.hide()  # 释放时隐藏Label

        # 获取文件路径
        file = event.mimeData()
        paths = [url.toLocalFile() for url in file.urls()]
        for path in paths:
            LoadFile(path)


class MainWindow(DropWidget):
    def __init__(self):
        super().__init__()
        importlib.reload(project_manage)
        importlib.reload(rop_manager)
        importlib.reload(asset_manage)
        importlib.reload(reference_manage)

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
        self.MainTab.addTab(project_manage.project_manage(), "工作文件管理")
        self.MainTab.addTab(rop_manager.rop_manager(), "ROP管理")
        self.MainTab.addTab(asset_manage.AssetManage(), '资产管理')
        self.MainTab.addTab(reference_manage.ReferenceWidget(), '引用管理')

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
        # importlib.reload(project_manage)
