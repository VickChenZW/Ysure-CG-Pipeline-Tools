import ctypes
import json
import os
import re
import shutil
from datetime import datetime

# 导入 PySide2 相关的模块和类
from PySide2.QtCore import (QSize, Qt, QMimeData, QUrl, QPoint,
                            QSortFilterProxyModel, Signal, QModelIndex, QObject
                            )
from PySide2.QtGui import (QIcon, QDrag, QStandardItemModel,
                        QStandardItem, QColor, QDragEnterEvent,
                        QDragLeaveEvent, QDropEvent)
from PySide2.QtWidgets import (
    QLabel, QTabWidget, QWidget, QPushButton,
    QHBoxLayout, QVBoxLayout, QLineEdit, QListWidget,
    QComboBox, QDialog, QDialogButtonBox,
    QTextEdit, QListWidgetItem, QMessageBox, QTableView, QHeaderView,
    QSplitter, QTreeWidget, QTreeWidgetItem
)

# 导入其他模块的内容
from scripts import Global_Vars
from scripts.Global_Vars import gv
# import Global_Vars
# from Global_Vars import gv

# --- 配置常量 ---
# 支持的数字内容创作 (DCC) 软件列表
_DCC_ = ["Blender", "C4d", "Houdini", "Maya"]
# 脚本的基础目录
Base_Dir = os.path.dirname(os.path.abspath(__file__))
# 各个 DCC 软件对应的文件格式
_format_ = ({"Blender": ".blend", "C4d": ".c4d", "Houdini": ".hip", "Maya": ".ma"})
# 项目的标准子文件夹列表
_list = ["__IN__", "tex", "geo", "alembic", "vdb", "usd", "render", "flipbook", "metadata", "reference"]
# 用于解析文件名的正则表达式模式，捕获内容名称、版本和时间
FILENAME_PATTERN = r'^(.*?)(?:_(v\d{3}))(?:_(.*?))$'


# --- 辅助函数 ---
class ProcessJson(QObject):
    """
    处理Json文件的类
    """

    def __init__(self, name):
        super().__init__()

        self._name = name
        self.json_path = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self._name + "/metadata/project.json"

    def change_name(self, new_name):
        self._name = new_name
        self.json_path = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + new_name + "/metadata/project.json"

    def create_json(self):
        """
        处理 project.json文件
        :return: str
        """
        log_text = ''

        if not os.path.exists(self.json_path):
            with open(self.json_path, 'w', encoding='utf-8') as file:
                json.dump([], file, ensure_ascii=False, indent=4)
            log_text = '创建元数据文件'

        return log_text

    def load_json(self, mode: str):
        """
        读取json
        """
        projects = []
        if not os.path.exists(self.json_path):
            # self.create_json()
            projects = []

        else:
            try:
                with open(self.json_path, mode, encoding='utf-8') as file:
                    projects = json.load(file)

            except (FileNotFoundError, json.JSONDecodeError) as e:
                gv.log = f"加载项目数据文件时出错: {e}"
            except Exception as e:
                gv.log = f"处理项目数据时出错: {e}"

        return projects

    def find_latest_version(self):
        """
        查找最新的版本的列表
        :return: dict
        """
        projects = self.load_json('r')
        latest_version_projects = {}
        for project in projects:
            content_name = project['content']
            version = project.get('version', 0)  # 默认版本为 0
            dcc = project['dcc']
            path = project['path']

            if content_name and path and os.path.exists(path):  # 确保关键信息存在且文件存在
                if content_name not in latest_version_projects or latest_version_projects[content_name][
                    'version'] < version:
                    latest_version_projects[content_name] = {
                        'version': version,
                        'project': project,
                        'dcc': dcc,
                        'path': path
                    }
            elif content_name:
                print(f"警告: 项目 '{content_name}' (版本 {version}) 的文件路径无效或文件不存在: {path}")

        return latest_version_projects

    def add_to_json(self, dic: dict):

        with open(self.json_path, 'r+', encoding='utf-8') as file:
            projects = json.load(file)
            projects.append(dic)
            file.seek(0)
            json.dump(projects, file, ensure_ascii=False, indent=4)

        gv.log = datetime.now().strftime("%Y-%m-%d-%H:%M:%S") + '文件增加成功'

    def modify_json(self, updated_projects: list):
        with open(self.json_path, 'r+', encoding='utf-8') as file:
            file.seek(0)
            file.truncate()
            json.dump(updated_projects, file, ensure_ascii=False, indent=4)

        gv.log = datetime.now().strftime("%Y-%m-%d-%H:%M:%S") + '备注修改成功'

    def debug(self):
        print(self._name)


