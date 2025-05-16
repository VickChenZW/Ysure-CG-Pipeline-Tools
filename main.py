import os
import sys
from PySide2.QtWidgets import (
    QMainWindow, QApplication, QMessageBox,  # 确保导入 QMessageBox
    QLabel, QHBoxLayout,
    QVBoxLayout, QWidget, QTabWidget, QPushButton,
    QFileDialog, QLineEdit, QListWidget, QDialog, QDialogButtonBox,
    QAction, QStatusBar, QSystemTrayIcon, QMenu, QStyle  # 添加 QSystemTrayIcon, QMenu, QAction, QStyle
)
from PySide2.QtCore import QSize, Qt, Signal, QAbstractNativeEventFilter, QTimer
from PySide2.QtGui import QIcon, QPixmap
import qdarktheme
from scripts.WorkProjectWidget import WorkProjectWidget
from scripts.Project_Manage import ProjectManager
# from scripts.file_exchange import File_Exchange # 如果不再使用，可以注释掉
from scripts.Render_List import RenderList
from scripts.Global_Vars import gv
from scripts.file_exchange_online import FileSenderWidget

from scripts import address_trans, Global_Vars, Function, Temp_update
# 导入新的 Popup Widget
from scripts.popup_widget import Win11StylePopup

# 抬头设置

base_dir = os.path.dirname(os.path.abspath(__file__))
_user = ["Neo", "Vick", "YL", "Jie", "K", "O"]
about = "制作：Vick   测试版beta v0.3"


class UserChoose(QDialog):
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


class Header(QWidget):

    def __init__(self):
        super().__init__()

        # add widgets
        # logo = QLabel()
        # logo.setPixmap(QPixmap(os.path.join(base_dir, "icon", "Y.ico")))
        # logo.setAlignment(Qt.AlignLeft)
        # logo.setScaledContents(True)
        # logo.setMaximumSize(QSize(100, 100))
        self.logo = QPushButton()
        self.logo.setIcon(QIcon(os.path.join(base_dir, "icon", "Y.ico")))
        self.logo.setIconSize(QSize(80, 80))
        # logo.setAlignment(Qt.AlignLeft)
        # logo.setScaledContents(True)
        self.logo.setFixedSize(QSize(100, 100))
        self.logo.setStyleSheet("""
            QPushButton {
                border: none; /* 移除边框 */
                background-color: transparent; /* 背景透明 */
                padding: 0px; /* 移除内边距 */
            }
            QPushButton:hover {
                background-color: rgba(85, 85, 85, 0.3); /* 轻微悬停效果 (可选) */
            }
            QPushButton:pressed {
                background-color: rgba(68, 68, 68, 0.5); /* 轻微按下效果 (可选) */
            }
        """)

        tile1 = QLabel()
        tile1.setPixmap(QPixmap(os.path.join(base_dir, "icon", "root.ico")))
        tile1.setScaledContents(True)
        tile1.setMaximumSize(QSize(30, 30))

        self.file_path_text = QLineEdit(Global_Vars.Root)
        self.file_path_text.textChanged.connect(self.root_change)
        self.file_path_text.setMaximumHeight(30)
        self.file_path_text.setEnabled(False)
        self.file_path_text.setStyleSheet("font-size:20px;}")
        btn_open = QPushButton()
        btn_open.setIcon(QIcon(os.path.join(base_dir, "icon", "opened_folder.ico")))
        btn_open.pressed.connect(lambda: os.startfile(Global_Vars.Root))
        btn_path = QPushButton("...")
        btn_path.pressed.connect(self.open_file_dir)

        path_lab = QLabel()
        path_lab.setPixmap(QPixmap(os.path.join(base_dir, "icon", "business.ico")))
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
        user_label.setPixmap(QPixmap(os.path.join(base_dir, "icon", "person.ico")))
        user_label.setAlignment(Qt.AlignLeft)
        user_label.setScaledContents(True)
        user_label.setMaximumSize(QSize(30, 30))

        self.user_text = QLabel("祝你工作快乐！ " + Global_Vars.User)
        self.user_text.setEnabled(False)
        self.user_text.setStyleSheet("font-size:20px;}")

        self.btn_user = QPushButton(Global_Vars.User)
        self.btn_user.pressed.connect(self.change_user)

        about_lab = QLabel(about)
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
        info_layout.addLayout(path_layout)
        info_layout.addLayout(work_layout)
        info_layout.addLayout(user_layout)

        layout = QHBoxLayout()
        layout.addWidget(self.logo)
        layout.addLayout(info_layout)

        self.setLayout(layout)

    def open_file_dir(self):
        # global root
        str_path = QFileDialog.getExistingDirectory(None, "选择文件夹", self.file_path_text.text())
        if str_path:
            self.file_path_text.setText(str_path)
            Global_Vars.Root = str_path
            gv.root = str_path

    def change_user(self):
        dialog = UserChoose()

        if dialog.exec_() == QDialog.Accepted:
            Global_Vars.User = dialog.list_user.currentItem().text()
            gv.user = dialog.list_user.currentItem().text()
            self.btn_user.setText(Global_Vars.User)
            self.user_text.setText("祝你工作快乐！ " + Global_Vars.User)

    def project_change(self, text):
        self.path_label.setText(text)

    def change_work(self):
        Global_Vars.Project = self.path_label.text()
        gv.project = self.path_label.text()

    def root_change(self):
        self.path_label.clear()
        Global_Vars.Root = self.file_path_text.text()


