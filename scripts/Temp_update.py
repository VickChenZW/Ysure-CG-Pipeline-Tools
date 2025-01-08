from PySide2.QtWidgets import (QMainWindow, QLineEdit,
                               QWidget, QVBoxLayout, QLabel,
                               QPushButton, QHBoxLayout, QApplication,
                               QProgressBar)
from PySide2.QtCore import Signal, QObject, QSize, QThread
import os, configparser

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_dir =r"Y:\07.Personal\Vick\7.Develop\Pipeline\Ysure-CG-Pipeline-Tools"


# 定义文件复制线程类
class CopyFilesThread(QThread):
    progress_updated = Signal(int)  # 用于更新进度条的信号
    finished = Signal()  # 用于通知复制完成的信号
    canceled = Signal()  # 用于通知复制被取消的信号

    def __init__(self, src_dir, dst_dir):
        super().__init__()
        self.src_dir = src_dir  # 源文件夹列表
        self.dst_dir = dst_dir  # 目标文件夹
        self.cancel_flag = False  # 取消标志

    def run(self):
        total_size = self.calculate_total_size()
        print(total_size)
        if not total_size:
            self.canceled.emit()
            print("error")
            return

        copied_size = 0

        for root, dirs, files in os.walk(self.src_dir):
            # 创建目标文件夹
            relative_path = os.path.relpath(root, self.src_dir)
            dest_path = os.path.join(self.dst_dir, relative_path)
            # print(dest_path)
            os.makedirs(dest_path, exist_ok=True)
            print(dirs)
            dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('_') and not d == 'config']
            for file in files:
                # 跳过隐藏文件（如果选中了不复制隐藏文件）
                if not file.startswith('.') and not file.startswith("__"):
                    # print(file)
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(dest_path, file)
                    # print(src_file)
                    # print(dst_file)

                    # 检查目标文件是否存在
                    if os.path.exists(dst_file):
                        try:
                            os.remove(dst_file)
                        except Exception as e:
                            print(f"无法删除文件 {dst_file}: {e}")
                            continue

                    # 复制文件并更新进度
                    try:
                        with open(src_file, 'rb') as fsrc, open(dst_file, 'wb') as fdst:
                            while True:
                                buffer = fsrc.read(1024 * 8)  # 每次读取 8KB
                                if not buffer:
                                    break
                                fdst.write(buffer)
                                copied_size += len(buffer)
                                progress = int((copied_size / total_size) * 100)
                                self.progress_updated.emit(progress)
                    except Exception as e:
                        print(f"无法复制文件 {src_file} 到 {dst_file}: {e}")
                        continue

        self.finished.emit()

    def calculate_total_size(self):
        """计算所有文件的总大小"""
        total_size = 0
        for root, dirs, files in os.walk(self.src_dir):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
        return total_size

    def cancel(self):
        """设置取消标志"""
        self.cancel_flag = True

class CheckUpdate(QWidget):
    update_signal = Signal(str)

    def __init__(self):
        super().__init__()


        self.have_update = False
        self.version = ""
        self.update_data = ""
        self.notes = ""

        self.btn_ok = QPushButton("更新")
        self.btn_ok.clicked.connect(self.update_app)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(lambda :self.close())

        self.progress_bar = QProgressBar()

        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        label = QLabel("有新的版本!!")
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)

        layout.addWidget(label)
        layout.addLayout(btn_layout)
        layout.addWidget(self.progress_bar)
        self.setWindowTitle("版本更新")
        self.setLayout(layout)
        self.setFixedSize(QSize(300, 150))

        self.copy_thread = None
        self.source_dirs = root_dir
        self.destination_dir = base_dir




    def create_ui(self):


        self.show()


    def get_ini(self):
        config = configparser.ConfigParser()
        path = os.path.join(base_dir, "../config", "version.ini")
        if os.path.exists(path):
            config.read(path)

        self.version = config.get("Version", "version")
        self.update_data = config.get("Version", "update_data")
        self.notes = config.get("Version", "update_notes")


    def check_update(self):
        config = configparser.ConfigParser()
        path = os.path.join(root_dir, "config", "version.ini")
        if os.path.exists(path):
            config.read(path)
        if config.get("Version", "version") != self.version or config.get("Version", "update_data") != self.update_data:
            self.create_ui()
            return True
        else:
            return False

    def update_app(self):
        self.update_signal.emit("close")
        self.btn_ok.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.start_copy()

    def start_copy(self):
        """开始复制文件"""

        # 创建并启动复制线程
        self.copy_thread = CopyFilesThread(
            self.source_dirs,
            self.destination_dir
        )
        print("start")
        self.copy_thread.progress_updated.connect(self.update_progress)
        self.copy_thread.finished.connect(self.copy_finished)
        self.copy_thread.start()


    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)

    def copy_finished(self):
        """复制完成后的处理"""
        self.btn_ok.setEnabled(True)  # 重新启用开始复制按钮
        self.btn_cancel.setEnabled(True)  # 禁用取消按钮
        self.progress_bar.setValue(100)
        self.btn_ok.clicked.connect(self.restart)
        self.btn_ok.setText("重启")
        # self.update_signal.emit("finish")
        # os.startfile(os.path.join(base_dir,'run.bat'))


    def restart(self):
        os.startfile(os.path.join(base_dir,'run.bat'))
        self.close()






