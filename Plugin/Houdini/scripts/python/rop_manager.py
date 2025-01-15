import shutil

import hou, toolutils, subprocess

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

# class select_user(QDialog):
#     def __init__(self,parent):
#         super(select_user, self).__init__(parent)
#
#         self._user_path = ""
#
#         self.layout = QVBoxLayout()
#         self.setWindowIcon(QIcon(os.path.join(base_dir, "icon", "Y_black.ico")))
#
#         label = QLabel("输出节点生成器")
#         label.setMinimumHeight(30)
#         self.layout.addWidget(label)
#
#         self.format_combo = QComboBox()
#         [self.format_combo.addItem(i) for i in ['FBX', 'ABC', 'RS_Proxy']]
#         self.layout.addWidget(self.format_combo)
#
#         layout_user = QHBoxLayout()
#         self.user_combo = QComboBox()
#         self.task_combo = QComboBox()
#         [layout_user.addWidget(i) for i in [self.user_combo, self.task_combo]]
#         self.layout.addLayout(layout_user)
#
#         self.notes_label = QLineEdit('输入备注')
#         self.notes_label.setMinimumHeight(60)
#         self.layout.addWidget(self.notes_label)
#
#         btn_Confirm = QPushButton("创建输出节点")
#         btn_Confirm.clicked.connect(self.run)
#         self.layout.addWidget(btn_Confirm)
#
#         self.layout.addStretch()
#
#         self.change_user_combo()
#         self.setWindowTitle("选择导出对象")
#         self.setFixedSize(QSize(300,400))
#
#
#         self.setLayout(self.layout)
#
#     def get_user_path(self):
#         self._user_path = hou.hipFile.path()
#         for _ in range(3):
#             self._user_path = os.path.dirname(self._user_path)
#
#     def change_user_combo(self):
#         self.user_combo.clear()
#         self.get_user_path()
#         for i in os.listdir(self._user_path):
#             self.user_combo.addItem(i)
#         self.user_combo.currentIndexChanged.connect(self.get_task_list)
#
#
#     def get_task_list(self):
#         self.task_combo.clear()
#         for i in os.listdir(os.path.join(self._user_path,self.user_combo.currentText())):
#             self.task_combo.addItem(i)
#
#     def get_path(self):
#         root_path = hou.hipFile.path()
#         for _ in range(3):
#             root_path = os.path.dirname(root_path)
#         des_path = os.path.join(root_path,self.user_combo.currentText(),self.task_combo.currentText(),'__IN__')
#
#         return des_path
#
#     def change_pram(self,rop_node):
#         rop_node.parm('sopoutput').set(f'{self.get_path()}/$OS.fbx'.replace('\\','/'))
#
#
#         rop_node.parm("user_text").disable(True)
#         rop_node.parm("user_text").set(self.user_combo.currentText())
#
#         rop_node.parm("takes_text").disable(True)
#         rop_node.parm("takes_text").set(self.task_combo.currentText())
#
#         rop_node.parm("notes").set(self.notes_label.text())
#
#         rop_node.parm('tpostrender').set(True)
#         rop_node.parm("postrender").set(os.path.join(base_dir,'py_scripts','create_out_info_json.py').replace("\\","/"))
#         rop_node.parm("lpostrender").set('python')
#
#     def rop_out(self):
#         dic = {
#             "FBX": "rop_fbx",
#             "ABC": "rop_alembic",
#             "RS_Proxy": "Redshift_Proxy_Output"
#         }
#
#         out_format = self.format_combo.currentText()
#         selected_node: hou.Node = hou.selectedItems()[0]
#         rop_node: hou.Node = selected_node.parent().createNode(dic[out_format], f'Rop_{selected_node.name()}')
#         parm_group: hou.ParmTemplateGroup = rop_node.parmTemplateGroup()
#         folder = hou.FolderParmTemplate("folder", "导出选项")
#
#
#         user_text = hou.StringParmTemplate("user_text", "发送给", 1)
#         user_text.setJoinWithNext(True)
#
#         takes_text = hou.StringParmTemplate("takes_text", "项目", 1)
#
#         string_parm = hou.StringParmTemplate("notes", "Notes", 1)
#         string_parm.setTags({"editor": "1"})
#
#         folder.addParmTemplate(user_text)
#         folder.addParmTemplate(takes_text)
#         folder.addParmTemplate(string_parm)
#
#         parm_group.append(folder)
#
#         rop_node.setInput(0, selected_node, 0)
#         rop_node.moveToGoodPosition(True, False)
#
#         rop_node.setParmTemplateGroup(parm_group)
#
#         self.change_pram(rop_node)
#
#     def run(self):
#         if "rop" in hou.selectedItems()[0].type().name():
#             self.change_pram(hou.selectedItems()[0])
#         else:
#             self.rop_out()

