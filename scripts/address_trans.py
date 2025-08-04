from PySide2.QtWidgets import (
    QMainWindow, QLabel, QHBoxLayout,
    QVBoxLayout, QWidget, QPushButton

)
from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import (QFont, QDropEvent, QDragLeaveEvent, QDragEnterEvent, QMouseEvent)
from scripts import Function


class Drag_Function(QLabel):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setText("拖动到此处")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet('''background : rgba(200,200,200,0.1); color : #747474;''')


    def dragEnterEvent(self, event:QDragEnterEvent) -> None:
        if event.mimeData().hasText():
            event.acceptProposedAction()
            text = event.mimeData().text()
            if "smb" in text or "Volumes" in  text:
                self.setStyleSheet('''background : rgba(10,200,10,0.5)''')
                self.setText("松开打开文件目录")
                self.setCursor(Qt.ClosedHandCursor)
            else:
                self.setStyleSheet('''background : rgba(10,200,80,0.5)''')
                self.setText("松开拷贝Mac文件目录")


    def dragLeaveEvent(self, event:QDragLeaveEvent) -> None:
        self.setStyleSheet('''background : rgba(200,200,200,0.1); color : #747474;''')
        self.setText("拖动到此处")
        self.setCursor(Qt.OpenHandCursor)

    def dropEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if "smb" in text or "Volumes" in text:
                Function.mac_2_win(text)
            else:
                Function.win_2_mac(text)

            self.setStyleSheet('''background : rgba(200,200,200,0.1); color : #747474;''')
            self.setText("拖动到此处")

class desktop_widget(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(QSize(50, 50))
        self.label = Drag_Function()
        # layout = QVBoxLayout()
        # layout.addWidget(self.label)
        self.setCentralWidget(self.label)

        self.draggable = True
        self.mousePressPos = None
        self.mouseMovePos = None
    def mousePressEvent(self, event:QMouseEvent):
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton and self.draggable:
            self.mousePressPos = event.globalPos()  # 全局坐标
            self.mouseMovePos = event.globalPos()   # 全局坐标
            event.accept()
            self.setCursor(Qt.ClosedHandCursor)
            # print(self.mouseMovePos)# 改变鼠标指针为闭合的手型

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        if event.buttons() == Qt.LeftButton and self.draggable:
            # 计算鼠标移动的距离
            current_pos = event.globalPos()
            diff = current_pos -self.mouseMovePos
            new_pos = self.pos() + diff
            # print(new_pos)

            # # 移动窗口到新的位置
            self.move(new_pos)
            self.mouseMovePos = current_pos
            event.accept()

    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.draggable:
            self.mousePressPos = None
            self.mouseMovePos = None
            event.accept()
            self.setCursor(Qt.ArrowCursor)  # 恢复默认鼠标指针

class ClipBoard_Function(QWidget):
    def __init__(self):
        super().__init__()

        self.win = desktop_widget()

        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()

        btn_M2W = QPushButton("Mac-->Windows")
        btn_M2W.pressed.connect(self.get_Win_Address)
        btn_W2M = QPushButton("Windows-->Mac")
        btn_W2M.pressed.connect(self.get_Mac_Address)
        self.widget = QPushButton("显示小组件")
        self.widget.clicked.connect(self.show_widget)
        btn_W2M.setMinimumHeight(50)
        btn_M2W.setMinimumHeight(50)
        self.widget.setMinimumHeight(50)
        self.widget.setCheckable(True)


        drag_lab = Drag_Function()
        font = QFont("Microsoft YaHei UI", 30)
        font.setBold(True)
        # drag_lab.setStyleSheet('''background : rgba(200,200,200,0.5);
        #                        color : #747474;''')
        drag_lab.setAlignment(Qt.AlignCenter)
        drag_lab.setFont(font)


        btn_layout.addWidget(btn_M2W)
        btn_layout.addWidget(btn_W2M)
        btn_layout.addWidget(self.widget)


        layout.addLayout(btn_layout)
        layout.addWidget(drag_lab)

        self.setLayout(layout)

    def debug(self):
        print("test")

    def get_Win_Address(self):
        Function.mac_2_win(Function.get_from_clipboard())

    def get_Mac_Address(self):
        Function.win_2_mac(Function.get_from_clipboard())

    def show_widget(self,checked):
        if checked:
            self.win.show()
        else:
            self.win.hide()
            # self.win = None

    def close_widget(self):
        if not self.win == None:
            self.win.close()


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     win = desktop_widget()
#     win.show()
#     app.exec_()