def create_work_folder_structure(base_path, user, project_name, subfolders):
    """
    创建新项目的标准文件夹结构。

    Args:
        base_path (str): 项目的基础目录。
        user (str): 当前用户的名称。
        project_name (str): 新项目的名称。
        subfolders (list): 要创建的子文件夹名称列表。
    """
    # 构建项目完整路径
    project_path = os.path.join(base_path, "2.Project", user, project_name)
    try:
        # 创建项目主文件夹，如果已存在则忽略
        os.makedirs(project_path, exist_ok=True)
        # 在项目主文件夹下创建子文件夹
        for folder in subfolders:
            os.makedirs(os.path.join(project_path, folder), exist_ok=True)
        print(f"成功创建项目文件夹结构: {project_path}")
    except OSError as e:
        # 处理文件夹创建失败的错误
        print(f"创建项目文件夹时出错: {e}")


def copy_and_rename(old_name, path, newname):
    src = os.path.join(Base_Dir, "../templates", old_name)
    des = os.path.join(path, newname)
    shutil.copy(src, des)


def get_file_modify_time(filepath):
    """
    获取文件的修改时间并格式化为字符串 (MMDD)。

    Args:
        filepath (str): 文件的路径。

    Returns:
        str: 格式化的修改时间 (MMDD)，如果文件不存在则返回 None。
    """
    try:
        # 获取文件的最后修改时间戳
        modify_time = os.path.getmtime(filepath)
        # 将时间戳转换为 datetime 对象并格式化为 MMDD
        return datetime.fromtimestamp(int(modify_time)).strftime('%m%d')
    except FileNotFoundError:
        # 文件未找到时的警告
        print(f"警告: 未找到文件，无法获取修改时间: {filepath}")
        return None
    except Exception as e:
        # 处理获取文件修改时间时的其他错误
        print(f"获取文件修改时间时出错 {filepath}: {e}")
        return None


def get_file_creation_time(filepath):
    """
    获取文件的创建时间并格式化为字符串 (YYYYMMDD_HHMMSS)。

    Args:
        filepath (str): 文件的路径。

    Returns:
        str: 格式化的创建时间 (YYYYMMDD_HHMMSS)，如果文件不存在则返回 None。
    """
    try:
        # 注意：在某些系统上，ctime 是创建时间，在其他系统上是最后一次元数据更改时间。
        # 为了与原始代码在 FlipbookDialog 中的用法保持一致，这里使用了 getmtime。
        # 如果需要更可靠的创建时间，可能需要平台特定的方法。
        create_time = os.path.getmtime(filepath)
        # 将时间戳转换为 datetime 对象并格式化
        return datetime.fromtimestamp(int(create_time)).strftime('%Y%m%d_%H%M%S')
    except FileNotFoundError:
        # 文件未找到时的警告
        print(f"警告: 未找到文件，无法获取创建时间: {filepath}")
        return None
    except Exception as e:
        # 处理获取文件创建时间时的其他错误
        print(f"获取文件创建时间时出错 {filepath}: {e}")
        return None


