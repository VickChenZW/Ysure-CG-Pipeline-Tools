import hou

import os, json, re

from datetime import datetime

os.add_dll_directory("{}/bin".format(os.environ["HFS"]))

# from PySide2 import QtWidgets,QtCore,QtUiTools,QtGui
from PySide2.QtWidgets import (QWidget, QLabel, QComboBox, QPushButton,
                               QHBoxLayout, QVBoxLayout, QTabWidget,
                               QTableView, QListWidget, QListWidgetItem,
                               QLineEdit, QTextEdit, QDialog, QStackedLayout,
                               QCheckBox)
from PySide2.QtGui import QIcon, QFont, QPixmap, QColor
from PySide2.QtCore import QSize ,Qt, QMimeData, QModelIndex

base_dir = os.path.dirname(os.path.abspath(__file__))

pattern_name = r"^(.*?)(?:_v\d{3}\.\w+)$"
pattern_version = r'(?<=_v)\d+(?![\d_]*\b_v)'
pattern_render_folder = r'\d{8}_(.*?)(?:_v\d{3})'

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

class select_user(QDialog):
    def __init__(self,parent):
        super(select_user, self).__init__(parent)

        self._user_path = ""

        label = QLabel("输出节点生成器")
        self.setWindowIcon(QIcon(os.path.join(base_dir, "icon", "Y_black.ico")))

        btn_fbx = QPushButton("FBX")
        btn_fbx.clicked.connect(lambda :print(hou.selectedNodes()[0]))
        btn_abc = QPushButton("ABC")
        btn_rs = QPushButton("RS代理")

        layout_btn = QHBoxLayout()
        [layout_btn.addWidget(i) for i in [btn_fbx, btn_abc, btn_rs]]

        layout_user = QHBoxLayout()
        self.user_combo = QComboBox()
        self.task_combo = QComboBox()

        [layout_user.addWidget(i) for i in [self.user_combo, self.task_combo]]


        self.change_user_combo()

        self.setWindowTitle("选择导出对象")
        self.setFixedSize(QSize(300,400))
        self.layout = QVBoxLayout()
        self.layout.addWidget(label)
        self.layout.addLayout(layout_btn)
        self.layout.addLayout(layout_user)
        self.setLayout(self.layout)

    def get_user_path(self):
        self._user_path = hou.hipFile.path()
        for _ in range(3):
            self._user_path = os.path.dirname(self._user_path)

    def change_user_combo(self):
        self.user_combo.clear()
        self.get_user_path()
        for i in os.listdir(self._user_path):
            self.user_combo.addItem(i)
        self.user_combo.currentIndexChanged.connect(self.get_task_list)


    def get_task_list(self):
        self.task_combo.clear()
        for i in os.listdir(os.path.join(self._user_path,self.user_combo.currentText())):
            self.task_combo.addItem(i)

    def fbx(self):
        node = hou.Node.createNode("rop_FBX")



