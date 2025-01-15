import os, json,shutil, ctypes
import re

from PySide2.QtWidgets import (
    QLabel, QTabWidget, QWidget, QPushButton,
    QHBoxLayout, QVBoxLayout, QLineEdit, QListWidget,
    QComboBox, QDialog, QDialogButtonBox,
    QTextEdit, QListWidgetItem, QMessageBox, QTableView, QHeaderView,
    QSplitter, QTreeWidget, QTreeWidgetItem,QAbstractItemView
)
from PySide2.QtCore import (QSize, Qt, QMimeData, QUrl, QPoint,
                            QSortFilterProxyModel, Signal, QModelIndex
                            )
from PySide2.QtGui import (QIcon, QDrag, QStandardItemModel,
                           QStandardItem, QColor, QDragEnterEvent,
                           QDragLeaveEvent, QDragMoveEvent, QDropEvent)

from  scripts import Function

from datetime import datetime

from scripts import Global_Vars
from scripts.Global_Vars import gv

# 本地变量
_DCC_ = ["Blender", "C4d", "Houdini", "Maya"]
base_dir = os.path.dirname(os.path.abspath(__file__))
_format_ = ({"Blender": ".blend", "C4d": ".c4d", "Houdini": ".hip", "Maya": ".ma"})
_list =["__IN__", "tex", "geo", "alembic", "vdb", "usd", "render", "flipbook", "metadata", "reference"]
# pattern = r"^(.*?)(?:_v\d{3}\.\w+)$"

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

class InputDialog(QDialog):
    def __init__(self, title, info, parent=None):
        super().__init__(parent)
        # self.init_ui()
        self.t = title
        self.i = info
        self.setWindowIcon(QIcon(os.path.join(base_dir, "../icon", "new.ico")))

        self.setWindowTitle(self.t)
        self.setMinimumSize(QSize(300,200))

        layout = QVBoxLayout()

        self.label = QLabel(self.i)
        self.line_edit = QLineEdit()
        self.ok_button = QPushButton("创建文件夹")
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

class ProjectDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("创建新工程")
        self.layout = QVBoxLayout()
        self.setWindowIcon(QIcon(os.path.join(base_dir, "../icon", "new.ico")))
        self.content_label = QLabel("内容名称:")
        self.layout.addWidget(self.content_label)

        self.content_edit = QLineEdit()
        self.layout.addWidget(self.content_edit)

        self.dcc_label = QLabel("使用软件：")
        self.layout.addWidget(self.dcc_label)

        self.dcc_select = QComboBox()
        index = 0
        for key in _format_:
            self.dcc_select.addItem(key)
            self.dcc_select.setItemIcon(index, QIcon(os.path.join(base_dir, "../icon", key)))
            index+=1
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

class DraggableTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QTreeWidget.DragOnly)  # 设置拖拽模式为仅拖出
        self.setDefaultDropAction(Qt.CopyAction)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is None:
            return

        project = item.data(0, Qt.UserRole)
        file_path = project["path"]
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(file_path)])

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.setHotSpot(QPoint(25, 25))

        drop_action = drag.exec_(supportedActions)

