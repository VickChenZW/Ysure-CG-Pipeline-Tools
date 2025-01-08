import os
import sys
from PySide2.QtWidgets import (
    QMainWindow, QApplication,
    QLabel, QHBoxLayout,
    QVBoxLayout, QWidget, QTabWidget, QPushButton,
    QFileDialog, QLineEdit, QListWidget, QDialog, QDialogButtonBox, QAction, QStatusBar

)
from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import QFont, QDropEvent, QDragLeaveEvent, QIcon, QPixmap, QDragEnterEvent
import qdarktheme
from scripts.Work_Project import Work_Project
from scripts.Project_Manage import project_manager
from scripts.file_exchange import File_Exchange
from scripts.Render_List import render_list
from scripts.Global_Vars import gv

from scripts import address_trans, Global_Vars, Function, Temp_update

## header with logo

base_dir = os.path.dirname(os.path.abspath(__file__))
_user = ["Neo", "Vick", "YL", "Jie", "K", "O"]
about = "制作：Vick   测试版beta v0.2"

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
    def __init__(self):
        super().__init__()

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
        btn_open_file.pressed.connect(lambda: os.startfile(self.path_label.text()))

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

        about_lab = QLabel(about)
        # about_lab.setAlignment(Qt.AlignRight)
        about_lab.setEnabled(False)
        about_lab.setStyleSheet("font-size:20px;}")


        path_layout = QHBoxLayout()
        path_layout.addWidget(tile1)
        path_layout.addWidget(self.file_path_text)
        path_layout.addWidget(btn_path)
        path_layout.addWidget(btn_open)


        work_layout = QHBoxLayout()
        work_layout.addWidget(path_lab)
        work_layout.addWidget(self.path_label)
        work_layout.addWidget(btn_open_file)

        user_layout = QHBoxLayout()
        user_layout.addWidget(user_label)

        user_layout.addWidget(self.btn_user)
        user_layout.addWidget(self.user_text)
        user_layout.addStretch()
        user_layout.addWidget(about_lab)

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
            gv.root = str_path

    def change_user(self):
        dialog = User_Choose()

        if dialog.exec_() == QDialog.Accepted:
            Global_Vars.User = dialog.list_user.currentItem().text()
            gv.user = dialog.list_user.currentItem().text()
            self.btn_user.setText(Global_Vars.User)
            # self.ci.change_user(Global_Vars.User)
            # self.ci.change_combo()
            self.user_text.setText("祝你工作快乐！ " + Global_Vars.User)


    def project_change(self, text):
        self.path_label.setText(text)

    def change_work(self):
        # self.ci.get_work_path(self.path_label.text())
        # self.ci.change_combo()
        # self.ci.load_projects()
        Global_Vars.Project = self.path_label.text()
        gv.project = self.path_label.text()

    def root_change(self):
        self.path_label.clear()
        Global_Vars.Root = self.file_path_text.text()


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
        head = header()
        self.clip_plane = address_trans.ClipBoard_Function()
        tabs.addTab(project_manager(wm,head), "项目管理")

        tabs.addTab(wm, "工作文件管理")
        tabs.addTab(File_Exchange(), "文件交换管理")
        tabs.addTab(render_list(), "渲染文件管理")
        tabs.addTab(self.clip_plane, "文件路径转换")
        fonts = tabs.font()
        fonts.setPointSize(13)
        fonts.setBold(True)
        tabs.setFont(fonts)

        about_lab = QLabel(about)
        about_lab.setAlignment(Qt.AlignRight)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&文件")
        save_action = QAction("&保存",self)
        update_action = QAction("&更新",self)
        save_action.triggered.connect(self.save)
        update_action.triggered.connect(self.update_version)
        file_menu.addAction(save_action)
        file_menu.addAction(update_action)
        # layout

        Main_Layout = QVBoxLayout()

        # weight add
        Main_Layout.addWidget(head)
        Main_Layout.addWidget(tabs)
        # Main_Layout.addWidget(about_lab)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)


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

        gv.or_changed.connect(lambda value: self.statusBar.showMessage(value,3000))

        self.update = Temp_update.CheckUpdate()
        self.update.update_signal.connect(lambda :self.close())

    def closeEvent(self, event):
        self.clip_plane.close_widget()

    def save(self):
        Function.ini(Global_Vars.Root, Global_Vars.Project, Global_Vars.User)
        self.statusBar.showMessage("保存成功", 3000)

    def update_version(self):
        if not self.update.check_update():
            self.statusBar.showMessage("你已经是最新版本!!",5000)

    def update_signal(self,value):
        if value == "close":
            self.close()





if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec_()