class rop_manager(QWidget):
    def __init__(self):
        super().__init__()

        btn = QPushButton("debug")
        btn.clicked.connect(self.change_render_parm)

        btn_changeRender = QPushButton("渲染节点")
        btn_changeRender.clicked.connect(self.change_render_parm)
        btn_addNull = QPushButton("空节点")
        btn_addNull.clicked.connect(self.add_null)
        btn_addCache = QPushButton("缓存节点")
        btn_addCache.clicked.connect(self.add_cache)

        self.cache_list = QListWidget()
        self.cache_list.setStyleSheet("font-size:20px;}")

        btn_open_folder = QPushButton("打开")
        btn_open_folder.clicked.connect(self.open_cache_folder)
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.load_cache_list)
        btn_debug = QPushButton("test")
        btn_debug.clicked.connect(self.openuser_select)

        self.version_list = QListWidget()
        self.version_list.currentItemChanged.connect(self.get_info)
        self.data_label = QLabel()
        self.from_label = QLabel()


        tool_layout = QHBoxLayout()
        tool_layout.addWidget(btn_addNull)
        tool_layout.addWidget(btn_addCache)
        tool_layout.addWidget(btn_changeRender)

        cache_tool_layout = QVBoxLayout()
        cache_tool_layout.addWidget(btn_open_folder)
        cache_tool_layout.addWidget(btn_refresh)
        cache_tool_layout.addWidget(btn_debug)

        info_layout = QVBoxLayout()
        info_layout.addWidget(self.version_list)
        info_layout.addWidget(self.data_label)
        info_layout.addWidget(self.from_label)


        cache_layout = QHBoxLayout()
        cache_layout.addLayout(cache_tool_layout)
        cache_layout.addWidget(self.cache_list)
        cache_layout.addLayout(info_layout)

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
        project_base_name = os.path.splitext(hou.hipFile.basename())[0]
        content_name = re.match(pattern_name,hou.hipFile.basename()).group(1)
        version = 1
        excluded_files = {"metadata", ".DS_Store"}
        for i in os.listdir(render_path):
            if not i in excluded_files:
                # print(i)
                parts = i.split("_")[1:-1]
                name_part = "_".join(parts)
                # print(name_part)
                project_name = re.match(pattern_render_folder, i).group(1)
                ver_part = int(i.split("_v")[-1])
                if project_name == content_name and ver_part >= version:
                    version = ver_part + 1
                # print(ver_part)

        ver_str = str(version).zfill(3)
        new_render_path = f'$HIP/render/{data}_{project_base_name}_v{ver_str}/$OS.$F4.exr'
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
        cache.parm("basedir").set("$HIP/geo/HCache")
        cache.parm('tpostrender').set(True)
        cache.parm("postrender").set(os.path.join(base_dir,'py_scripts','create_render_info_json.py').replace("\\","/"))
        cache.parm("lpostrender").set('python')
        cache.setInput(0, sel, 0)
        cache.moveToGoodPosition(True, False)

    def load_cache_list(self):
        nodes = hou.node("/obj").allSubChildren()
        self.cache_list.clear()
        count = 0
        for node in nodes:
            if node.type().name() == "filecache::2.0":
                name = node.name()
                version = node.parm("version").eval()

                path = os.path.dirname(node.parm("sopoutput").eval())
                info = {
                    "node_path":node.path(),
                    "path":path
                }
                if node.parm("trange").eval() ==1:
                    start = int(node.parm("f1").eval())
                    end = int(node.parm("f2").eval())
                    list_name = f'{name}  v{version}  F{start}-{end}'
                else:
                    # print(node.parm("trange").eval())
                    list_name = f'{name}  v{version}  单帧'
                item = QListWidgetItem(list_name)
                item.setData(Qt.UserRole, info)
                if node.isGenericFlagSet(hou.nodeFlag.Bypass):
                    item.setTextColor(QColor("yellow"))
                elif node.evalParm('loadfromdisk') == 1:
                    item.setTextColor(QColor("green"))
                else:
                    item.setTextColor(QColor("grey"))

                self.cache_list.addItem(item)
                count += 1
        self.cache_list.doubleClicked.connect(self.local_node)
        self.cache_list.currentItemChanged.connect(self.load_version)

    def local_node(self,path):
        info = path.data(Qt.UserRole)
        node: hou.Node = hou.node(info['node_path'])
        panel: hou.PaneTab = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        panel.setPwd(node.parent())
        node.setSelected(True, False)
        node.setGenericFlag(hou.nodeFlag.Template, True)

    def open_cache_folder(self):
        item = self.cache_list.currentItem()
        info = item.data(Qt.UserRole)
        path = info["path"]
        os.startfile(os.path.abspath(path))

    def load_version(self,value):
        if value:
            self.version_list.clear()
            info = value.data(Qt.UserRole)
            verison_path = os.path.dirname(os.path.abspath(info['path']))
            # print(verison_path)
            if os.path.exists(verison_path):
                for i in os.listdir(verison_path):
                    # print(i)
                    if os.path.isdir(os.path.join(verison_path,i)):
                        item = QListWidgetItem(i)
                        info = {
                            "path":os.path.join(verison_path,i)
                        }
                        item.setData(Qt.UserRole,info)
                        self.version_list.addItem(item)
                    else:
                        print("no")
                self.get_info(value)
            else:
                self.data_label.setText("缓存未创建")

    def get_info(self,value):
        if value:
            info = value.data(Qt.UserRole)
            path = info['path']
            json_file = os.path.join(os.path.abspath(path),'info.json')
            with open(json_file,"r+") as f:
                info_json = json.load(f)

                date = info_json['datatime']
                make = info_json['from']

                self.data_label.setText(f'创建时间：{date}')
                self.from_label.setText(f'缓存工程: {make}')

    def openuser_select(self):
        if hou.selectedNodes():
            node = hou.selectedNodes()[0]
            win = select_user(hou.qt.mainWindow())
            win.show()
        else:
            hou.ui.displayMessage("请选择一个输出节点")







