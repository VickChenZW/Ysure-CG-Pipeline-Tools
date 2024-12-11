import json
import os
import sys
from PySide2.QtWidgets import (
    QMainWindow, QApplication,
    QLabel,  QHBoxLayout,
    QVBoxLayout, QWidget, QTabWidget, QPushButton,
    QFileDialog, QLineEdit, QTextEdit, QListWidget,QListWidgetItem,
    QTableWidget, QTableWidgetItem, QDialog, QDialogButtonBox, QMessageBox,
    QStackedLayout,QComboBox, QMenuBar, QMenu,QToolBar,QAction

)
from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import QFont, QDropEvent, QEnterEvent, QDragLeaveEvent, QIcon, QPixmap
import Function
import qdarktheme
from Work_Project import Work_Project

from Project_Manage import project_manager
from file_exchange import File_Exchange
import Global_Vars

## header with logo

base_dir = os.path.dirname(os.path.abspath(__file__))
_user = ["Neo", "Vick", "YL", "Jie", "K", "O"]
about = "制作：Vick   测试版beta v0.1"

class User_Choose(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("选择用户")
        self.layout = QVBoxLayout()

        self.list_user = QListWidget()

        for user in _user:
            self.list_user.addItem(user)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.list_user)
        self.layout.addWidget(button_box)

        self.setLayout(self.layout)
class header(QWidget):
    def __init__(self,work):
        super().__init__()


        self.ci = work

        # add widgets
        logo = QLabel()
        logo.setPixmap(QPixmap(os.path.join(base_dir, "icon", "Y.ico")))
        logo.setAlignment(Qt.AlignLeft)
        logo.setScaledContents(True)
        logo.setMaximumSize(QSize(100,100))


        tile1 = QLabel()
        tile1.setPixmap(QPixmap(os.path.join(base_dir,"icon","root.ico")))
        tile1.setScaledContents(True)
        tile1.setMaximumSize(QSize(30, 30))

        self.file_path_text = QLineEdit(Global_Vars.Root)
        self.file_path_text.textChanged.connect(self.root_change)
        self.file_path_text.setMaximumHeight(30)
        self.file_path_text.setEnabled(False)
        self.file_path_text.setStyleSheet("font-size:20px;}")
        btn_open = QPushButton()
        btn_open.setIcon(QIcon(os.path.join(base_dir,"icon","opened_folder.ico")))
        btn_open.pressed.connect(lambda:os.startfile(Global_Vars.Root))
        btn_path = QPushButton("...")
        btn_path.pressed.connect(self.open_file_Dic)

        path_lab = QLabel()
        path_lab.setPixmap(QPixmap(os.path.join(base_dir,"icon","business.ico")))
        path_lab.setMaximumSize(QSize(30, 30))
        path_lab.setScaledContents(True)

        self.path_label = QLineEdit(Global_Vars.Project)
        self.path_label.textChanged.connect(self.change_work)
        self.path_label.setStyleSheet("font-size:20px;}")
        self.path_label.setEnabled(False)
        btn_open_file = QPushButton()
        btn_open_file.setIcon(QIcon(os.path.join(base_dir, "icon", "opened_folder.ico")))
        btn_open_file.pressed.connect(lambda: os.startfile(self.path_label.text() + "/2.Project/"))

        user_label = QLabel()
        user_label.setPixmap(QPixmap(os.path.join(base_dir,"icon","person.ico")))
        user_label.setAlignment(Qt.AlignLeft)
        user_label.setScaledContents(True)
        user_label.setMaximumSize(QSize(30,30))

        self.user_text = QLabel("祝你工作快乐！ " + Global_Vars.User)
        self.user_text.setEnabled(False)
        self.user_text.setStyleSheet("font-size:20px;}")

        self.btn_user = QPushButton(Global_Vars.User)
        self.btn_user.pressed.connect(self.change_user)




        path_layout = QHBoxLayout()
        path_layout.addWidget(tile1)
        path_layout.addWidget(self.file_path_text)
        path_layout.addWidget(btn_open)
        path_layout.addWidget(btn_path)

        work_layout = QHBoxLayout()
        work_layout.addWidget(path_lab)
        work_layout.addWidget(self.path_label)
        work_layout.addWidget(btn_open_file)

        user_layout = QHBoxLayout()
        user_layout.addWidget(user_label)

        user_layout.addWidget(self.btn_user)
        user_layout.addWidget(self.user_text)
        user_layout.addStretch()


        info_layout = QVBoxLayout()
        # info_layout.setContentsMargins(30,30,0,0)
        info_layout.addLayout(path_layout)
        info_layout.addLayout(work_layout)
        info_layout.addLayout(user_layout)

        layout = QHBoxLayout()
        layout.addWidget(logo)
        layout.addLayout(info_layout)

        self.setLayout(layout)




    def open_file_Dic(self):
        # global root
        str_path = QFileDialog.getExistingDirectory(None, "选择文件夹", self.file_path_text.text())
        if str_path:
            self.file_path_text.setText(str_path)
            Global_Vars.Root = str_path

    def change_user(self):
        dialog = User_Choose()

        if dialog.exec_() == QDialog.Accepted:
            Global_Vars.User = dialog.list_user.currentItem().text()
            self.btn_user.setText(Global_Vars.User)
            # self.ci.change_user(Global_Vars.User)
            self.ci.change_combo()
            self.user_text.setText("祝你工作快乐！ " + Global_Vars.User)


    def project_change(self, text):
        self.path_label.setText(text)

    def change_work(self):
        self.ci.get_work_path(self.path_label.text())
        self.ci.change_combo()
        self.ci.load_projects()

    def root_change(self):
        self.path_label.clear()
        Global_Vars.Root = self.file_path_text.text()