# 主界面
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ysure 工具组件")
        self.setMinimumSize(QSize(800, 500))
        # 确保图标路径正确
        icon_path = os.path.join(base_dir, "icon", "Y_black.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"警告: 找不到窗口图标文件: {icon_path}")
        qdarktheme.setup_theme()

        # 标签页配置
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        wm = WorkProjectWidget()
        head = Header()
        head.logo.clicked.connect(self.show_popup_widget)
        self.file_exchange = FileSenderWidget(Global_Vars.User, Global_Vars.Project, Global_Vars.task)
        self.clip_plane = address_trans.ClipBoard_Function()
        tabs.addTab(ProjectManager(wm, head), "项目管理")

        tabs.addTab(wm, "工程管理")
        # tabs.addTab(File_Exchange(), "资产管理") # 如果不再使用，可以注释掉
        tabs.addTab(RenderList(), "渲染管理")
        # tabs.addTab(self.clip_plane, "路径转换")
        tabs.addTab(self.file_exchange, "文件发送(beta)")
        fonts = tabs.font()
        fonts.setPointSize(13)
        fonts.setBold(True)
        tabs.setFont(fonts)

        about_lab = QLabel(about)
        about_lab.setAlignment(Qt.AlignRight)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&文件")
        save_action = QAction("&保存", self)
        update_action = QAction("&更新", self)
        save_action.triggered.connect(self.save)
        update_action.triggered.connect(self.update_version)
        file_menu.addAction(save_action)
        file_menu.addAction(update_action)

        # 设置主布局
        main_layout = QVBoxLayout()

        # 增加组件
        main_layout.addWidget(head)
        main_layout.addWidget(tabs)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        main = QWidget()
        main.setLayout(main_layout)
        self.setStyleSheet("""
            QToolTip {
                background-color: black;
                color: white;
                border: 1px solid white;
                padding: 4px;
                border-radius: 4px;
            }
        """)
        self.setCentralWidget(main)

        # --- 系统托盘图标设置 ---
        self.tray_icon = QSystemTrayIcon(self)
        # 使用一个存在的图标，例如 Y_black.ico
        tray_icon_path = os.path.join(base_dir, "icon", "Y_black.ico")
        if os.path.exists(tray_icon_path):
            self.tray_icon.setIcon(QIcon(tray_icon_path))
        else:
            # 如果找不到指定图标，使用标准图标作为备选
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
            print(f"警告: 找不到托盘图标文件: {tray_icon_path}, 使用默认图标。")

        show_action = QAction("显示", self)
        tool_show = QAction("小工具", self)
        quit_action = QAction("退出", self)

        show_action.triggered.connect(self.showNormal)  # 使用 showNormal 恢复窗口
        tool_show.triggered.connect(self.show_popup_widget)
        quit_action.triggered.connect(self.quit_application)

        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(tool_show)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)

        # 连接 activated 信号，处理左键单击
        self.tray_icon.activated.connect(self.tray_icon_activated)

        self.tray_icon.show()
        # -----------------------------

        # +++ 在这里创建并持有 popup_widget 的实例 +++
        self.popup_widget = Win11StylePopup()
        # ++++++++++++++++++++++++++++++++++++++++++++

        # --- 添加用于区分单击/双击的定时器 ---
        self.click_timer = QTimer(self)
        self.click_timer.setInterval(QApplication.doubleClickInterval()) # 使用系统双击间隔
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self.handle_single_click) # 定时器超时执行单击操作
        # ------------------------------------

        gv.or_changed.connect(lambda value: self.statusBar.showMessage(value, 3000))
        gv.or_changed.connect(self.change_connect)
        gv.or_changed.connect(self.popup_widget.load_history)

        self.update = Temp_update.CheckUpdate()
        self.update.update_signal.connect(self.handle_update_signal)  # 连接到新的处理函数

        # 标记是否因为更新而关闭
        self.closing_for_update = False

    def handle_update_signal(self, signal_type):
        """处理来自更新模块的信号"""
        if signal_type == "close":
            self.closing_for_update = True  # 设置标志
            self.close()  # 触发 closeEvent

    def closeEvent(self, event):
        """重写关闭事件，实现最小化到托盘"""
        # 检查是否是更新程序请求关闭
        if self.closing_for_update:
            print("正在为更新关闭...")
            if hasattr(self, 'clip_plane') and self.clip_plane:
                self.clip_plane.close_widget()  # 关闭悬浮窗
            if hasattr(self, 'file_exchange') and self.file_exchange:
                self.file_exchange.disconnect_network()  # 断开网络连接
            self.tray_icon.hide()  # 隐藏托盘图标
            event.accept()  # 接受关闭事件，允许窗口关闭
        else:
            # 用户点击关闭按钮或其他正常关闭操作
            print("最小化到系统托盘...")
            event.ignore()  # 忽略默认的关闭事件（不退出程序）
            self.hide()  # 隐藏主窗口
            self.tray_icon.showMessage(
                "Ysure 工具组件",
                "应用程序已最小化到系统托盘",
                QSystemTrayIcon.Information,
                2000  # 消息显示时间（毫秒）
            )




    # --- 修改后的 tray_icon_activated (使用定时器) ---
    def tray_icon_activated(self, reason):
        """处理托盘图标的激活事件（单击和双击）"""
        if reason == QSystemTrayIcon.DoubleClick:
            # 如果是双击，立即停止定时器（如果正在运行）并执行双击操作
            self.click_timer.stop()
            self.handle_double_click()
        elif reason == QSystemTrayIcon.Trigger:
            # 如果是单击，启动（或重启）定时器
            self.click_timer.start(100)
        # ---------------------------------------------

        # --- 新增：处理定时器超时（即确认为单击） ---

    def handle_single_click(self):
        """执行单击操作：切换小工具"""
        print("Detected single click")
        self.show_popup_widget()
        # ------------------------------------------

        # --- 新增：处理双击操作 ---

    def handle_double_click(self):
        """执行双击操作：显示主窗口"""
        print("Detected double click")
        self.show_main_window()

    # -------------------------
    def quit_application(self):
        """处理退出应用程序的请求"""
        print("正在退出应用程序...")
        # 在退出前执行必要的清理工作
        if hasattr(self, 'clip_plane') and self.clip_plane:
            self.clip_plane.close_widget()  # 关闭悬浮窗
        if hasattr(self, 'file_exchange') and self.file_exchange:
            self.file_exchange.disconnect_network()  # 断开网络连接

        self.tray_icon.hide()  # 隐藏托盘图标
        QApplication.quit()  # 退出应用程序

    def save(self):
        Function.ini(Global_Vars.Root, Global_Vars.Project, Global_Vars.User)
        self.statusBar.showMessage("保存成功", 3000)

    def update_version(self):
        if not self.update.check_update():
            self.statusBar.showMessage("你已经是最新版本!!", 5000)


    def show_main_window(self):
        """显示主窗口并激活"""
        if self.isHidden():
            self.show()
        self.activateWindow()
        # if hasattr(self, 'popup_widget') and self.popup_widget.isVisible():
        #     self.popup_widget.hide()

    def show_popup_widget(self):

        if self.popup_widget.isHidden():
            self.popup_widget.show_at_bottom_right()
        else:
            self.popup_widget.hide()

    def change_connect(self):
        # 确保总是从 Global_Vars 获取最新的值
        current_user = Global_Vars.gv.user
        current_project = Global_Vars.gv.project
        current_task = Global_Vars.gv.task
        print(
            f"DEBUG (main.py): change_connect called. User: {current_user}, Project: {current_project}, Task: {current_task}")  # 调试信息
        if hasattr(self, 'file_exchange') and isinstance(self.file_exchange, FileSenderWidget):
            self.file_exchange.update_user_and_project(current_user, current_project, current_task)
            # self.file_exchange.set_current_task(current_task) # set_current_task 会在 update_user_and_project 内部调用
        else:
            print("DEBUG (main.py): file_exchange widget not found or not FileSenderWidget")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 阻止在最后一个窗口隐藏时退出应用程序
    app.setQuitOnLastWindowClosed(False)

    # 检查系统托盘是否可用 (可选但推荐)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "错误", "未检测到系统托盘。")
        # sys.exit(1) # 如果托盘是必需的，则退出

    w = MainWindow()
    w.show()
    sys.exit(app.exec_())  # 使用 sys.exit(app.exec_()) 以获取正确的退出代码
