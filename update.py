import sys
import os
import json
import hashlib
import shutil
from pathlib import Path
from PySide2.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QProgressBar, QLabel, QWidget
from PySide2.QtCore import Qt, QThread, Signal


class UpdateThread(QThread):
    """后台更新线程"""
    progress_updated = Signal(int)
    update_finished = Signal(bool)

    def __init__(self, source_file, target_file):
        super().__init__()
        self.source_file = source_file
        self.target_file = target_file

    def run(self):
        try:
            # 复制文件并显示进度
            with open(self.source_file, 'rb') as src, open(self.target_file, 'wb') as dst:
                file_size = os.path.getsize(self.source_file)
                copied_size = 0
                chunk_size = 8192
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    dst.write(chunk)
                    copied_size += len(chunk)
                    progress = int((copied_size / file_size) * 100)
                    self.progress_updated.emit(progress)

            self.update_finished.emit(True)
        except Exception as e:
            print(f"更新失败: {e}")
            self.update_finished.emit(False)


class MainWindow(QMainWindow):
    def __init__(self, source_json, target_json):
        super().__init__()
        self.source_json = source_json
        self.target_json = target_json
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("项目更新检查")
        self.setGeometry(100, 100, 400, 200)

        central_widget = QWidget()
        layout = QVBoxLayout()

        self.label = QLabel("点击按钮检查更新", self)
        layout.addWidget(self.label)

        self.check_button = QPushButton("检查更新", self)
        self.check_button.clicked.connect(self.check_for_updates)
        layout.addWidget(self.check_button)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def check_for_updates(self):
        # 检查 JSON 文件是否更新
        if self.is_json_updated():
            self.label.setText("发现更新，正在关闭界面...")
            self.close()  # 关闭主窗口
            self.start_update_process()  # 启动更新进程
        else:
            self.label.setText("没有新更新。")

    def is_json_updated(self):
        """检查 JSON 文件是否更新"""
        if not os.path.exists(self.target_json):
            return True  # 如果目标文件不存在，则认为有更新

        # 通过比较文件的 MD5 哈希值来判断是否有更新
        source_hash = self.calculate_md5(self.source_json)
        target_hash = self.calculate_md5(self.target_json)

        return source_hash != target_hash

    def calculate_md5(self, file_path):
        """计算文件的 MD5 哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def start_update_process(self):
        """启动后台更新进程"""
        self.update_thread = UpdateThread(self.source_json, self.target_json)
        self.update_thread.progress_updated.connect(self.update_progress_bar)
        self.update_thread.update_finished.connect(self.on_update_finished)
        self.update_thread.start()

    def update_progress_bar(self, progress):
        """更新进度条"""
        self.progress_bar.setValue(progress)

    def on_update_finished(self, success):
        """更新完成后处理"""
        if success:
            print("更新成功！")
        else:
            print("更新失败。")

        # 重新打开主窗口
        self.show()
        self.label.setText("更新完成。")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 定义源 JSON 文件和目标 JSON 文件路径
    source_json = Path("Y:/YourProjectFolder/config.json")  # 公用盘下的 JSON 文件路径
    target_json = Path(os.getcwd()) / "config.json"  # 当前工作目录中的 JSON 文件路径

    window = MainWindow(source_json, target_json)
    window.show()

    sys.exit(app.exec_())