## Project List

# class list_ltem_with_path(QListWidgetItem):
#     def __init__(self,name,path,parent=None):
#         super().__init__(name,parent)
#         self.project_path =path
#
# class project_list(QListWidget):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.itemDoubleClicked.connect(self.open_path)
#
#     def open_path(self, item):
#         if isinstance(item,list_ltem_with_path):
#             path = item.project_path
#         if path:
#             os.startfile(path)
#
# class project_manager(QWidget):
#     def __init__(self,class_intance):
#         super().__init__()
#         self.wm = class_intance
#
#         # add widgets
#         self.name_lab = QLineEdit("输入名字")
#         self.en_name_lab = QLineEdit("输入英文名字")
#         self.describe_lab = QTextEdit("输入描述")
#         self.prj_list = project_list()
#         btn_create_path = QPushButton("创建目录")
#         btn_create_path.pressed.connect(self.create_new_project_file)
#         btn_refresh = QPushButton("刷新列表")
#         btn_refresh.pressed.connect(self.refresh)
#
#         btn_setproject = QPushButton("")
#         btn_setproject.setIcon(QIcon(os.path.join(base_dir, "icon", "right.ico")))
#         btn_setproject.pressed.connect(self.change_project)
#         btn_edit_file = QPushButton("")
#         btn_edit_file.setIcon(QIcon(os.path.join(base_dir, "icon", "edit_file.ico")))
#
#         # layout
#         layout_create = QVBoxLayout()
#         layout_list = QVBoxLayout()
#         layout_main = QHBoxLayout()
#         layout_set = QVBoxLayout()
#
#
#         # add widget
#         layout_create.addWidget(self.name_lab)
#         layout_create.addWidget(self.en_name_lab)
#         layout_create.addWidget(self.describe_lab)
#         layout_create.addWidget(btn_create_path)
#
#         layout_list.addWidget(self.prj_list)
#         layout_list.addWidget(btn_refresh)
#
#         layout_set.addWidget(btn_setproject)
#         layout_set.addWidget(btn_edit_file)
#         layout_set.addStretch()
#
#         layout_main.addLayout(layout_create)
#         layout_main.addLayout(layout_list)
#         layout_main.addLayout(layout_set)
#
#         self.List_update()
#         # self.Table_update()
#         self.setLayout(layout_main)
#
#
#
#     def create_new_project_file(self):
#         name = self.name_lab.text()
#         date = Function.get_date()
#         en_name = self.en_name_lab.text()
#         if is_chinese(en_name):
#             error("英文名字不为英文！！")
#         else:
#             des = self.describe_lab.toPlainText()
#             new_path = _Root_Path + "/" + date+"_"+en_name
#             Function.create_path(new_path)
#             Function.create_sub_folders(new_path)
#             Function.create_project_info(name, en_name, des, new_path)
#         self.List_update()
#
#     def List_update(self):
#         self.prj_list.clear()
#         infos = Function.get_Project_info(_Root_Path)
#         for info in infos:
#             item = list_ltem_with_path(info["name"]+"("+info["describe"]+")",info["path"],self.prj_list)
#             self.prj_list.addItem(item)
#     def refresh(self):
#         self.List_update()
#
#     def change_project(self):
#         global _Work_Path
#         current_item = self.prj_list.currentItem()
#         if isinstance(current_item,list_ltem_with_path):
#             print(current_item.project_path)
#             _Work_Path = current_item.project_path
#             self.wm.project_change(current_item.project_path)


