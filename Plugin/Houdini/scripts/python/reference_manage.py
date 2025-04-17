import sys
import os
import hou
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
import shutil

base_dir = os.path.dirname(os.path.abspath(__file__))

class ReferenceWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.image_parms = []
        self.image_paths = []
        self.model_parms = []
        self.model_paths = []

        self.layout = QVBoxLayout()

        self.button_layout = QHBoxLayout()
        self.scan_button = QPushButton('扫描')
        self.scan_button.pressed.connect(self.refresh_list)
        self.button_layout.addWidget(self.scan_button)

        self.localize_button = QPushButton('本地化')
        self.localize_button.pressed.connect(self.localize_references)
        self.button_layout.addWidget(self.localize_button)
        self.layout.addLayout(self.button_layout)

        self.tab_widget = QTabWidget()

        # 图片引用表格
        self.image_list = QTableWidget()
        self.image_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.image_list.setSelectionMode(QTableWidget.SingleSelection)
        self.image_list.cellDoubleClicked.connect(self.go_to_node)
        self.tab_widget.addTab(self.image_list, '贴图')

        # 模型引用表格
        self.model_list = QTableWidget()
        self.model_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.model_list.setSelectionMode(QTableWidget.SingleSelection)
        self.model_list.cellDoubleClicked.connect(self.go_to_node)
        self.tab_widget.addTab(self.model_list, '模型')

        self.layout.addWidget(self.tab_widget)
        self.setLayout(self.layout)

    def scan_reference(self):
        self.image_parms = []
        self.image_paths = []
        self.model_parms = []
        self.model_paths = []

        for parm, path in hou.fileReferences():
            if parm and path:
                parm_name = parm.name()
                if parm_name == 'file':
                    self.model_parms.append(parm)
                    self.model_paths.append(path)
                elif parm_name == 'tex0' or parm_name == 'env_map': # 你可以根据需要添加更多贴图参数的名称
                    self.image_parms.append(parm)
                    self.image_paths.append(path)

    def refresh_list(self):
        self.scan_reference()
        self.populate_table(self.image_list, self.image_parms, self.image_paths, ['贴图路径', '节点'])
        self.populate_table(self.model_list, self.model_parms, self.model_paths, ['模型路径', '节点'])

    def populate_table(self, table_widget, parms, paths, headers):
        table_widget.clear()
        table_widget.setRowCount(len(parms))
        table_widget.setColumnCount(len(headers))
        table_widget.setHorizontalHeaderLabels(headers)

        for index, parm in enumerate(parms):
            if parm:
                path = paths[index]
                path_item = QTableWidgetItem(path)
                node_item = QTableWidgetItem(parm.node().path())

                # 标记本地化状态
                if path.startswith('$HIP') or path.startswith('op:'):
                    path_item.setTextColor(QColor(200, 255, 200))  # 绿色表示已本地化
                else:
                    path_item.setTextColor(QColor(255, 200, 200))  # 红色表示未本地化

                table_widget.setItem(index, 0, path_item)
                table_widget.setItem(index, 1, node_item)

        table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def go_to_node(self, row, column):
        current_tab_index = self.tab_widget.currentIndex()
        if current_tab_index == 0:  # 贴图标签页
            node_path = self.image_list.item(row, 1).text()
        elif current_tab_index == 1:  # 模型标签页
            node_path = self.model_list.item(row, 1).text()
        else:
            return

        try:
            node = hou.node(node_path)
            if node:
                hou.ui.setCurrentNode(node)
                hou.ui.paneTabOfType(hou.paneTabType.SceneViewer).homeToSelection()
        except hou.Error_NodeNotFound:
            hou.ui.displayMessage("节点未找到: {}".format(node_path))

    def localize_references(self):
        hip_path = hou.hipFile.path()
        if not hip_path:
            hou.ui.displayMessage("请先保存你的 Houdini 文件。")
            return

        hip_dir = os.path.dirname(hip_path)
        local_image_dir = os.path.join(hip_dir, "tex")
        local_model_dir = os.path.join(hip_dir, "geo")

        os.makedirs(local_image_dir, exist_ok=True)
        os.makedirs(local_model_dir, exist_ok=True)

        self.localize_tab_references(self.image_list, self.image_parms, self.image_paths, local_image_dir)
        self.localize_tab_references(self.model_list, self.model_parms, self.model_paths, local_model_dir)

        self.refresh_list() # 刷新列表以显示本地化后的状态

    def localize_tab_references(self, table_widget, parms, paths, local_dir):
        for i, path in enumerate(paths):
            if path and not path.startswith('$HIP'):
                try:
                    original_path = path
                    filename = os.path.basename(original_path)
                    new_local_path = os.path.join(local_dir, filename)
                    relative_path = os.path.join("$HIP", os.path.basename(local_dir), filename)

                    if not os.path.exists(new_local_path):
                        shutil.copy2(original_path, new_local_path) # 使用 copy2 保留元数据

                    parm = parms[i]
                    if parm.isValid():
                        parm.set(relative_path)
                        hou.ui.displayMessage("已本地化: {} -> {}".format(original_path, relative_path))

                except Exception as e:
                    hou.ui.displayMessage("本地化失败: {}\n{}".format(path, e))