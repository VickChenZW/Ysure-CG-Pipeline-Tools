import sys
import os
import socket
import threading
import json
import time
import datetime  # For timestamp in message
import subprocess  # Added import
import shutil  # Keep for potential future use, though not used now

# --- PySide2 Imports ---
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt, QDir, QModelIndex, QThread, Signal, Slot, QUrl, QTimer, QMimeData, QPoint
# Added QDesktopServices import
from PySide2.QtGui import QDesktopServices, QStandardItemModel, QStandardItem, QDrag, QColor # Added QColor
from PySide2.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QTextEdit, QLineEdit, QPushButton, QTreeView,
    QSplitter, QLabel, QMessageBox, QInputDialog,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDialog, QDialogButtonBox, # Keep QTableWidget imports for now if needed elsewhere, but remove usage here
    QComboBox, QListWidgetItem
)
from scripts.Global_Vars import gv

# --- Configuration ---
BROADCAST_PORT = 50001
TCP_PORT = 50003
BUFFER_SIZE = 4096
VALID_SUBDIRS = ["geo", "tex", "alembic"]  # Define valid types

class EditNotesDialog(QDialog):
    """
    编辑notes的Dialog
    """
    def __init__(self, initial_notes="", parent=None): # Added parent=None and default value
        super().__init__(parent)
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

    # Removed accept_and_destroy as it's not standard QDialog behavior

# --- DraggableListWidget (Copied from user's file) ---
class DraggableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is None:
            return

        # Assuming item data (Qt.UserRole) stores the full path
        file_path = item.data(Qt.UserRole)
        if not file_path or not isinstance(file_path, str):
             print("DraggableListWidget: No valid file path found in item data.")
             return

        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(file_path)])

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        # Optional: Set pixmap for drag visual
        # drag.setPixmap(item.icon().pixmap(50, 50))
        drag.setHotSpot(QPoint(10, 10)) # Adjust hotspot if needed

        drag.exec_(supportedActions)


