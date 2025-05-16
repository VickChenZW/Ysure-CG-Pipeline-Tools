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

# --- Configuration ---
BROADCAST_PORT = 50001
TCP_PORT = 50003
BUFFER_SIZE = 4096
VALID_SUBDIRS = ["geo", "tex", "alembic"]  # Define valid types
# USER_TIMEOUT_SECONDS = 30 # REMOVED
# CHECK_TIMEOUT_INTERVAL_MS = 15000 # REMOVED

# --- Network Listener Thread ---
class NetworkListener(QThread):
    """
    后台线程，监听UDP广播和TCP文件信息。
    """
    user_discovered = Signal(str, str)
    connection_status = Signal(str)
    file_info_received = Signal(dict)

    def __init__(self, tcp_port, user_name):
        super().__init__()
        self.tcp_port = tcp_port
        self.user_name = user_name
        self.running = False
        self.tcp_server_socket = None
        self.udp_socket = None
        self.my_local_ip = self.get_local_ip()
        self.broadcast_thread = None

    def run(self):
        self.running = True
        self.connection_status.emit(f"正在监听 UDP:{BROADCAST_PORT}, TCP:{self.tcp_port}...")
        print(f"Network Listener: Starting for user '{self.user_name}'...")

        # UDP Setup
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.udp_socket.bind(('', BROADCAST_PORT))
            self.udp_socket.settimeout(1.0)
        except OSError as e:
            error_msg = f"错误: 无法绑定 UDP {BROADCAST_PORT}: {e}"
            print(f"NL: {error_msg}")
            self.connection_status.emit(error_msg)
            self.running = False
            return

        # TCP Setup
        self.tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.tcp_server_socket.bind(('', self.tcp_port))
            self.tcp_server_socket.listen(5)
            self.tcp_server_socket.settimeout(1.0)
        except OSError as e:
            error_msg = f"错误: 无法绑定 TCP {self.tcp_port}: {e}"
            print(f"NL: {error_msg}")
            self.connection_status.emit(error_msg)
            self.running = False
            if self.udp_socket: # Close UDP socket if TCP fails
                self.udp_socket.close()
            return

        # Broadcast Setup
        if not self.my_local_ip:
            print("NL: Warning - Could not determine local IP.")
        self.broadcast_thread = threading.Thread(target=self.broadcast_presence, daemon=True)
        self.broadcast_thread.start()
        print("NL: Running.")

        # Main Loop
        while self.running:
            # UDP Check
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                if not self.running:
                    break
                if addr[0] == self.my_local_ip:
                    continue
                message = json.loads(data.decode('utf-8'))
                # Only emit discovery, main widget handles timestamping
                if message.get('type') == 'discovery' and message.get('username') != self.user_name:
                    self.user_discovered.emit(message['username'], addr[0])
            except socket.timeout:
                pass # Expected timeout, continue loop
            except Exception as e:
                 if self.running: # Avoid printing error if stopping
                     print(f"NL: UDP Error - {e}")

            # TCP Check
            try:
                client_socket, client_address = self.tcp_server_socket.accept()
                if not self.running:
                    client_socket.close()
                    break
                client_thread = threading.Thread(target=self.handle_tcp_client, args=(client_socket, client_address), daemon=True)
                client_thread.start()
            except socket.timeout:
                pass # Expected timeout, continue loop
            except Exception as e:
                if self.running: # Avoid printing error if stopping
                    print(f"NL: TCP Accept Error - {e}")

        # Cleanup
        print("NL: Stopping...")
        if self.tcp_server_socket:
            try:
                self.tcp_server_socket.close()
            except Exception:
                pass # Ignore errors on close
            self.tcp_server_socket = None
        if self.udp_socket:
            try:
                self.udp_socket.close()
            except Exception:
                pass # Ignore errors on close
            self.udp_socket = None
        self.connection_status.emit("已断开连接")
        print("NL: Stopped.")

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            try:
                IP = socket.gethostbyname(socket.gethostname())
            except Exception:
                IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def broadcast_presence(self):
        if not self.my_local_ip:
            print("NL: Cannot broadcast.")
            return
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        message = json.dumps({'type': 'discovery', 'username': self.user_name, 'tcp_port': self.tcp_port})
        broadcast_address = ('<broadcast>', BROADCAST_PORT)
        print("NL: Broadcast thread started.")
        while self.running:
            try:
                broadcast_socket.sendto(message.encode('utf-8'), broadcast_address)
            except Exception as e:
                print(f"NL: Broadcast Error - {e}")
                time.sleep(10) # Wait longer after error
                continue # Retry broadcast loop
            # Broadcast frequency (e.g., every 10 seconds)
            for _ in range(10):
                 if not self.running:
                     break
                 time.sleep(1)
            if not self.running:
                 break # Exit outer loop if stopped
        broadcast_socket.close()
        print("NL: Broadcast thread stopped.")

    def handle_tcp_client(self, client_socket, client_address):
        """Handles incoming TCP connections (only file info expected)."""
        try:
            full_data = b""
            client_socket.settimeout(10.0)
            while self.running:
                try:
                    chunk = client_socket.recv(BUFFER_SIZE)
                    if not chunk:
                        break # Connection closed
                    full_data += chunk
                    # Basic check for JSON message end
                    if full_data.strip().endswith(b'}') and full_data.strip().startswith(b'{'):
                        break
                except socket.timeout:
                     if not self.running:
                         break
                     print(f"NL: Timeout receiving from {client_address}.")
                     break # Assume incomplete message on timeout

            if not full_data or not self.running:
                return # No data or stopped

            try:
                message_data = json.loads(full_data.decode('utf-8').strip())
                msg_type = message_data.get('type')
                sender = message_data.get('sender', 'Unknown')

                if msg_type == 'file_info':
                    # Validate required fields (including notes now)
                    if all(k in message_data for k in ('sender', 'filename', 'date', 'full_source_path', 'notes')):
                        print(f"NL: Received file_info from {sender} for {message_data.get('filename')}")
                        self.file_info_received.emit(message_data)
                    else:
                        print(f"NL: Received invalid file_info from {sender}: Missing fields.")
                else:
                    print(f"NL: Unknown TCP type from {client_address}: {msg_type}")

            except (json.JSONDecodeError, UnicodeDecodeError, KeyError) as e:
                print(f"NL: TCP Decode Error from {client_address}: {e} - Data: {full_data[:200]}")
            except Exception as e:
                print(f"NL: Error handling TCP client {client_address}: {e}")
        finally:
            try:
                client_socket.close()
            except Exception:
                pass # Ignore errors on close

    def stop(self):
        print("NL: Stop requested.")
        self.running = False
        # Attempt to unblock accept() call
        if self.tcp_server_socket:
            try:
                dummy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                dummy_socket.settimeout(0.5)
                dummy_socket.connect(('127.0.0.1', self.tcp_port))
                dummy_socket.close()
                print("NL: Sent dummy connection.")
            except Exception as e:
                print(f"NL: Info - Dummy connection failed: {e}")

