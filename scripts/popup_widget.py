import sys
import os  # 导入 os
import json  # 导入 json
import datetime  # 导入 datetime
from PySide2.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QApplication, QPushButton, QFrame,
    QListWidget, QListWidgetItem  # 导入 QListWidget 和 QListWidgetItem
)
from PySide2.QtCore import Qt, QRect, QPoint, QEvent, QSize, QUrl
from PySide2.QtGui import (QColor, QPalette, QFont, QCursor, QDragEnterEvent,
                           QDragLeaveEvent, QDropEvent, QDesktopServices)  # 导入事件 和 QDesktopServices

# 从 scripts 导入 Function 和 Global_Vars 模块
from scripts import Function, Global_Vars
# 从 address_trans 导入 Drag_Function 类
from scripts.address_trans import Drag_Function
from scripts.file_exchange_online import DraggableListWidget


class Win11StylePopup(QWidget):
    """
    一个模仿 Win11 弹出菜单样式的简单小部件。
    包含路径转换和文件发送历史记录功能。
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 调整初始大小以容纳新组件
        self.initial_height = 450  # 再次增加高度
        self.initial_width = 400  # 增加宽度

        # --- 窗口设置 ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.Popup)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(self.initial_width, self.initial_height)  # 使用固定大小
        self.setFocusPolicy(Qt.StrongFocus)

        # --- 创建一个内部容器 QFrame ---
        self.container = QFrame(self)
        # 更新样式以包含 QListWidget
        self.container.setStyleSheet("""
            QFrame {
                background-color: #222222; /* 深色背景 */
                border-radius: 8px;     /* 圆角 */
                color: #DCDCDC;         /* 容器内默认文本颜色 */
            }
            QPushButton {
                background-color: #444444;
                color: #DCDCDC;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 4px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
            QListWidget { /* 列表样式 */
                background-color: #2D2D2D; /* 列表背景色 */
                border: 1px solid #444444; /* 列表边框 */
                border-radius: 4px;
                color: #DCDCDC; /* 列表项文本颜色 */
                outline: 0px; /* 去除选中时的虚线框 */
            }
            QListWidget::item {
                padding: 5px; /* 列表项内边距 */
            }
            QListWidget::item:selected {
                background-color: #555555; /* 选中项背景色 */
                color: #FFFFFF; /* 选中项文本颜色 */
            }
            QListWidget::item:hover {
                background-color: #444444; /* 悬停项背景色 */
            }
        """)
        self.container.setGeometry(self.rect())

        # --- 布局 (现在添加到 container 内部) ---
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(10)  # 增加组件间距

        # --- 添加路径转换按钮 ---
        button_layout = QHBoxLayout()
        btn_M2W = QPushButton("Mac ➔ Windows")
        btn_W2M = QPushButton("Windows ➔ Mac")
        btn_font = QFont()
        btn_font.setPointSize(10)
        btn_M2W.setFont(btn_font)
        btn_W2M.setFont(btn_font)
        button_layout.addWidget(btn_M2W)
        button_layout.addWidget(btn_W2M)
        self.content_layout.addLayout(button_layout)

        # --- 添加拖放区域 ---
        self.drag_lab = Drag_Function()
        drag_font = QFont()
        drag_font.setPointSize(14)
        self.drag_lab.setFont(drag_font)
        self.drag_lab.setMinimumHeight(60)  # 调整拖放区域高度
        self.drag_lab.setMaximumHeight(80)
        self.content_layout.addWidget(self.drag_lab)  # 不设置拉伸因子

        # --- 添加历史记录列表 ---
        history_label = QLabel("文件发送历史:")
        history_label.setStyleSheet("color: #AAAAAA; margin-top: 5px;")  # 标签样式
        self.content_layout.addWidget(history_label)

        refresh_btn = QPushButton("刷新")
        self.content_layout.addWidget(refresh_btn)
        refresh_btn.clicked.connect(self.load_history)

        self.history_list = DraggableListWidget(self.container)
        self.history_list.setAlternatingRowColors(False)  # 可以关闭交替行颜色，如果背景足够区分
        self.content_layout.addWidget(self.history_list, 1)  # 添加列表，设置拉伸因子1使其填充剩余空间

        # --- 连接信号 ---
        btn_M2W.pressed.connect(self.get_Win_Address)
        btn_W2M.pressed.connect(self.get_Mac_Address)
        self.history_list.itemDoubleClicked.connect(self.open_history_folder)  # 连接双击信号

        # 初始时隐藏
        self.hide()

    # --- 实现路径转换方法 ---
    def get_Win_Address(self):
        """从剪贴板获取 Mac 路径并转换为 Windows 路径"""
        try:
            mac_path = Function.get_from_clipboard()
            if mac_path:
                Function.mac_2_win(mac_path)
            else:
                print("剪贴板为空")
        except Exception as e:
            print(f"Mac 到 Win 转换出错: {e}")

    def get_Mac_Address(self):
        """从剪贴板获取 Windows 路径并转换为 Mac 路径"""
        try:
            win_path = Function.get_from_clipboard()
            if win_path:
                Function.win_2_mac(win_path)
            else:
                print("剪贴板为空")
        except Exception as e:
            print(f"Win 到 Mac 转换出错: {e}")

    # --- 历史记录相关方法 ---
    def get_log_file_path(self):
        """获取日志文件的完整路径"""
        # 确保 Global_Vars.Project 有效
        project_root = Global_Vars.gv.project  # 使用 gv 获取最新值
        if project_root and os.path.isdir(project_root):
            log_dir = os.path.join(project_root, ".file_sender_logs")  # 使用与 file_exchange_online 相同的日志文件夹
            try:
                os.makedirs(log_dir, exist_ok=True)
                return os.path.join(log_dir, "file_info_log.jsonl")  # JSON Lines 格式
            except OSError as e:
                print(f"创建日志目录时出错 {log_dir}: {e}")
                return None
        else:
            print(f"项目根目录无效或未设置: {project_root}")
            return None

    def load_history(self):
        """从日志文件加载历史记录到列表"""
        self.history_list.clear()
        log_file = self.get_log_file_path()

        if not log_file or not os.path.exists(log_file):
            print("无法加载历史记录：日志文件路径未设置或文件不存在。")
            return

        try:
            entries = []
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        # 跳过空行
                        stripped_line = line.strip()
                        if not stripped_line:
                            continue
                        log_entry = json.loads(stripped_line)
                        entries.append(log_entry)
                    except json.JSONDecodeError:
                        print(f"跳过历史日志中的无效行: {line.strip()}")

            # 按时间戳降序排序（最新的在前面）
            entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            # 添加到列表控件
            for log_entry in entries:
                users = log_entry.get("users", ["N/A", "N/A"])
                filename = log_entry.get("filename", "N/A")
                send_time_str = log_entry.get("date_sent", "N/A")
                # 尝试解析时间并格式化
                try:
                    send_time_dt = datetime.datetime.fromisoformat(send_time_str)
                    display_time = send_time_dt.strftime("%m-%d %H:%M")  # 月-日 时:分
                except (ValueError, TypeError):
                    display_time = send_time_str  # 如果解析失败，显示原始字符串

                notes = log_entry.get("notes", "")  # 默认为空字符串

                # 确保 users 列表至少有两个元素
                sender = users[0] if len(users) > 0 else "N/A"
                recipient = users[1] if len(users) > 1 else "N/A"

                # 格式化显示文本
                history_text = f"{display_time} [{sender}➔{recipient}] {filename}"
                if notes:
                    history_text += f" ({notes})"  # 如果有备注则添加

                list_item = QListWidgetItem(history_text)
                # 将原始文件路径存储在 UserRole 中，用于双击打开文件夹
                list_item.setData(Qt.UserRole, log_entry.get('path'))
                self.history_list.addItem(list_item)

        except Exception as e:
            print(f"从 {log_file} 加载历史记录时出错: {e}")

    def open_history_folder(self, item: QListWidgetItem):
        """双击历史记录项时打开文件所在的文件夹"""
        if item is None:
            return
        file_path = item.data(Qt.UserRole)
        if file_path and isinstance(file_path, str):
            folder_path = os.path.dirname(file_path)
            if os.path.exists(folder_path):
                try:
                    # 使用 QDesktopServices 打开文件夹，更跨平台
                    QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
                    print(f"尝试打开文件夹: {folder_path}")
                except Exception as e:
                    print(f"无法打开文件夹 {folder_path}: {e}")
                    # 可以添加一个 QMessageBox 提示用户
            else:
                print(f"历史记录中的文件夹路径不存在: {folder_path}")
                # 可以添加一个 QMessageBox 提示用户
        else:
            print("历史记录项中未找到有效的路径数据。")

    # --- 窗口显示和事件处理 ---
    def show_at_bottom_right(self):
        """计算屏幕右下角位置并显示窗口，同时加载历史记录"""
        # 在显示前加载历史记录
        self.load_history()

        screen_geometry = QApplication.primaryScreen().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        widget_width = self.width()
        widget_height = self.height()

        margin = 10
        x = screen_width - widget_width - margin
        y = screen_height - widget_height - margin

        self.move(x, y)
        self.show()
        self.activateWindow()
        self.setFocus()

    def focusOutEvent(self, event: QEvent):
        """当窗口失去焦点时自动隐藏"""
        super().focusOutEvent(event)

        # 检查窗口当前是否仍然可见
        # Check if the window is still visible
        if self.isVisible():
            print(f"调试：窗口失去焦点 (原因: {event.reason()}), 尝试隐藏...")
            # Debug: Window lost focus (reason: ...), attempting to hide...
            self.hide()
            print(f"调试：窗口隐藏后是否可见: {self.isVisible()}")
            # Debug: Is window visible after hiding: ...
        else:
            print("调试：窗口失去焦点，但它已经不可见。")
            # Debug: Window lost focus, but it was already hidden.

    def mousePressEvent(self, event: QEvent):
        """重写鼠标按下事件，点击内部时不关闭"""
        # 检查点击是否在窗口矩形内
        if event.button() == Qt.LeftButton and self.rect().contains(event.pos()):
            # 点击内部，接受事件，但不做任何操作 (不调用 self.hide())
            event.accept()
            print('yes')
        else:
            # 对于其他鼠标按钮或理论上的外部点击（主要由 focusOutEvent 处理），调用父类
            super().mousePressEvent(event)
            print('no')

    def resizeEvent(self, event):
        """当窗口大小调整时，确保容器也调整大小"""
        self.container.setGeometry(self.rect())
        super().resizeEvent(event)

    def get_content_layout(self):
        """返回内容布局，如果需要从外部添加更多组件"""
        return self.content_layout