# --- Main Widget ---
class FileSenderWidget(QWidget):

    show_message_box = Signal(str, str, str) # icon_type, title, text

    def __init__(self, user_name, project_root, current_task=None, parent=None): # Added current_task
        super().__init__(parent)
        self.user_name = user_name
        self.project_root = project_root.replace('\\', '/') if project_root else None
        self.current_task = current_task # Store the current task name
        self.users = {}
        self.log_file = None
        self.is_connected = False

        # Connect internal signals
        # self.show_message_box.connect(self._show_message_box_slot)

        # UI Setup
        self._setup_ui()

        # Initial Project Check & Setup
        if not self.project_root or not os.path.isdir(os.path.join(self.project_root, "2.Project")):
             print(f"FileSenderWidget: Initial project root '{self.project_root}' invalid.")
             self.initialize_project_root(None)
        else:
            self.initialize_project_root(self.project_root)

    def _setup_ui(self):
        """Creates the UI elements."""
        main_layout = QVBoxLayout(self)  # Use QVBoxLayout as main layout
        self.setLayout(main_layout)

        # Project Label (Button removed)
        project_layout = QHBoxLayout()
        self.project_label = QLabel(f"项目: {os.path.basename(self.project_root) if self.project_root else '未设置'}")
        self.project_label.setWordWrap(True)
        project_layout.addWidget(self.project_label, 1)
        main_layout.addLayout(project_layout)

        # --- ADDED: Main Vertical Splitter ---
        self.main_vertical_splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(self.main_vertical_splitter, 1)  # Add splitter with stretch

        # --- Middle Section (Users & Files) - Now inside a container ---
        middle_container = QWidget()
        middle_layout = QHBoxLayout(middle_container)  # Use QHBoxLayout for the splitter inside
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_splitter = QSplitter(Qt.Horizontal)
        middle_layout.addWidget(middle_splitter)  # Add horizontal splitter to container layout
        # -----------------------------------------------------------------

        # Users List Area
        user_list_widget_container = QWidget()
        user_list_layout = QVBoxLayout(user_list_widget_container)
        user_list_layout.setContentsMargins(0, 0, 0, 0)  # Remove layout margins
        user_header_layout = QHBoxLayout()
        user_header_layout.addWidget(QLabel("使用用户:"))
        self.refresh_users_button = QPushButton("🔄")  # Refresh button
        self.refresh_users_button.setFixedSize(25, 25)  # Make button small
        self.refresh_users_button.setToolTip("刷新使用用户列表")
        self.refresh_users_button.clicked.connect(self._refresh_user_list)
        user_header_layout.addWidget(self.refresh_users_button)
        user_header_layout.addStretch()  # Push button to the right
        user_list_layout.addLayout(user_header_layout)  # Add header layout
        self.user_list_widget = QListWidget()
        self.user_list_widget.itemSelectionChanged.connect(self.on_user_or_file_selected)
        user_list_layout.addWidget(self.user_list_widget)  # Add list below header
        user_list_widget_container.setMinimumWidth(150)
        user_list_widget_container.setMaximumWidth(300)
        middle_splitter.addWidget(user_list_widget_container)  # Add to HORIZONTAL splitter

        # Files Area
        files_widget = QWidget()
        files_layout = QVBoxLayout(files_widget)
        file_filter_layout = QHBoxLayout()
        file_filter_layout.addWidget(QLabel("文件类型:"))
        self.subdir_filter_combo = QComboBox()
        self.subdir_filter_combo.addItems(VALID_SUBDIRS)
        self.subdir_filter_combo.addItems(['Project'])
        self.subdir_filter_combo.currentIndexChanged.connect(self.update_file_tree_view)
        file_filter_layout.addWidget(self.subdir_filter_combo)
        files_layout.addLayout(file_filter_layout)
        self.file_list_label = QLabel(f"文件 ({self.user_name} / {self.current_task or '未选任务'}):")
        self.file_list_label.setObjectName("file_list_label")
        files_layout.addWidget(self.file_list_label)
        self.refresh_files_list_btn = QPushButton('刷新')
        self.refresh_files_list_btn.pressed.connect(self.update_file_tree_view)
        files_layout.addWidget(self.refresh_files_list_btn)
        self.file_tree_view = QTreeView()
        self.file_tree_model = QStandardItemModel()
        self.file_tree_view.setModel(self.file_tree_model)
        self.file_tree_view.setHeaderHidden(True)
        self.file_tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.file_tree_view.selectionModel().selectionChanged.connect(self.on_user_or_file_selected)
        files_layout.addWidget(self.file_tree_view)
        self.send_file_info_button = QPushButton("发送文件信息")
        self.send_file_info_button.setEnabled(False)
        self.send_file_info_button.clicked.connect(self.send_file_info)
        files_layout.addWidget(self.send_file_info_button)
        middle_splitter.addWidget(files_widget)  # Add to HORIZONTAL splitter

        middle_splitter.setSizes([200, 400])  # Adjust initial sizes

        # Add the middle container (with the horizontal splitter) to the VERTICAL splitter
        self.main_vertical_splitter.addWidget(middle_container)

        # --- Bottom Section: History List - Now inside a container ---
        history_container = QWidget()
        history_layout = QVBoxLayout(history_container)
        history_layout.setContentsMargins(0, 5, 0, 0)  # Add some top margin
        history_layout.addWidget(QLabel("文件信息历史:"))
        self.history_list_widget = DraggableListWidget()  # Use DraggableListWidget from user's code
        self.history_list_widget.doubleClicked.connect(
            lambda value: os.startfile(os.path.dirname(value.data(Qt.UserRole)))
        )  # Connect double click
        # self.history_list_widget.setMaximumHeight(150) # Max height controlled by splitter now
        history_layout.addWidget(self.history_list_widget)
        # -------------------------------------------------------------

        # Add the history container to the VERTICAL splitter
        self.main_vertical_splitter.addWidget(history_container)

        # Set initial sizes for the vertical splitter (adjust ratio as needed)
        self.main_vertical_splitter.setSizes([400, 150])  # Give more space to top initially

    # --- Public methods for parent interaction ---
    def update_user_and_project(self, user_name, project_root, task_name=None): # Added task_name
        """Allows the parent application to update user, project, and task."""
        print(f"FileSenderWidget: Updating user='{user_name}', project='{project_root}', task='{task_name}'")
        if not user_name:
            print("FileSenderWidget: Update rejected, user_name empty.")
            return

        user_changed = (self.user_name != user_name)
        new_project_root = project_root.replace('\\', '/') if project_root else None
        project_changed = (self.project_root != new_project_root)
        task_changed = (self.current_task != task_name)

        if not user_changed and not project_changed and not task_changed:
            print("FileSenderWidget: No change in user, project, or task.")
            return

        self.user_name = user_name
        self.current_task = task_name # Update task


        # Re-init UI and logs only if project changed or was previously None
        if project_changed or self.project_root is None:
            self.initialize_project_root(new_project_root) # This will also update the tree view
            self._refresh_user_list()
        elif user_changed or task_changed:
             # If only user or task changed, update label and repopulate tree
            self.file_list_label.setText(f"文件 ({self.user_name} / {self.current_task or '未选任务'}):")
            self.update_file_tree_view() # Repopulate tree for new user/task


    def set_current_task(self, task_name):
        """Public method specifically for updating the task and refreshing the view."""
        print(f"FileSenderWidget: Setting task to '{task_name}'")
        if self.current_task != task_name:
            self.current_task = task_name
            self.file_list_label.setText(f"文件 ({self.user_name} / {self.current_task or '未选任务'}):")
            self.update_file_tree_view() # Refresh tree view for the new task

    def initialize_project_root(self, directory):
         """Sets up the application based on the selected project root."""
         # Clear previous state
         self.file_tree_model.clear()
         self.send_file_info_button.setEnabled(False)
         self.history_list_widget.clear() # Clear history list

         if directory and os.path.isdir(os.path.join(directory, "2.Project")):
             self.project_root = directory
             self.project_label.setText(f"项目: {os.path.basename(self.project_root)}") # Update label
             self.file_list_label.setText(f"文件 ({self.user_name} / {self.current_task or '未选任务'}):")
             self.update_file_tree_view() # Populate file tree using current task
             self.setup_log_file() # Setup log file
             self.load_history() # Load history from log file
             self.on_user_or_file_selected() # Re-evaluate button state
         else:
             self.project_root = None
             self.project_label.setText("项目: 未设置") # Update label
             # self.update_connection_status("项目无效或未设置。")
             self.log_file = None
             self.send_file_info_button.setEnabled(False)

    @Slot()
    def update_file_tree_view(self):
        """Populates the file tree view for the current user/task/subdir."""
        self.file_tree_model.clear()
        self.send_file_info_button.setEnabled(False) # Disable button during update

        # Check prerequisites
        if not self.project_root or not self.user_name or not self.current_task:
            status = "项目、用户或任务未设置"
            if not self.project_root: status = "项目未设置"
            elif not self.user_name: status = "用户未设置"
            elif not self.current_task: status = "任务未选择"
            print(f"Cannot populate file tree: {status}")
            root_item = QStandardItem(status)
            root_item.setEnabled(False)
            self.file_tree_model.appendRow(root_item)
            return

        # Construct the specific task path to scan
        task_path = os.path.join(self.project_root, "2.Project", self.user_name, self.current_task).replace('\\', '/')
        selected_subdir = self.subdir_filter_combo.currentText()
        if selected_subdir == 'Project':
            target_dir = task_path.replace('\\', '/')
        else:
            target_dir = os.path.join(task_path, selected_subdir).replace('\\', '/')

        # Set header label for the tree
        self.file_tree_model.setHorizontalHeaderLabels([f"{self.current_task} / {selected_subdir}"])

        if not os.path.isdir(target_dir):
            status_msg = f"目录不存在: .../{self.user_name}/{self.current_task}/{selected_subdir}"
            print(status_msg)
            root_item = QStandardItem(status_msg)
            root_item.setEnabled(False)
            self.file_tree_model.appendRow(root_item)
            return

        print(f"Populating file tree for: {target_dir}")
        root_node = self.file_tree_model.invisibleRootItem()
        # Directly list files in the target directory
        try:
            for filename in os.listdir(target_dir):
                full_path = os.path.join(target_dir, filename).replace('\\', '/')
                if os.path.isfile(full_path): # Only list files
                    file_item = QStandardItem(filename)
                    file_item.setEditable(False)
                    # Store full path and subdir type in item data
                    file_item.setData(full_path, Qt.UserRole)
                    # file_item.setData(selected_subdir, Qt.UserRole + 1) # Store subdir type (Not needed anymore?)
                    root_node.appendRow(file_item)
        except Exception as e:
             print(f"Error listing directory {target_dir}: {e}")
             root_item = QStandardItem(f"读取目录时出错")
             root_item.setEnabled(False)
             self.file_tree_model.appendRow(root_item)


    def get_log_file_path(self, filename):
        """Gets the full path for a log file within the project root."""
        if self.project_root and os.path.isdir(self.project_root):
            log_dir = os.path.join(self.project_root, ".file_sender_logs") # Different log folder
            try:
                os.makedirs(log_dir, exist_ok=True)
                return os.path.join(log_dir, filename)
            except OSError as e:
                print(f"Error creating log directory {log_dir}: {e}")
                return None
        return None

    def setup_log_file(self):
         """Sets up the log file path."""
         self.log_file = self.get_log_file_path("file_info_log.jsonl") # JSON Lines format
         if self.log_file:
             print(f"Log file set to: {self.log_file}")
         else:
             print("Logging disabled.")

    # --- Restored log_file_info from user's version ---
    def log_file_info(self, direction, user, file_info_dict):
        """Logs sent/received file info and updates history list."""
        filename = file_info_dict.get("filename", "N/A")
        # Determine the 'users' list based on direction
        if direction == "Sent":
            users_list = [self.user_name, user]
        elif direction == "Received":
            users_list = [user, self.user_name]
        else:
            users_list = [self.user_name, user] # Default or fallback

        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "users": users_list,  # Use the determined list
            "filename": filename,
            "date_sent": file_info_dict.get("date"), # Original sent date
            "path": file_info_dict.get("full_source_path"),
            "notes": file_info_dict.get("notes") # Include notes
        }

        # Add to history list widget (using the user's format)
        send_time = log_entry.get("date_sent", "N/A")
        notes = log_entry.get("notes", "N/A")
        history_text = f"{send_time}:{filename} ({users_list[0]} ➡️ {users_list[1]})  ({notes})"

        list_item = QListWidgetItem(history_text)
        # Store the original source path in the list item's data role
        list_item.setData(Qt.UserRole, file_info_dict.get("full_source_path"))
        self.history_list_widget.insertItem(0, list_item) # Prepend

        # Add to log file
        if not self.log_file:
            print("Logging disabled: Log file path not set.")
            return
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                json.dump(log_entry, f, ensure_ascii=False) # Use ensure_ascii=False for notes
                f.write('\n')
        except Exception as e:
            print(f"Error writing to log file {self.log_file}: {e}")

    # --- Restored load_history from user's version ---
    def load_history(self):
        """Loads history from log file into the list widget."""
        self.history_list_widget.clear()
        if not self.log_file or not os.path.exists(self.log_file):
            print("Cannot load history: Log file path not set or file does not exist.")
            return
        try:
            entries = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        entries.append(log_entry)
                    except json.JSONDecodeError:
                        print(f"Skipping invalid line in history log: {line.strip()}")

            # Sort entries by timestamp descending (newest first)
            entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            # Add to list widget
            for log_entry in entries:
                users = log_entry.get("users", ["N/A", "N/A"])
                filename = log_entry.get("filename", "N/A")
                send_time = log_entry.get("date_sent", "N/A")
                notes = log_entry.get("notes", "") # Default to empty string if missing

                # Ensure users list has at least two elements before accessing indices
                sender = users[0] if len(users) > 0 else "N/A"
                recipient = users[1] if len(users) > 1 else "N/A"

                history_text = f"{send_time}:{filename} ({sender} ➡️ {recipient})  ({notes})"
                if self.user_name in users:
                    list_item = QListWidgetItem(history_text)
                    list_item.setData(Qt.UserRole, log_entry.get('path'))
                    self.history_list_widget.addItem(list_item) # Append to show oldest first, or insertItem(0,...) for newest first

        except Exception as e:
            print(f"Error loading history from {self.log_file}: {e}")


    @Slot()
    def _refresh_user_list(self):
        """Clears the user list. Users will reappear on next discovery broadcast."""
        self.user_list_widget.clear()
        if os.path.exists(os.path.join(gv.project, ('2.Project'))):
            print(os.path.join(gv.project, ('2.Project')))
            for user in os.listdir(os.path.join(gv.project, ('2.Project'))):
                if not os.path.basename(user).startswith('.'):
                    self.user_list_widget.addItem(os.path.basename(user))
        self.load_history()

    @Slot()
    def on_user_or_file_selected(self):
        """Enables/disables the send file button based on user and file selection."""
        selected_user_items = self.user_list_widget.selectedItems()
        selected_file_indexes = self.file_tree_view.selectedIndexes()
        user_selected = bool(selected_user_items)
        file_selected = False
        if selected_file_indexes:
            index = selected_file_indexes[0]
            # Check if the selected item has file path data (i.e., it's a file item)
            if index.isValid() and self.file_tree_model.itemFromIndex(index).data(Qt.UserRole):
                 file_selected = True
        self.send_file_info_button.setEnabled(user_selected and file_selected)

    # --- Restored send_file_info to include notes dialog ---
    def send_file_info(self):
        """Sends the selected file's information (including notes) to the chosen user."""

        selected_user_items = self.user_list_widget.selectedItems()
        selected_file_indexes = self.file_tree_view.selectedIndexes()

        if not selected_user_items or not selected_file_indexes:
            self.on_user_or_file_selected()
            return
        index = selected_file_indexes[0]
        item = self.file_tree_model.itemFromIndex(index)
        if not index.isValid() or not item or not item.data(Qt.UserRole):
            self.on_user_or_file_selected()
            return

        source_file_path = item.data(Qt.UserRole)
        filename = os.path.basename(source_file_path)
        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        recipient_name = selected_user_items[0].text()

        # Show notes dialog
        dialog = EditNotesDialog("", self) # Pass self as parent
        if dialog.exec_() == QDialog.Accepted:
            notes = dialog.notes_edit.toPlainText().strip()
            file_info_data = {
                'type': 'file_info',
                'sender': self.user_name,
                'filename': filename,
                'date': current_date,
                'full_source_path': source_file_path.replace('\\', '/'),
                'notes': notes # Include notes
            }


            # Log locally (using the user's log format)
            self.log_file_info("Sent", recipient_name, file_info_data)
            self.update_connection_status(f"已发送文件信息 '{filename}' 给 {recipient_name}")
            self.load_history() # Refresh history list after logging
        else:
            QMessageBox.information(self, "提示", "发送已取消!")

    # def load_history(self):
    #     """从日志文件加载历史记录到列表"""
    #     self.history_list.clear()
    #     log_file = self.get_log_file_path()
    #
    #     if not log_file or not os.path.exists(log_file):
    #         print("无法加载历史记录：日志文件路径未设置或文件不存在。")
    #         return
    #
    #     try:
    #         entries = []
    #         with open(log_file, 'r', encoding='utf-8') as f:
    #             for line in f:
    #                 try:
    #                     # 跳过空行
    #                     stripped_line = line.strip()
    #                     if not stripped_line:
    #                         continue
    #                     log_entry = json.loads(stripped_line)
    #                     entries.append(log_entry)
    #                 except json.JSONDecodeError:
    #                     print(f"跳过历史日志中的无效行: {line.strip()}")
    #
    #         # 按时间戳降序排序（最新的在前面）
    #         entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    #
    #         # 添加到列表控件
    #         for log_entry in entries:
    #             users = log_entry.get("users", ["N/A", "N/A"])
    #             filename = log_entry.get("filename", "N/A")
    #             send_time_str = log_entry.get("date_sent", "N/A")
    #             # 尝试解析时间并格式化
    #             try:
    #                 send_time_dt = datetime.datetime.fromisoformat(send_time_str)
    #                 display_time = send_time_dt.strftime("%m-%d %H:%M")  # 月-日 时:分
    #             except (ValueError, TypeError):
    #                 display_time = send_time_str  # 如果解析失败，显示原始字符串
    #
    #             notes = log_entry.get("notes", "")  # 默认为空字符串
    #
    #             # 确保 users 列表至少有两个元素
    #             sender = users[0] if len(users) > 0 else "N/A"
    #             recipient = users[1] if len(users) > 1 else "N/A"
    #
    #             # 格式化显示文本
    #             history_text = f"{display_time} [{sender}➔{recipient}] {filename}"
    #             if notes:
    #                 history_text += f" ({notes})"  # 如果有备注则添加
    #
    #             if Global_Vars.User in users:
    #
    #                 list_item = QListWidgetItem(history_text)
    #                 # print(filename.endswith())
    #                 if filename.split('.')[-1] in ['fbx', 'abc', 'rs', 'obj']:
    #                     item_icon = QIcon(os.path.join(Base_Dir, "../icon", "3d.ico"))
    #                 elif filename.split('.')[-1] in ['jpg', 'exr', 'hdr', 'png', 'tif', 'jpeg']:
    #                     item_icon = QIcon(os.path.join(Base_Dir, "../icon", "image.ico"))
    #                 else:
    #                     item_icon = QIcon(os.path.join(Base_Dir, "../icon", "edit_file.ico"))
    #                 list_item.setIcon(item_icon)
    #                 # 将原始文件路径存储在 UserRole 中，用于双击打开文件夹
    #                 list_item.setData(Qt.UserRole, log_entry.get('path'))
    #                 self.history_list.addItem(list_item)
    #             else:
    #                 pass
    #
    #     except Exception as e:
    #         print(f"从 {log_file} 加载历史记录时出错: {e}")

    @Slot(QListWidgetItem) # Connect to the history list's itemDoubleClicked
    def locate_history_source_file(self, item):
        """Attempts to locate the original source file from history."""
        if item is None:
            return
        # Retrieve the stored source path from the item's data
        source_path = item.data(Qt.UserRole)
        if source_path:
            folder_path = os.path.dirname(source_path)
            if os.path.exists(source_path): # Check if the original source file exists and is accessible
                print(f"Attempting to locate original file: {source_path}")
                url = QUrl.fromLocalFile(folder_path)
                if QDesktopServices.openUrl(url):
                    print("Opened folder via QDesktopServices.")
                    # Try to select the file after opening the folder (Windows specific)
                    if sys.platform == 'win32':
                        try:
                            subprocess.run(['explorer', '/select,', source_path], check=False) # Use check=False to avoid errors if explorer is already open
                        except Exception as e:
                            print(f"Could not select file in explorer: {e}")
                    return
                else:
                    print("QDesktopServices failed, trying platform fallback...")
                    try:
                         if sys.platform == 'win32':
                             subprocess.run(['explorer', '/select,', source_path], check=True)
                         elif sys.platform == 'darwin':
                             subprocess.call(['open', '-R', source_path])
                         else: # Linux and other POSIX
                             subprocess.call(['xdg-open', folder_path]) # Fallback to folder
                    except Exception as e:
                         QMessageBox.warning(self, "无法定位文件", f"无法打开 '{folder_path}'.\n错误: {e}")
                         print(f"Error locating file {source_path} using fallback: {e}")
            else:
                QMessageBox.warning(self, "文件不存在", f"记录的源文件路径 '{source_path}' 不存在或无法访问。")
                print(f"Path not found or inaccessible: {source_path}")
        else:
             print("No source path data found for history item.")