def is_hidden_file(filepath):
    """
    检查文件是否是 Windows 上的隐藏文件。

    Args:
        filepath (str): 文件的路径。

    Returns:
        bool: 如果文件是隐藏的则返回 True，否则返回 False。
    """
    if os.name == 'nt':  # 检查操作系统是否是 Windows
        try:
            # 使用 Windows API 获取文件属性并检查隐藏属性位
            return bool(ctypes.windll.kernel32.GetFileAttributesW(filepath) & 2)
        except Exception as e:
            # 处理获取文件属性时的错误
            print(f"检查文件属性时出错 {filepath}: {e}")
            return False
    # 对于其他操作系统，默认返回 False (或实现相关的检查)
    return False


def parse_filename(filename):
    """
    解析文件名，提取内容名称、版本和时间。

    Args:
        filename (str): 要解析的文件名 (不含路径)。

    Returns:
        tuple: 包含 (内容名称, 版本, 时间) 的元组，如果文件名不符合模式则返回 (None, None, None)。
    """
    # 移除文件扩展名
    name_without_ext = os.path.splitext(filename)[0]
    # 使用正则表达式匹配文件名模式
    match = re.match(FILENAME_PATTERN, name_without_ext)
    if match:
        # 返回匹配到的分组：内容名称、版本、时间
        return match.groups()
    return None, None, None  # 如果不匹配则返回 None


def create_work_Folder(path, user, name, type_lists):
    project_path = path + "/2.Project/" + user
    if not os.path.exists(project_path):
        os.makedirs(project_path)
    project_path += "/" + name
    if not os.path.exists(project_path):
        os.makedirs(project_path)
    for file_type in type_lists:
        if not os.path.exists(project_path + "/" + file_type):
            os.makedirs(project_path + "/" + file_type)


# --- 对话框类 ---
class EditNotesDialog(QDialog):
    """
    编辑notes的Dialog
    """

    def __init__(self, initial_notes):
        """

        :param initial_notes: 默认的内容
        """
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

    def accept_and_destroy(self):
        self.accept()  # 关闭对话框并返回 Accepted
        self.deleteLater()  # 销毁对话框


class InputDialog(QDialog):
    """
    用于获取单行文本输入的通用对话框。
    创建文件夹使用
    """

    def __init__(self, title, info, parent=None):
        super().__init__(parent)

        self.t = title
        self.i = info
        self.setWindowIcon(QIcon(os.path.join(Base_Dir, "../icon", "new.ico")))

        self.setWindowTitle(self.t)
        self.setMinimumSize(QSize(300, 200))

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