# --- Modify Widget (Copied from user's file) ---
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
    # project_root_changed = Signal(str) # Signal removed as button is removed
    show_message_box = Signal(str, str, str) # icon_type, title, text
    # Signal removed as copy functionality is removed
    # ask_copy_file = Signal(dict)

    def __init__(self, user_name, project_root, current_task=None, parent=None): # Added current_task
        super().__init__(parent)
        self.user_name = user_name
        self.project_root = project_root.replace('\\', '/') if project_root else None
        self.current_task = current_task # Store the current task name
        self.users = {}
        self.log_file = None
        self.is_connected = False

        # Network Listener Setup
        self.network_listener = NetworkListener(TCP_PORT, self.user_name)
        self.network_listener.user_discovered.connect(self.add_user)
        self.network_listener.connection_status.connect(self.update_connection_status)
        self.network_listener.file_info_received.connect(self.handle_incoming_file_info)

        # Connect internal signals
        self.show_message_box.connect(self._show_message_box_slot)

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

        # --- Top Section: Connection & Project ---
        top_layout = QHBoxLayout()
        self.connect_button = QPushButton("🔌 连接")
        self.connect_button.clicked.connect(self.toggle_connection)
        self.connection_status_label = QLabel("未连接")
        self.connection_status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top_layout.addWidget(self.connect_button)
        top_layout.addWidget(self.connection_status_label, 1)
        main_layout.addLayout(top_layout)

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
        user_header_layout.addWidget(QLabel("在线用户:"))
        self.refresh_users_button = QPushButton("🔄")  # Refresh button
        self.refresh_users_button.setFixedSize(25, 25)  # Make button small
        self.refresh_users_button.setToolTip("刷新在线用户列表")
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

        was_connected = self.is_connected
        if self.is_connected:
            self.toggle_connection() # Disconnect if running

        # Update listener's internal username *before* potentially restarting
        self.network_listener.user_name = self.user_name

        # Re-init UI and logs only if project changed or was previously None
        if project_changed or self.project_root is None:
             self.initialize_project_root(new_project_root) # This will also update the tree view
        elif user_changed or task_changed:
             # If only user or task changed, update label and repopulate tree
             self.file_list_label.setText(f"文件 ({self.user_name} / {self.current_task or '未选任务'}):")
             self.update_file_tree_view() # Repopulate tree for new user/task

        if was_connected:
            QTimer.singleShot(500, self.toggle_connection) # Reconnect later

    def set_current_task(self, task_name):
        """Public method specifically for updating the task and refreshing the view."""
        print(f"FileSenderWidget: Setting task to '{task_name}'")
        if self.current_task != task_name:
            self.current_task = task_name
            self.file_list_label.setText(f"文件 ({self.user_name} / {self.current_task or '未选任务'}):")
            self.update_file_tree_view() # Refresh tree view for the new task


    def connect_network(self):
        if not self.is_connected:
            self.toggle_connection()

    def disconnect_network(self):
        if self.is_connected:
            self.toggle_connection()

    # --- Internal Methods ---
    def toggle_connection(self):
        """Starts or stops the network listener thread."""
        if not self.is_connected:
            if not self.project_root:
                QMessageBox.warning(self, "需要项目", "请先设置项目根目录。")
                return
            self.update_connection_status("正在连接...")
            self.connect_button.setEnabled(False)
            self.user_list_widget.clear()
            self.users.clear()
            if not self.network_listener.isRunning():
                self.network_listener.start()
            QTimer.singleShot(1000, self._check_connection_started) # Check status after delay
        else:
            self.update_connection_status("正在断开连接...")
            self.connect_button.setEnabled(False)
            if self.network_listener.isRunning():
                self.network_listener.stop()
            QTimer.singleShot(500, self._check_connection_stopped) # Ensure UI updates after stop signal

    def _check_connection_started(self):
        """Callback to update button state after attempting connection."""
        if self.network_listener.isRunning():
            if not self.is_connected: # If status signal hasn't updated yet
                 self.is_connected = True
                 self.connect_button.setText("🔌 断开连接")
                 self.update_connection_status("连接成功 (等待监听...)") # Intermediate status
            self.connect_button.setEnabled(True)
        else: # Failed to start or stopped immediately
            self.is_connected = False
            self.connect_button.setText("🔌 连接")
            self.connect_button.setEnabled(True)
            if "错误" not in self.connection_status_label.text(): # Check label text
                 self.update_connection_status("连接失败")

    def _check_connection_stopped(self):
         """Callback to ensure UI reflects disconnected state."""
         if not self.network_listener.isRunning():
              self.is_connected = False
              self.connect_button.setText("🔌 连接")
              self.connect_button.setEnabled(True)
              self.user_list_widget.clear()
              self.users.clear()
              # Ensure status label reflects disconnection if signal didn't fire correctly
              if "已断开连接" not in self.connection_status_label.text():
                  self.update_connection_status("已断开连接")

    @Slot(str)
    def update_connection_status(self, status):
        """Updates the status label and connection state."""
        self.connection_status_label.setText(status)
        # Update internal state based on status message content
        if "正在监听" in status or "连接成功" in status: # Added "连接成功"
            if not self.is_connected:
                 self.is_connected = True
                 self.connect_button.setText("🔌 断开连接")
                 self.connect_button.setEnabled(True) # Ensure enabled
        elif "已断开连接" in status or "错误" in status or "失败" in status:
             if self.is_connected:
                 self.is_connected = False
                 self.connect_button.setText("🔌 连接")
                 self.connect_button.setEnabled(True) # Ensure enabled
                 self.user_list_widget.clear()
                 self.users.clear()

    # Removed select_project_root as button is removed

    def initialize_project_root(self, directory):
         """Sets up the application based on the selected project root."""
         # Clear previous state
         self.file_tree_model.clear()
         self.send_file_info_button.setEnabled(False)
         self.history_list_widget.clear() # Clear history list

         if directory and os.path.isdir(os.path.join(directory, "2.Project")):
             self.project_root = directory
             self.project_label.setText(f"项目: {os.path.basename(self.project_root)}") # Update label
             self.update_connection_status("项目已设置。")
             # Update file list label with current task (might be None initially)
             self.file_list_label.setText(f"文件 ({self.user_name} / {self.current_task or '未选任务'}):")
             self.update_file_tree_view() # Populate file tree using current task
             self.setup_log_file() # Setup log file
             self.load_history() # Load history from log file
             self.on_user_or_file_selected() # Re-evaluate button state
         else:
             self.project_root = None
             self.project_label.setText("项目: 未设置") # Update label
             self.update_connection_status("项目无效或未设置。")
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


    @Slot(str, str)
    def add_user(self, username, ip_address):
        """Adds a discovered user to the list if not already present."""
        if username != self.user_name and username not in self.users:
            self.users[username] = {'ip': ip_address, 'tcp_port': TCP_PORT}
            items = self.user_list_widget.findItems(username, Qt.MatchExactly)
            if not items:
                self.user_list_widget.addItem(username)
                print(f"Added user: {username} ({ip_address})")

    # --- ADDED: Slot for refresh button ---
    @Slot()
    def _refresh_user_list(self):
        """Clears the user list. Users will reappear on next discovery broadcast."""
        print("Refreshing user list...")
        self.users.clear()
        self.user_list_widget.clear()

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
        if not self.is_connected:
            self.show_message_box.emit("warning", "未连接", "请先连接网络。")
            return

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

        # Check if recipient is online before showing dialog
        if recipient_name not in self.users:
            self.show_message_box.emit("warning", "用户离线?", f"用户 '{recipient_name}' 当前不在线或已超时。\n请刷新用户列表或等待其重新连接。")
            return

        recipient_info = self.users.get(recipient_name)
        recipient_ip = recipient_info['ip']
        recipient_port = recipient_info.get('tcp_port', TCP_PORT)

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

            # Send in background thread
            thread = threading.Thread(target=self._send_tcp_message, args=(recipient_ip, recipient_port, file_info_data, recipient_name), daemon=True)
            thread.start()

            # Log locally (using the user's log format)
            self.log_file_info("Sent", recipient_name, file_info_data)
            self.update_connection_status(f"已发送文件信息 '{filename}' 给 {recipient_name}")
            self.load_history() # Refresh history list after logging
        else:
            QMessageBox.information(self, "提示", "发送已取消!")


    def _send_tcp_message(self, ip, port, data, recipient_name_log):
        """Worker function to send TCP message (file info) in a background thread."""
        print(f"DEBUG: Attempting to send to {ip}:{port} - Type: {data.get('type')}")
        success = False
        error_msg = ""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((ip, port))
            sock.sendall(json.dumps(data).encode('utf-8') + b'\n') # Add newline
            sock.close()
            print(f"DEBUG: Send successful to {ip}:{port}")
            success = True
        except socket.timeout:
            error_msg = f"连接用户 {recipient_name_log} 超时。"
            print(f"Timeout sending to {ip}:{port}")
        except ConnectionRefusedError:
            error_msg = f"用户 {recipient_name_log} 拒绝连接。"
            print(f"Connection refused by {ip}:{port}")
            # Remove user from list if connection refused
            QTimer.singleShot(0, lambda: self._remove_user(recipient_name_log))
        except Exception as e:
            error_msg = f"无法发送消息给 {recipient_name_log}: {e}"
            print(f"Error sending to {ip}:{port}: {e}")

        if not success and error_msg:
             self.show_message_box.emit("critical", "发送错误", error_msg)
        print(f"DEBUG: Send attempt finished. Success: {success}")

    @Slot(str)
    def _remove_user(self, username):
        """Removes a user from the internal dict and UI list."""
        print(f"Removing user '{username}' due to connection error.")
        if username in self.users:
            del self.users[username]
        items = self.user_list_widget.findItems(username, Qt.MatchExactly)
        for item in items:
            self.user_list_widget.takeItem(self.user_list_widget.row(item))


    @Slot(dict)
    def handle_incoming_file_info(self, file_info_data):
        """Handles received file information."""
        sender = file_info_data.get("sender")
        filename = file_info_data.get("filename")
        date_sent = file_info_data.get("date")
        source_path = file_info_data.get("full_source_path")
        notes = file_info_data.get("notes", "") # Get notes

        # Log reception (using the user's log format)
        # self.log_file_info("Received", sender, file_info_data)
        self.load_history() # Refresh history list after logging

        # Display info in a simple message box, including notes
        display_text = (
            f"收到来自 {sender} 的文件信息:\n\n"
            f"文件名: {filename}\n"
            f"发送日期: {date_sent}\n"
            f"源路径: {source_path}\n"
            f"备注: {notes}" # Display notes
        )
        print(f"Displaying received info: {display_text}") # Debug
        # Use signal to show message box safely
        self.show_message_box.emit("information", "收到文件信息", display_text)


    @Slot(str, str, str)
    def _show_message_box_slot(self, icon_type, title, text):
        """Slot to display QMessageBox from signals."""
        icon_map = { "warning": QMessageBox.Warning, "critical": QMessageBox.Critical, "information": QMessageBox.Information }
        # Make message box slightly wider
        msgBox = QMessageBox(self)
        msgBox.setIcon(icon_map.get(icon_type, QMessageBox.NoIcon))
        msgBox.setWindowTitle(title)
        msgBox.setText(text)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.setStyleSheet("QLabel{min-width: 400px;}") # Adjust min-width as needed
        msgBox.exec_()

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


    def stop_listener_thread(self):
         """Public method to ensure listener stops."""
         print("FileSenderWidget: stop_listener_thread called.")
         if self.network_listener.isRunning():
             self.network_listener.stop()


