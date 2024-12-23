import hou

import os, json, re

from datetime import datetime

os.add_dll_directory("{}/bin".format(os.environ["HFS"]))

# from PySide2 import QtWidgets,QtCore,QtUiTools,QtGui
from PySide2.QtWidgets import (QWidget, QLabel, QComboBox, QPushButton,
                               QHBoxLayout, QVBoxLayout, QTabWidget,
                               QTableView, QListWidget, QListWidgetItem,
                               QLineEdit, QTextEdit)
from PySide2.QtGui import QIcon, QFont, QPixmap
from PySide2.QtCore import QSize ,Qt, QMimeData, QModelIndex

base_dir = os.path.dirname(os.path.abspath(__file__))

pattern_name = r"^(.*?)(?:_v\d{3}\.\w+)$"
pattern_version = r'(?<=_v)\d+(?![\d_]*\b_v)'

def get_date():
    now = datetime.now()
    year = str(now.year)
    month = now.month
    day = now.day
    if month<10:
        month = "0" + str(month)
    else:
        month = str(month)

    if day<10:
        day = "0" + str(day)
    else:
        day = str(day)

    date = year + month + day
    return date

class rop_manager(QWidget):
    def __init__(self):
        super().__init__()

        btn = QPushButton("debug")
        btn.clicked.connect(self.change_render_parm)

        btn_changeRender = QPushButton("渲染节点")
        btn_addNull = QPushButton("空节点")
        btn_addNull.clicked.connect(self.add_cache)
        btn_addCache = QPushButton("缓存节点")
        btn_addCache.clicked.connect(self.add_cache)

        self.cache_list = QListWidget()

        btn_open_folder = QPushButton("打开")
        btn_local= QPushButton("定位")


        tool_layout = QHBoxLayout()
        tool_layout.addWidget(btn_addNull)
        tool_layout.addWidget(btn_addCache)
        tool_layout.addWidget(btn_changeRender)

        cache_tool_layout = QVBoxLayout()
        cache_tool_layout.addWidget(btn_open_folder)
        cache_tool_layout.addWidget(btn_local)


        cache_layout = QHBoxLayout()
        cache_layout.addLayout(cache_tool_layout)
        cache_layout.addWidget(self.cache_list)

        self.layout = QVBoxLayout()
        self.layout.addLayout(tool_layout)
        self.layout.addLayout(cache_layout)
        # self.layout.addWidget(btn)
        self.setLayout(self.layout)
    def change_render_parm(self):
        # $YYYY$MM$DD_$prj_v001
        node:hou.Node = hou.selectedNodes()[0]
        render_path_parm:hou.Parm = node.parm('RS_outputFileNamePrefix')
        render_path = os.path.join(os.path.dirname(hou.hipFile.path()),"render")
        data = get_date()
        content_name = os.path.splitext(hou.hipFile.basename())[0]
        version = 1
        excluded_files = {"metadata", ".DS_Store"}
        for i in os.listdir(render_path):
            if not i in excluded_files:
                # print(i)
                parts = i.split("_")[1:-1]
                name_part = "_".join(parts)
                # print(name_part)
                ver_part = int(i.split("_")[-1].split('v')[-1])
                if name_part == content_name and ver_part >= version:
                    version = ver_part + 1
                # print(ver_part)

        ver_str = str(version).zfill(3)
        new_render_path = f'$HIP/render/{data}_{content_name}_v{ver_str}/$OS.$F4.exr'
        render_path_parm.set(new_render_path)
        aov_path_parms = node.parms()
        for p in aov_path_parms:
            if 'RS_aovCustomPrefix' in p.name():
                index = p.name().split("_")[-1]
                aov_name = node.parm('RS_aovSuffix_'+index).eval()
                p.set(f'{os.path.dirname(new_render_path)}/{aov_name}/$OS.{aov_name}.$F4.exr')

    def add_null(self):
        nodes = hou.selectedItems()
        if len(nodes):
            node = nodes[0]
            pnode = node.parent()
            num = hou.ui.displayMessage("usefor", buttons=("Render", "Preview", "Out"))
            if num == 0:
                nullnode = pnode.createNode("null", "Render")
                nullnode.setRenderFlag(True)
            elif num == 1:
                nullnode = pnode.createNode("null", "Preview")
                nullnode.setDisplayFlag(True)
            else:
                nodename = pnode.name()
                nullnode = pnode.createNode("null", "Out_" + nodename)
            nullnode.setInput(0, node, 0)
            nullnode.moveToGoodPosition(True, False)
        else:
            print("non_selected")

    def add_cache(self):

        sel = hou.selectedItems()[0]
        if hou.ui.displayMessage("name", buttons=("use:" + sel.name(), "custom"), close_choice=0) == 0:
            name = "Cache_" + sel.name()
        else:
            name = "Cache_" + hou.ui.readInput("custom_name")[1]
        # name += "_" + get_date()
        cache:hou.Node= sel.parent().createNode("filecache::2.0", name)
        cache.parm("filemethod").set("constructed")
        # cache.parm("file").set("$HIP/geo/$OS/$OS.$F.bgeo.sc")
        cache.parm("basename").set("$OS")
        cache.parm("basedir").set("$HIP/geo")
        cache.parm('tpostrender').set(True)
        cache.parm("postrender").set(os.path.join(base_dir,'py_scripts','create_render_info_json.py').replace("\\","/"))
        cache.parm("lpostrender").set('python')
        cache.setInput(0, sel, 0)
        cache.moveToGoodPosition(True, False)



