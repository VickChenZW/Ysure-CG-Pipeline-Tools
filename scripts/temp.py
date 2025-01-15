from PySide2.QtWidgets import QApplication, QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QLabel
from PySide2.QtCore import Qt
import sys
import os

class DroppableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)  # 接受拖拽进入
        self.setSelectionMode(QListWidget.SingleSelection)

    def dragEnterEvent(self, event):
        # 只接受本地文件的拖拽
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):  # 确保是文件
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.UserRole, file_path)  # 存储完整路径作为用户数据
                self.addItem(item)
        event.acceptProposedAction()

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('拖拽文件到列表')
        layout = QVBoxLayout()
        label = QLabel("将文件从文件系统拖放到下方列表中")
        layout.addWidget(label)
        self.list_widget = DroppableListWidget()
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())