class Opensub(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("打开资产文件夹")
        self.layout = QVBoxLayout()
        self.setWindowIcon(QIcon(os.path.join(base_dir, "../icon", "version.ico")))
        self.assets = {'贴图': 'tex', '参考': 'reference', '缓存': 'geo','ABC': 'alembic', 'VDB': 'vdb'}
        self.current_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + Global_Vars.task

        self.path_label = QLabel()
        self.layout.addWidget(self.path_label)

        self.tab = QTabWidget()
        self.add_ltem()
        self.tab.currentChanged.connect(self.change_path_tab)

        self.layout.addWidget(self.tab)
        self.path_label.setText(self.assets[self.tab.tabText(0)])
        self.setLayout(self.layout)

    def add_ltem(self):
        self.createFoloder()
        for key in self.assets:



            widget = QWidget()
            layout = QVBoxLayout(widget)
            list = DraggableListWidget()
            list.itemDoubleClicked.connect(lambda item,lw = list:self.open_down(item,lw))

            btn_up = QPushButton("向上一层")
            btn_up.pressed.connect(lambda lw = list:self.open_up(lw))

            btn_open = QPushButton("打开文件夹")
            btn_open.pressed.connect(lambda x=self.assets[key]:os.startfile(os.path.join(self.current_file,x)))

            layout.addWidget(list)
            layout.addWidget(btn_up)
            layout.addWidget(btn_open)
            self.tab.addTab(widget, key)
            path = os.path.join(self.current_file,self.assets[key])
            for i in os.listdir(path):
                att = ctypes.windll.kernel32.GetFileAttributesW(os.path.join(path,i))
                if  att != -1 and bool(att & 2):  ##判断是不是隐藏文件
                    pass
                else:
                    item = QListWidgetItem(i)
                    dic = {
                        'path':os.path.join(path,i)
                    }
                    if os.path.isdir(os.path.join(path,i)):
                        item.setBackgroundColor(QColor(0,50,0))
                    item.setData(Qt.UserRole,dic)
                    list.addItem(item)

    def change_path_tab(self):
        self.path_label.setText(self.assets[self.tab.tabText(self.tab.currentIndex())])
    def change_path_label(self, new_path):
        path = self.path_label.text()
        self.path_label.setText(path+"\\"+new_path)

    def open_down(self,value,list):
        data = value.data(Qt.UserRole)
        path = data['path']
        if os.path.isdir(path):
            list.clear()
            for i in os.listdir(path):
                item = QListWidgetItem(i)
                dic = {
                    'path': os.path.join(path, i)
                }
                if os.path.isdir(os.path.join(path, i)):
                    item.setBackgroundColor(QColor(0, 50, 0))
                item.setData(Qt.UserRole, dic)
                list.addItem(item)
            self.change_path_label(path.split("\\")[-1])

    def open_up(self,list):
        if not "\\" in self.path_label.text():
            pass
        else:
            self.path_label.setText(os.path.dirname(self.path_label.text()))
            path = os.path.join(os.path.join(self.current_file,self.path_label.text()))
            list.clear()
            for i in os.listdir(path):
                item = QListWidgetItem(i)
                dic = {
                    'path': os.path.join(path, i)
                }
                if os.path.isdir(os.path.join(path, i)):
                    item.setBackgroundColor(QColor(0, 50, 0))
                item.setData(Qt.UserRole, dic)
                list.addItem(item)


    def createFoloder(self):
        for key in self.assets:
            if os.path.exists(os.path.join(self.current_file,self.assets[key])):
                pass
            else:
                os.makedirs(os.path.join(self.current_file,self.assets[key]))

class Flipbook_Dialog(QDialog):
    def __init__(self,content):
        super().__init__()
        self.flip_path = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + Global_Vars.task + "/flipbook/" + content
        self.content = content
        self.setWindowTitle("拍屏文件")
        self.layout = QVBoxLayout()
        self.setWindowIcon(QIcon(os.path.join(base_dir, "../icon", "new.ico")))
        self.content_label = QLabel(self.content)
        self.content_label.setStyleSheet("font-size:20px;}")
        self.content_label.setAlignment(Qt.AlignCenter)

        self.btn_expanded = QPushButton("全部折叠")
        self.btn_expanded.clicked.connect(self.expanded)

        # self.list = DraggableListWidget()
        self.list = DraggableTreeWidget()
        self.list.setHeaderLabels(['版本','创建时间'])
        self.list.doubleClicked.connect(self.open_file)
        btn_refresh = QPushButton("刷新列表")
        btn_refresh.clicked.connect(self.add_item)
        btn_open = QPushButton("打开拍屏文件夹")
        btn_open.clicked.connect(lambda :os.startfile(self.flip_path))
        self.layout.addWidget(self.content_label)
        self.layout.addWidget(self.btn_expanded)
        self.layout.addWidget(self.list)
        self.layout.addWidget(btn_refresh)
        self.layout.addWidget(btn_open)
        self.setLayout(self.layout)
        self.add_item()

    def add_item(self):
        pattern = r'^(.*?)(?:_(v\d{3}))(?:_(.*?))$'
        self.list.clear()
        if os.path.exists(self.flip_path):
            # 获取所有文件并按版本降序排序
            files = sorted((f for f in os.listdir(self.flip_path)),
                           key=lambda f: os.path.getmtime(os.path.join(self.flip_path, f)), reverse=True)

            version_items = {}
            for i in files:
                filename = os.path.splitext(i)[0]
                group = re.match(pattern, filename)
                if group:
                    name = group.group(1)
                    version = group.group(2)
                    time = group.group(3)
                    path = os.path.join(self.flip_path, i)

                    if version not in version_items:
                        # 创建一个新的顶级项（版本）
                        version_item = QTreeWidgetItem(self.list, [version, ""])
                        version_items[version] = version_item

                    # 创建子项并添加到对应的版本项下
                    file_item = QTreeWidgetItem(version_item, ["", f"{time}"])
                    file_item.setData(0, Qt.UserRole, {"content": i, "path": path})

            # 展开所有顶级项
            for version_item in version_items.values():
                version_item.setExpanded(True)

        else:
            pass

    def open_file(self, index: QModelIndex):
        """处理双击事件"""
        if not index.isValid():
            return

        item = self.list.itemFromIndex(index)
        if item is None:
            return

        data = item.data(0, Qt.UserRole)
        if data:
            path = data["path"]
            try:
                os.startfile(path)
            except Exception as e:
                print(f"Error opening file: {e}")

    def expanded(self):
        self.list.collapseAll()

class Version_Table(QStandardItemModel):
    dataChangedSignal = Signal(int,int,str)
    def __init__(self):
        super().__init__()
        self.setHorizontalHeaderLabels(['版本', '最后修改时间', '备注'])
        self.setColumnCount(3)
    def flags(self, index):
        default_flag = super().flags(index)
        if index.isValid():
            return default_flag | Qt.ItemIsDragEnabled
        return default_flag

    def mimeTypes(self):
        return ["text/uri-list"]

    def mimeData(self, indexes):
        mime_data = QMimeData()
        item = self.item
        for index in indexes:
            if index.column() == 0:
                project = self.data(index.siblingAtColumn(0),Qt.ItemDataRole.UserRole)
                path = project["path"]
                mime_data.setUrls([QUrl.fromLocalFile(path)])
        return mime_data

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        if role == Qt.EditRole and index.column() == 2:  # Only the last column can be edited
            # Get the corresponding first column item
            first_column_item = self.item(index.row(), 0)
            if role == Qt.EditRole:
                self.dataChangedSignal.emit(index.row(),index.column(),value)
                # 调用父类的 setData 方法以确保实际的数据更新
            return super().setData(index, value, role)

class CopyToFileDialog(QDialog):
    def __init__(self, src_path):
        super().__init__()
        self.src_path = src_path
        self.assets = {'贴图': 'tex', '参考': 'reference', '缓存': 'geo', 'ABC': 'alembic', 'VDB': 'vdb'}
        self.text = ""

        self.setWindowTitle("复制到文件")
        self.setWindowIcon(QIcon(os.path.join(base_dir, "../icon", "new.ico")))

        self.layout = QVBoxLayout()

        self.label = QLabel(src_path)
        self.layout.addWidget(self.label)

        for k in self.assets:
            btn = QPushButton(k)
            btn.clicked.connect(self.clicked)
            self.layout.addWidget(btn)

        self.setLayout(self.layout)

    def clicked(self):
        button:QPushButton = self.sender()
        self.text = button.text()
        self.accept()

    def get_text(self):
        return self.text

    def get_asset(self) ->dict:
        return self.assets


class DraggableDroppableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        # self.setDragDropMode(QAbstractItemView.DragDrop)

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

    def dragEnterEvent(self, event:QDragEnterEvent):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            url = mime_data.urls()[0]
            event.acceptProposedAction()
            print(url.toLocalFile())

    def dragLeaveEvent(self, event:QDragLeaveEvent):
        print('leave')

    def dropEvent(self, event:QDropEvent) -> None:
        event.accept()
        print('move')

class Work_Project(DraggableDroppableWidget):
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


        project_add = QPushButton()
        project_add.pressed.connect(self.add_name_input)
        project_add.setIcon(QIcon(os.path.join(base_dir, "../icon", "add.ico")))
        project_add.setToolTip("增加工程文件夹层级")

        self.list_project = DraggableListWidget()
        self.list_project.doubleClicked.connect(self.get_filpbook)
        self.list_project.currentItemChanged.connect(self.get_describe)
        self.list_project.setStyleSheet("font-size:20px;}")

        self.table_version = QTableView()
        self.proxy_model = QSortFilterProxyModel()
        self.version_model = Version_Table()
        self.version_model.dataChangedSignal.connect(self.edit_version_note)
        self.proxy_model.setSourceModel(self.version_model)
        self.proxy_model.sort(1, Qt.SortOrder.DescendingOrder)
        self.table_version.setModel(self.proxy_model)
        self.table_version.setSelectionBehavior(QTableView.SelectRows)
        self.table_version.setAlternatingRowColors(True)
        self.table_version.setShowGrid(False)
        self.table_version.verticalHeader().setVisible(False)
        self.table_version.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_version.setDragEnabled(True)
        header = self.table_version.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self.on_header_clicked)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.list_project)
        splitter.addWidget(self.table_version)
        splitter.setStretchFactor(0,1)
        splitter.setStretchFactor(1,1)

        btn_new = QPushButton()
        btn_new.setIcon(QIcon(os.path.join(base_dir, "../icon", "new.ico")))
        btn_new.setMinimumSize(QSize(40,40))
        btn_new.setToolTip("新建文件")
        btn_new.pressed.connect(self.create_new_project)

        btn_open_project = QPushButton()
        btn_open_project.setIcon(QIcon(os.path.join(base_dir, "../icon", "open.ico")))
        btn_open_project.setToolTip("打开文件")
        btn_open_project.setMinimumSize(QSize(40, 40))
        btn_open_project.pressed.connect(lambda: os.startfile(f'{Global_Vars.Project}/2.Project/{Global_Vars.User}/{Global_Vars.task}'))

        btn_update = QPushButton()
        btn_update.setIcon(QIcon(os.path.join(base_dir, "../icon", "updata.ico")))
        btn_update.setMinimumSize(QSize(40, 40))
        btn_update.setToolTip("版本升级")
        btn_update.pressed.connect(self.upgrade_selected_project)

        btn_refresh = QPushButton()
        btn_refresh.setIcon(QIcon(os.path.join(base_dir, "../icon", "refresh.ico")))
        btn_refresh.setMinimumSize(QSize(40, 40))
        btn_refresh.setToolTip("刷新")
        btn_refresh.pressed.connect(self.update_list)

        btn_subfolder = QPushButton()
        btn_subfolder.setIcon(QIcon(os.path.join(base_dir, "../icon", "version.ico")))
        btn_subfolder.setMinimumSize(QSize(40, 40))
        btn_subfolder.setToolTip("打开子文件夹")
        btn_subfolder.pressed.connect(self.opensub)


        self.des_lab = QLabel("describe")
        self.des_lab.setMinimumWidth(150)

        name_layout.addWidget(project_lab)
        name_layout.addWidget(self.project_combo)
        name_layout.addWidget(project_add)
        # name_layout.addWidget(btn_add_folder)

        layout_tools.addWidget(btn_new)
        layout_tools.addWidget(btn_open_project)
        layout_tools.addWidget(btn_update)
        layout_tools.addWidget(btn_refresh)
        layout_tools.addWidget(btn_subfolder)
        layout_tools.addStretch()

        layout.addLayout(layout_tools)
        layout.addWidget(splitter)

        main_layout.addLayout(name_layout)
        main_layout.addLayout(layout)

        Global_Vars.task = self.project_combo.currentText()
        self.setLayout(main_layout)

        self.get_work_path(Global_Vars.Project)
        self.load_projects()

        gv.user_changed.connect(self.change_combo)
        gv.project_changed.connect(self.change_project)

    def get_work_path(self, text):
        self.des_lab.setText(text)
        Global_Vars.Project = text

    def change_project(self):
        self.change_combo()
        self.load_projects()

    def add_name_input(self):
        di = InputDialog("增加项目文件夹", "请输入名字")
        if di.exec_() == InputDialog.Accepted:
            value = di.get_input()
            self.project_combo.addItem(value)
            for i in range(self.project_combo.count()):
                if self.project_combo.itemText(i) == value:
                    self.project_combo.setCurrentIndex(i)
            path = Global_Vars.Project
            name = value
            self.data_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + name + "/metadata/project.json"
            if path:
                Function.create_work_Folder(path, Global_Vars.User, name, _list)
            if not os.path.exists(self.data_file):
                with open(self.data_file, 'w', encoding='utf-8') as file:
                    json.dump([], file, ensure_ascii=False, indent=4)

    def change_combo(self):
        self.project_combo.clear()
        path = Global_Vars.Project + "/2.Project/" + Global_Vars.User
        if os.path.exists(path):
            projs = os.listdir(path)
            for proj in projs:
                self.project_combo.addItem(proj)

    def load_projects(self):
        # self.change_combo()
        Global_Vars.task = self.project_combo.currentText()
        self.list_project.clear()
        projects_info = {}
        self.data_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self.project_combo.currentText() + "/metadata/project.json"
        # print(self.data_file)
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as file:
                projects = json.load(file)

            for project in projects:
                content_name = project['content']
                version = project['version']
                dcc = project['dcc']
                path = project['path']

                if content_name not in projects_info or projects_info[content_name]['version'] < version:
                    projects_info[content_name] = {
                        'version': version,
                        'project': project,
                        'dcc': dcc,
                        'path':path
                    }
                else:
                    QMessageBox.warning(self, "警告", "工程已经存在")
            for content_name, info in projects_info.items():
                path = info['path']
                modify_time = os.path.getmtime(path)
                mtime = datetime.fromtimestamp(int(modify_time)).strftime('%m%d')
                item_text = f"{mtime} {content_name} v{info['version']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, info['project'])
                item.setIcon(QIcon(os.path.join(base_dir, "../icon", info["dcc"])))
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

                exist_file = []
                with open(self.data_file, 'r+', encoding='utf-8') as file:
                    projects = json.load(file)

                    for i in projects:
                        exist_file.append(i['content'])
                file.close()

                if content_name in exist_file:
                    QMessageBox.warning(self, "警告", "文件名已经存在")
                else:
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
        content_name = item_text.split(' ')[1]

        self.current_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self.project_combo.currentText()
        self.data_file = self.current_file + "/metadata/project.json"
        if QMessageBox.question(self, "升级工程", "请确实使用外部升级\n确认保存当前工程了") == QMessageBox.StandardButton.Yes:
            print("ok")
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
                    new_name = content_name + "_v" + str(new_version).zfill(3) + _format_[latest_project['dcc']]
                    if dialog.exec_() == QDialog.Accepted:
                        shutil.copy(old_path, self.current_file + "/" + new_name)
                        new_notes = dialog.notes_edit.toPlainText().strip()
                        new_project = {
                            'content': content_name,
                            'version': new_version,
                            'user': Global_Vars.User,
                            'dcc': latest_project['dcc'],
                            'path': self.current_file + "/" + new_name,
                            'notes': new_notes
                        }
                        projects.append(new_project)
                        file.seek(0)
                        json.dump(projects, file, ensure_ascii=False, indent=4)
        else:
            QMessageBox.information(self, "提示", "已经取消升级!")

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
            if new_notes is None:
                new_notes = ""

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
                file.truncate()
                json.dump(updated_projects, file, ensure_ascii=False, indent=4)

            self.load_projects()
        self.list_project.setCurrentIndex(index)

    def update_list(self):
        self.load_projects()
        self.show_all_versions()
        index = self.project_combo.currentIndex()
        self.project_combo.clear()
        path = Global_Vars.Project + "/2.Project/" + Global_Vars.User
        if os.path.exists(path):
            projs = os.listdir(path)
            for proj in projs:
                self.project_combo.addItem(proj)
        self.project_combo.setCurrentIndex(index)

    def on_header_clicked(self, logical_index):
        # 获取当前排序顺序
        current_order = self.proxy_model.sortOrder()
        if current_order == Qt.AscendingOrder:
            new_order = Qt.DescendingOrder
        else:
            new_order = Qt.AscendingOrder

        # 设置新的排序顺序
        self.proxy_model.sort(logical_index, new_order)

    def show_all_versions(self):
        self.version_model.removeRows(0, self.version_model.rowCount())
        selected_item = self.list_project.currentItem()
        if selected_item:
            data = selected_item.data(Qt.UserRole)
        else:
            data = None
        if selected_item:
            item_text = selected_item.text()
            # content_name = item_text.split(' ')[0]
            content_name = data['content']

            self.current_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self.project_combo.currentText()
            self.data_file = self.current_file + "/metadata/project.json"
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as file:
                    projects = json.load(file)

                self.version_model.removeRows(0,self.version_model.rowCount())
                for project in projects:
                    if project["content"] == content_name:
                        modify_time = os.path.getmtime(project["path"])
                        mtime = datetime.fromtimestamp(int(modify_time))
                        row_count = self.version_model.rowCount()
                        self.version_model.insertRow(row_count)
                        item_version = QStandardItem(str(project['version']).zfill(3))
                        item_modify = QStandardItem(str(mtime))
                        item_des = QStandardItem(project["notes"])

                        item_version.setData(project,Qt.ItemDataRole.UserRole)
                        self.version_model.setItem(row_count, 0, item_version)
                        self.version_model.setItem(row_count, 1, item_modify)
                        self.version_model.setItem(row_count, 2, item_des)

    def edit_version_note(self,row,colume,new_text):
        item = self.version_model.item(row,0).data(Qt.UserRole)
        self.current_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self.project_combo.currentText()
        self.data_file = self.current_file + "/metadata/project.json"
        with open(self.data_file, 'r+', encoding='utf-8') as file:
            projects = json.load(file)
            updated_projects = []
            if new_text is None:
                new_text = ""
            for project in projects:
                if project['path'] == item['path']:
                    project['notes'] = new_text
                updated_projects.append(project)
                file.seek(0)
                file.truncate()
                json.dump(updated_projects, file, ensure_ascii=False, indent=4)

    def get_describe(self,item):
        if item:
            project = item.data(Qt.ItemDataRole.UserRole)
            describe = project['notes']
            self.des_lab.setText(describe)
        self.show_all_versions()

    def copy_and_rename(self,old_name,path,newname):
        src = os.path.join(base_dir, "../templates", old_name)
        des = os.path.join(path,newname)
        shutil.copy(src,des)

    def get_filpbook(self,value):
        item = value
        data = item.data(Qt.UserRole)
        content = data["content"]
        dialog = Flipbook_Dialog(content)
        dialog.show()
        dialog.exec_()

    def opensub(self):
        sub_window = Opensub()
        sub_window.exec_()

    def dropEvent(self, event:QDropEvent):
        self.current_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self.project_combo.currentText()
        src_path = event.mimeData().urls()[0].toLocalFile()
        dialog = CopyToFileDialog(src_path)
        if dialog.exec_() == QDialog.Accepted:
            des = os.path.join(self.current_file, dialog.get_asset()[dialog.get_text()],os.path.basename(src_path))
            shutil.copy(src_path,des)