class Flipbook(QDialog):

    def __init__(self,parent):
        super(Flipbook,self).__init__(parent)

        self.project_name = re.match(pattern_name,hou.hipFile.basename()).group(1)
        # print(self.project_name)
        self.start = 0
        self.end = 0
        self.mp4_output_path = ""
        self.jpg_output_path = ""


        self.setWindowTitle("Ysure拍屏工具")

        self.layout = QVBoxLayout()
        frame_layout = QHBoxLayout()

        self.start_text = QLineEdit(str(int(hou.playbar.frameRange()[0])))
        self.end_text = QLineEdit(str(int(hou.playbar.frameRange()[1])))
        frame_layout.addWidget(self.start_text)
        frame_layout.addWidget(self.end_text)
        self.layout.addLayout(frame_layout)

        btn_run = QPushButton("开始拍屏")
        btn_run.clicked.connect(self.run)
        self.layout.addWidget(btn_run)

        self.setLayout(self.layout)

    def out_flip(self):
        # Parent dir of folder containing the hip_file_path
        flip_path = os.path.join(os.path.dirname(hou.hipFile.path()), "flipbook",self.project_name)
        if not os.path.exists(flip_path):
            print("创建flipbook文件夹")
            os.makedirs(flip_path)


        os.makedirs(os.path.join(flip_path, 'cache'))

        self.mp4_output_path = os.path.join(flip_path,hou.getenv('HIPNAME') + "_" + datetime.now().strftime('%Y-%m-%d %H-%M-%S')+'.mp4')
        self.jpg_out_path = os.path.join(flip_path, 'cache', 'cache.$F4.jpg')
        flbk_settings = toolutils.sceneViewer().flipbookSettings().stash()

        # Set the output path
        flbk_settings.output(self.jpg_out_path)

        flbk_settings.outputToMPlay(1)


        flbk_settings.useResolution(1)
        resx, resy = self.get_cam()
        flbk_settings.resolution((resx,resy))
        flbk_settings.frameRange((int(self.start_text.text()),int(self.end_text.text())))


        # self.start = flbk_settings.frameRange()[0]
        # self.end = flbk_settings.frameRange()[1]
        inc = flbk_settings.frameIncrement()


        # Launch the flipbook
        toolutils.sceneViewer().flipbook(viewport=None, settings=flbk_settings, open_dialog=False)

        print("缓存生成成功!")


    def run_ffmpeg(self):
        ffmpeg_command = [
            'ffmpeg',
            '-framerate', str(hou.fps()),
            '-start_number', self.start_text.text(),
            '-i', 'cache.%04d.jpg',  # 假设图片名称模式为 test.0100.png 到 test.0130.png
            '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            self.mp4_output_path  # 输出文件位置
        ]
        # ffmpeg_command = 'ffmpeg'
        # ffmpeg_command += ' -framerate ', str(hou.fps())
        print("启动ffmpeg!")

        try:
            result = subprocess.run(
                ffmpeg_command,
                cwd=os.path.dirname(self.jpg_out_path),  # 更改当前工作目录到图像序列所在目录
                check=True,  # 如果命令返回非零退出状态，则抛出CalledProcessError异常
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("视频生成成功:", result.stdout.decode())
            shutil.rmtree(os.path.dirname(self.jpg_out_path))
            print("缓存文件删除成功!!")
        except subprocess.CalledProcessError as e:
            shutil.rmtree(os.path.dirname(self.jpg_out_path))
            print("视频生成失败:", e.stderr.decode())



    def get_cam(self):
        viewer:hou.GeometryViewport = toolutils.sceneViewer().selectedViewport()
        # viewport:hou.GeometryViewport = viewer.viewports()[0]
        cam:hou.ObjNode = viewer.camera()
        if cam:
            resx = cam.parm("resx").eval()
            resy = cam.parm("resy").eval()
            return int(resx),int(resy)

        else:
            return 1920,1080

    def run(self):
        self.out_flip()
        self.run_ffmpeg()

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
        btn_addOut = QPushButton("输出节点")
        btn_addOut.clicked.connect(self.add_out)

        self.cache_list = QListWidget()
        self.cache_list.setStyleSheet("font-size:20px;}")

        btn_open_folder = QPushButton("打开")
        btn_open_folder.clicked.connect(self.open_cache_folder)
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.load_cache_list)
        btn_flipbook = QPushButton("拍屏")
        btn_flipbook.clicked.connect(self.make_flipbook)

        # btn_debug = QPushButton("test")
        # btn_debug.clicked.connect(self.make_flipbook)

        self.version_list = QListWidget()
        self.version_list.currentItemChanged.connect(self.get_info)
        self.data_label = QLabel()
        self.from_label = QLabel()


        tool_layout = QHBoxLayout()
        tool_layout.addWidget(btn_addNull)
        tool_layout.addWidget(btn_addCache)
        tool_layout.addWidget(btn_changeRender)
        tool_layout.addWidget(btn_addOut)

        cache_tool_layout = QVBoxLayout()
        cache_tool_layout.addWidget(btn_open_folder)
        cache_tool_layout.addWidget(btn_refresh)
        cache_tool_layout.addWidget(btn_flipbook)

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

    def add_out(self):
        if hou.selectedNodes():
            sel = hou.selectedNodes()[0]
            # name = node.name()
            if hou.ui.displayMessage("name", buttons=("use:" + sel.name(), "custom"), close_choice=0) == 0:
                name = "Rop_" + sel.name()
            else:
                name = "Rop_" + hou.ui.readInput("custom_name")[1]
            out_node = sel.parent().createNode("rop_ysure",name)
            out_node.setInput(0, sel, 0)
            out_node.moveToGoodPosition(True, False)

    def make_flipbook(self):
        flipbook = Flipbook(hou.qt.mainWindow())
        flipbook.show()
        # flipbook.out_flip()
        # flipbook.run_ffmpeg()