## Clipboard Funcction
class Drag_Function(QLabel):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setText("拖动到此处")
        self.setStyleSheet('''background : rgba(200,200,200,0.1);
                                                   color : #747474;''')

    def dragEnterEvent(self, event:QEnterEvent) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()
            text = event.mimeData().text()
            if "smb" in text:
                self.setStyleSheet('''background : rgba(10,200,10,0.5)''')
                self.setText("松开打开文件目录")
            else:
                self.setStyleSheet('''background : rgba(10,200,80,0.5)''')
                self.setText("松开拷贝Mac文件目录")

    def dragLeaveEvent(self, event:QDragLeaveEvent) -> None:
        self.setStyleSheet('''background : rgba(200,200,200,0.1);
                                                   color : #747474;''')
        self.setText("拖动到此处")

    def dropEvent(self, event:QDropEvent) -> None:
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if "smb" in text:
                Function.mac_2_win(text)
            else:
                Function.win_2_mac(text)

            self.setStyleSheet('''background : rgba(200,200,200,0.1);
                                           color : #747474;''')
            self.setText("拖动到此处")
class ClipBoard_Function(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()

        btn_M2W = QPushButton("Mac-->Windows")
        btn_M2W.pressed.connect(self.get_Win_Address)
        btn_W2M = QPushButton("Windows-->Mac")
        btn_W2M.pressed.connect(self.get_Mac_Address)
        btn_W2M.setMinimumHeight(50)
        btn_M2W.setMinimumHeight(50)


        drag_lab = Drag_Function()
        font = QFont("Microsoft YaHei UI", 30)
        font.setBold(True)
        # drag_lab.setStyleSheet('''background : rgba(200,200,200,0.5);
        #                        color : #747474;''')
        drag_lab.setAlignment(Qt.AlignCenter)
        drag_lab.setFont(font)


        btn_layout.addWidget(btn_M2W)
        btn_layout.addWidget(btn_W2M)


        layout.addLayout(btn_layout)
        layout.addWidget(drag_lab)

        self.setLayout(layout)

    def debug(self):
        print("test")

    def get_Win_Address(self):
        Function.mac_2_win(Function.get_from_clipboard())

    def get_Mac_Address(self):
        Function.win_2_mac(Function.get_from_clipboard())

class CustomDialog(QDialog):
    def __init__(self,mes):
        super().__init__()

        self.setWindowTitle("警告")

        QBtn = QDialogButtonBox.Ok

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.reject)

        self.layout = QVBoxLayout()
        message = QLabel(mes)
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
## Main Window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.work_path = ""
        self.setWindowTitle("Ysure 工具组件")
        self.setMinimumSize(QSize(800,500))
        self.setWindowIcon(QIcon(os.path.join(base_dir, "icon", "Y_black.ico")))
        qdarktheme.setup_theme()


        ## Tabs
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        wm = Work_Project()
        head = header(wm)
        # pro = project_manager(head, self)
        tabs.addTab(project_manager(wm,head), "项目管理")

        tabs.addTab(wm, "工作文件管理")
        tabs.addTab(File_Exchange(),"文件交换管理")
        tabs.addTab(ClipBoard_Function(), "文件路径转换")
        fonts = tabs.font()
        fonts.setPointSize(13)
        fonts.setBold(True)
        tabs.setFont(fonts)

        about_lab = QLabel(about)
        about_lab.setAlignment(Qt.AlignRight)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        save_action = QAction("&Save",self)
        save_action.triggered.connect(lambda: Function.ini(Global_Vars.Root, Global_Vars.Project,Global_Vars.User))
        file_menu.addAction(save_action)
        # layout

        Main_Layout = QVBoxLayout()

        # weight add
        Main_Layout.addWidget(head)
        Main_Layout.addWidget(tabs)
        Main_Layout.addWidget(about_lab)

        Main = QWidget()
        Main.setLayout(Main_Layout)
        self.setStyleSheet("""
            QToolTip {
                background-color: black;
                color: white;
                border: 1px solid white;
                padding: 4px;
                border-radius: 4px;
            }
        """)
        self.setCentralWidget(Main)



app = QApplication(sys.argv)
w = MainWindow()
w.show()
app.exec_()