class ProjectCreationDialog(QDialog):
    """
    创建DCC工程文件对话框
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("创建新工程")
        self.layout = QVBoxLayout()
        self.setWindowIcon(QIcon(os.path.join(Base_Dir, "../icon", "new.ico")))
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
            self.dcc_select.setItemIcon(index, QIcon(os.path.join(Base_Dir, "../icon", key)))
            index += 1
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


class CopyToFileDialog(QDialog):
    def __init__(self, src_path):
        super().__init__()
        self.src_path = src_path
        self.assets = {'贴图': 'tex', '参考': 'reference', '三维': 'geo', 'ABC': 'alembic', 'VDB': 'vdb'}
        self.text = ""

        self.setWindowTitle("复制到文件")
        self.setWindowIcon(QIcon(os.path.join(Base_Dir, "../icon", "new.ico")))

        self.layout = QVBoxLayout()

        self.label = QLabel(src_path)
        self.layout.addWidget(self.label)

        for k in self.assets:
            btn = QPushButton(k)
            btn.clicked.connect(self.clicked)
            self.layout.addWidget(btn)

        self.setLayout(self.layout)

    def clicked(self):
        button: QPushButton = self.sender()
        self.text = button.text()
        self.accept()

    def get_text(self):
        return self.text

    def get_asset(self) -> dict:
        return self.assets


# --- 自定义控件类 ---
# 保留自定义控件类以实现拖放等特定行为
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


class VersionTableModel(QStandardItemModel):
    dataChangedSignal = Signal(int, int, str)

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
                project = self.data(index.siblingAtColumn(0), Qt.ItemDataRole.UserRole)
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
                self.dataChangedSignal.emit(index.row(), index.column(), value)
                # 调用父类的 setData 方法以确保实际的数据更新
            return super().setData(index, value, role)


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

    def dragEnterEvent(self, event: QDragEnterEvent):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            url = mime_data.urls()[0]
            event.acceptProposedAction()
            print(url.toLocalFile())

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        print('leave')

    def dropEvent(self, event: QDropEvent) -> None:
        event.accept()
        print('move')


# --- 主应用程序控件 ---
class OpenSubDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("打开资产文件夹")
        self.layout = QVBoxLayout()
        self.setWindowIcon(QIcon(os.path.join(Base_Dir, "../icon", "version.ico")))
        self.assets = {'贴图': 'tex', '参考': 'reference', '三维': 'geo', 'ABC': 'alembic', 'VDB': 'vdb'}
        self.current_file = gv.project + "/2.Project/" + gv.user + "/" + gv.task

        self.path_label = QLabel()
        self.layout.addWidget(self.path_label)

        self.tab = QTabWidget()
        self.add_item()
        self.tab.currentChanged.connect(self.change_path_tab)

        self.layout.addWidget(self.tab)
        self.path_label.setText(self.assets[self.tab.tabText(0)])
        self.setLayout(self.layout)

    def add_item(self):
        self.createFoloder()
        for key in self.assets:

            widget = QWidget()
            layout = QVBoxLayout(widget)
            list = DraggableListWidget()
            list.itemDoubleClicked.connect(lambda item, lw=list: self.open_down(item, lw))

            btn_up = QPushButton("向上一层")
            btn_up.pressed.connect(lambda lw=list: self.open_up(lw))

            btn_open = QPushButton("打开文件夹")
            btn_open.pressed.connect(lambda x=self.assets[key]: os.startfile(os.path.join(self.current_file, x)))

            layout.addWidget(list)
            layout.addWidget(btn_up)
            layout.addWidget(btn_open)
            self.tab.addTab(widget, key)
            path = os.path.join(self.current_file, self.assets[key])
            for i in os.listdir(path):
                att = ctypes.windll.kernel32.GetFileAttributesW(os.path.join(path, i))
                if att != -1 and bool(att & 2):  # 判断是不是隐藏文件
                    pass
                else:
                    item = QListWidgetItem(i)
                    dic = {
                        'path': os.path.join(path, i)
                    }
                    if os.path.isdir(os.path.join(path, i)):
                        item.setBackgroundColor(QColor(0, 50, 0))
                    item.setData(Qt.UserRole, dic)
                    list.addItem(item)

    def change_path_tab(self):
        self.path_label.setText(self.assets[self.tab.tabText(self.tab.currentIndex())])

    def change_path_label(self, new_path):
        path = self.path_label.text()
        self.path_label.setText(path + "\\" + new_path)

    def open_down(self, value, list):
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

    def open_up(self, list):
        if not "\\" in self.path_label.text():
            pass
        else:
            self.path_label.setText(os.path.dirname(self.path_label.text()))
            path = os.path.join(os.path.join(self.current_file, self.path_label.text()))
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
            if os.path.exists(os.path.join(self.current_file, self.assets[key])):
                pass
            else:
                os.makedirs(os.path.join(self.current_file, self.assets[key]))


class FlipbookDialog(QDialog):
    def __init__(self, content):
        super().__init__()
        self.flip_path = gv.project + "/2.Project/" + gv.user + "/" + gv.task + "/flipbook/" + content
        self.content = content
        self.setWindowTitle("拍屏文件")
        self.layout = QVBoxLayout()
        self.setWindowIcon(QIcon(os.path.join(Base_Dir, "../icon", "new.ico")))
        self.content_label = QLabel(self.content)
        self.content_label.setStyleSheet("font-size:20px;}")
        self.content_label.setAlignment(Qt.AlignCenter)

        self.btn_expanded = QPushButton("全部折叠")
        self.btn_expanded.clicked.connect(self.expanded)

        # self.list = DraggableListWidget()
        self.list = DraggableTreeWidget()
        self.list.setHeaderLabels(['版本', '创建时间'])
        self.list.doubleClicked.connect(self.open_file)
        btn_refresh = QPushButton("刷新列表")
        btn_refresh.clicked.connect(self.add_item)
        btn_open = QPushButton("打开拍屏文件夹")
        btn_open.clicked.connect(lambda: os.startfile(self.flip_path))
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


class WorkProjectWidget(DraggableDroppableWidget):
    """
    用于管理工作项目、版本和资产的主控件。
    处理项目的创建、加载、版本控制和拖放功能。
    """

    def __init__(self):
        super().__init__()
        self.data_file = ""
        self.current_file = ""
        self.process_json = ProcessJson(Global_Vars.task)
        self._setup_ui()

        Global_Vars.task = self.project_combo.currentText()
        self.get_work_path(Global_Vars.Project)
        self.load_projects()

        gv.user_changed.connect(self.change_combo)
        gv.project_changed.connect(self.change_project)

    def _setup_ui(self):
        """初始化布局"""
        # 设置布局
        main_layout = QVBoxLayout()

        layout = QHBoxLayout()

        # name—layout设置
        name_layout = QHBoxLayout()

        project_lab = QLabel("Project name")

        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(500)
        self.change_combo()
        self.project_combo.currentIndexChanged.connect(self.load_projects)
        self.project_combo.setStyleSheet("font-size:20px;}")

        project_add = QPushButton()
        project_add.pressed.connect(self.add_name_input)
        project_add.setIcon(QIcon(os.path.join(Base_Dir, "../icon", "add.ico")))
        project_add.setToolTip("增加工程文件夹层级")

        name_layout.addWidget(project_lab)
        name_layout.addWidget(self.project_combo)
        name_layout.addWidget(project_add)

        # 设置侧边栏按钮
        layout_tools = QVBoxLayout()

        btn_new = QPushButton()
        btn_new.setIcon(QIcon(os.path.join(Base_Dir, "../icon", "new.ico")))
        btn_new.setMinimumSize(QSize(40, 40))
        btn_new.setToolTip("新建文件")
        btn_new.pressed.connect(self.create_new_project)

        btn_open_project = QPushButton()
        btn_open_project.setIcon(QIcon(os.path.join(Base_Dir, "../icon", "open.ico")))
        btn_open_project.setToolTip("打开文件")
        btn_open_project.setMinimumSize(QSize(40, 40))
        btn_open_project.pressed.connect(
            lambda: os.startfile(f'{gv.project}/2.Project/{gv.user}/{gv.task}'))

        btn_update = QPushButton()
        btn_update.setIcon(QIcon(os.path.join(Base_Dir, "../icon", "updata.ico")))
        btn_update.setMinimumSize(QSize(40, 40))
        btn_update.setToolTip("版本升级")
        btn_update.pressed.connect(self.upgrade_selected_project)

        btn_refresh = QPushButton()
        btn_refresh.setIcon(QIcon(os.path.join(Base_Dir, "../icon", "refresh.ico")))
        btn_refresh.setMinimumSize(QSize(40, 40))
        btn_refresh.setToolTip("刷新")
        btn_refresh.pressed.connect(self.update_list)

        btn_subfolder = QPushButton()
        btn_subfolder.setIcon(QIcon(os.path.join(Base_Dir, "../icon", "version.ico")))
        btn_subfolder.setMinimumSize(QSize(40, 40))
        btn_subfolder.setToolTip("打开子文件夹")
        btn_subfolder.pressed.connect(self.OpenSubDialog)

        self.des_lab = QLabel("describe")
        self.des_lab.setMinimumWidth(150)

        layout_tools.addWidget(btn_new)
        layout_tools.addWidget(btn_open_project)
        layout_tools.addWidget(btn_update)
        layout_tools.addWidget(btn_refresh)
        layout_tools.addWidget(btn_subfolder)
        layout_tools.addStretch()

        # 设置列表布局
        splitter = QSplitter(Qt.Horizontal)

        self.list_project = DraggableListWidget()
        self.list_project.doubleClicked.connect(self.get_filpbook)
        self.list_project.currentItemChanged.connect(self.get_describe)
        self.list_project.setStyleSheet("font-size:20px;}")
        splitter.addWidget(self.list_project)

        self.table_version = QTableView()
        self.proxy_model = QSortFilterProxyModel()
        self.version_model = VersionTableModel()
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

        splitter.addWidget(self.table_version)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        # 设置布局排列
        layout.addLayout(layout_tools)
        layout.addWidget(splitter)

        main_layout.addLayout(name_layout)
        main_layout.addLayout(layout)

        self.setLayout(main_layout)

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
            data_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + name + "/metadata/project.json"
            log_text = ''
            if path:
                create_work_Folder(path, Global_Vars.User, name, _list)
                log_text = '文件夹创建完成'
            else:
                log_text = '路径存在错误'

            if not os.path.exists(data_file):
                with open(data_file, 'w', encoding='utf-8') as file:
                    json.dump([], file, ensure_ascii=False, indent=4)
                log_text = '创建元数据文件'
            gv.log = log_text

    def change_combo(self):
        self.project_combo.clear()
        path = Global_Vars.Project + "/2.Project/" + Global_Vars.User
        if os.path.exists(path):
            projs = os.listdir(path)
            for proj in projs:
                if os.path.isdir(os.path.isdir(os.path.join(path, proj))):
                    self.project_combo.addItem(proj)
            self.process_json.change_name(self.project_combo.currentText())

    def load_projects(self):
        """加载当前选定项目下的内容列表（最新版本）到项目列表视图。"""
        self.list_project.clear()
        Global_Vars.gv.task = self.project_combo.currentText()
        self.process_json.change_name(self.project_combo.currentText())

        projects_info = self.process_json.find_latest_version()

        for content_name, info in projects_info.items():
            path = info['path']
            modify_time_str = get_file_modify_time(path)  # 获取格式化的修改时间
            # 构建列表项文本
            item_text = f"{modify_time_str} {content_name} v{str(info['version']).zfill(3)}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, info['project'])

            item.setIcon(QIcon(os.path.join(Base_Dir, "../icon", info["dcc"])))

            self.list_project.addItem(item)
        gv.log = datetime.now().strftime("%Y-%m-%d-%H:%M:%S") + '文件列表加载成功'
        gv.task = self.project_combo.currentText()

    def create_new_project(self):
        """
        创建新的工程文件
        :return:
        """
        self.current_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self.project_combo.currentText()
        self.data_file = self.current_file + "/metadata/project.json"
        if not os.path.exists(self.current_file):
            QMessageBox.warning(self, "警告", "请创建文件夹")
        else:
            dialog = ProjectCreationDialog()

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
                projects = self.process_json.load_json('r+')

                for i in projects:
                    exist_file.append(i['content'])

                if content_name in exist_file:
                    QMessageBox.warning(self, "警告", "文件名已经存在")
                else:
                    full_name = content_name + "_v" + str(version).zfill(3) + format
                    self.current_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self.project_combo.currentText()
                    self.data_file = self.current_file + "/metadata/project.json"
                    copy_and_rename(dcc + format, self.current_file + "/", full_name)
                    new_project = {
                        'content': content_name,
                        'version': version,
                        'user': Global_Vars.User,
                        'dcc': dcc,
                        'path': self.current_file + "/" + full_name,
                        'notes': notes
                    }
                    self.process_json.add_to_json(new_project)

            self.load_projects()

    def upgrade_selected_project(self):
        """
        升级所选的工程
        :return:
        """
        selected_item = self.list_project.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "警告", "请选择一个工程")
            return

        item_text = selected_item.text()
        content_name = item_text.split(' ')[1]

        self.current_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self.project_combo.currentText()
        self.data_file = self.current_file + "/metadata/project.json"
        if QMessageBox.question(self, "升级工程",
                                "请确实使用外部升级\n确认保存当前工程了") == QMessageBox.StandardButton.Yes:
            print("ok")
            latest_project = None
            projects = self.process_json.load_json('r+')

            for project in projects:
                if project['content'] == content_name and (
                        latest_project is None or project['version'] > latest_project['version']):
                    latest_project = project

            if latest_project:
                new_version = latest_project['version'] + 1
                current_notes = latest_project['notes']
                dialog = EditNotesDialog(current_notes)
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
                    self.process_json.add_to_json(new_project)
            self.load_projects()
        else:
            QMessageBox.information(self, "提示", "已经取消升级!")

    def edit_notes(self, item):
        """
        编辑备注
        :param item:
        :return:
        """
        project_data = item.data(Qt.UserRole)
        index = self.list_project.currentIndex()
        content_name = project_data['content']
        version = project_data['version']
        current_notes = project_data.get('notes', '')

        dialog = EditNotesDialog(current_notes)
        if dialog.exec_() == QDialog.Accepted:
            new_notes = dialog.notes_edit.toPlainText().strip()
            if new_notes is None:
                new_notes = ""

            self.current_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self.project_combo.currentText()
            self.data_file = self.current_file + "/metadata/project.json"
            updated_projects = []
            projects = self.process_json.load_json('r+')

            for project in projects:
                if project['content'] == content_name and project['version'] == version:
                    project['notes'] = new_notes
                updated_projects.append(project)
            self.process_json.modify_json(updated_projects)

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
                if os.path.isdir(os.path.join(path, proj)):
                    self.project_combo.addItem(proj)
        self.project_combo.setCurrentIndex(index)
        self.process_json.change_name(self.project_combo.currentText())

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
            content_name = data['content']
            projects = self.process_json.load_json('r')

            self.version_model.removeRows(0, self.version_model.rowCount())
            for project in projects:
                if project["content"] == content_name:
                    modify_time = os.path.getmtime(project["path"])
                    mtime = datetime.fromtimestamp(int(modify_time))
                    row_count = self.version_model.rowCount()
                    self.version_model.insertRow(row_count)
                    item_version = QStandardItem(str(project['version']).zfill(3))
                    item_modify = QStandardItem(str(mtime))
                    item_des = QStandardItem(project["notes"])

                    item_version.setData(project, Qt.ItemDataRole.UserRole)
                    self.version_model.setItem(row_count, 0, item_version)
                    self.version_model.setItem(row_count, 1, item_modify)
                    self.version_model.setItem(row_count, 2, item_des)

    def edit_version_note(self, row, colume, new_text):
        item = self.version_model.item(row, 0).data(Qt.UserRole)
        projects = self.process_json.load_json('r+')
        updated_projects = []
        if new_text is None:
            new_text = ""
        for project in projects:
            if project['path'] == item['path']:
                project['notes'] = new_text
            updated_projects.append(project)
        self.process_json.modify_json(updated_projects)

    def get_describe(self, item):
        if item:
            project = item.data(Qt.ItemDataRole.UserRole)
            describe = project['notes']
            self.des_lab.setText(describe)
        self.show_all_versions()

    def get_filpbook(self, value):
        item = value
        data = item.data(Qt.UserRole)
        content = data["content"]
        dialog = FlipbookDialog(content)
        dialog.show()
        dialog.exec_()

    def OpenSubDialog(self):
        sub_window = OpenSubDialog()
        sub_window.exec_()

    def dropEvent(self, event: QDropEvent):
        self.current_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self.project_combo.currentText()
        src_path = event.mimeData().urls()[0].toLocalFile()
        dialog = CopyToFileDialog(src_path)
        if dialog.exec_() == QDialog.Accepted:
            des = os.path.join(self.current_file, dialog.get_asset()[dialog.get_text()], os.path.basename(src_path))
            shutil.copy(src_path, des)