# # --- Example Usage (Standalone Test) ---
# if __name__ == '__main__':
#     class DummyGlobalVar:
#         user = "TestUser"
#         project = r"C:/temp/chat_test_project"
#         task = "Task01" # Add dummy task for testing
#
#     print("Running FileSenderWidget standalone for testing...")
#     test_gv = DummyGlobalVar()
#     test_user = test_gv.user
#     test_project_root = test_gv.project.replace('\\','/')
#     test_task = test_gv.task # Get task for init
#
#     dummy_project_2 = os.path.join(test_project_root, "2.Project")
#     dummy_user_a_geo = os.path.join(dummy_project_2, "TestUser", "Task01", "geo")
#     dummy_user_a_tex = os.path.join(dummy_project_2, "TestUser", "Task02", "tex")
#     os.makedirs(dummy_user_a_geo, exist_ok=True)
#     os.makedirs(dummy_user_a_tex, exist_ok=True)
#     with open(os.path.join(dummy_user_a_geo, "model_v01.ma"), "w") as f: f.write("dummy geo")
#     with open(os.path.join(dummy_user_a_tex, "diffuse.tx"), "w") as f: f.write("dummy tex")
#     print(f"Created dummy structure in: {test_project_root}")
#
#     app = QApplication(sys.argv)
#     main_win = QtWidgets.QMainWindow()
#     main_win.setWindowTitle("File Sender Test Container")
#     main_win.setGeometry(50, 50, 700, 600) # Smaller window for simpler UI
#     # Pass the initial task to the widget constructor
#     sender_widget = FileSenderWidget(user_name=test_user, project_root=test_project_root, current_task=test_task)
#     main_win.setCentralWidget(sender_widget)
#
#     # Example of how parent might update task
#     def update_task_later():
#          print("\n--- Simulating task update from parent ---")
#          new_task = "Task02"
#          # Call the specific method to update the task
#          sender_widget.set_current_task(new_task)
#
#     QTimer.singleShot(5000, update_task_later) # Simulate task change after 5 seconds
#
#
#     def close_app():
#          print("Test Container: Closing.")
#          sender_widget.stop_listener_thread()
#          app.quit()
#     main_win.closeEvent = lambda event: close_app()
#
#     main_win.show()
#     sys.exit(app.exec_())
