import json
import os
import sys
from PySide2.QtWidgets import (
    QMainWindow, QApplication,
    QLabel,  QHBoxLayout,
    QVBoxLayout, QWidget, QTabWidget, QPushButton,
    QFileDialog, QLineEdit, QTextEdit, QListWidget,QListWidgetItem,
    QTableWidget, QTableWidgetItem, QDialog, QDialogButtonBox, QMessageBox,
    QStackedLayout,QComboBox, QMenuBar, QMenu,QToolBar,QAction, QStatusBar

)
from PySide2.QtCore import QSize, Qt, QRectF, QPoint
from PySide2.QtGui import (QFont, QDropEvent, QEnterEvent,
                           QDragLeaveEvent, QIcon, QPixmap,
                           QDragEnterEvent,QMouseEvent, QPainter, QColor,
                           QPen, QPainterPath, QRegion)
import Function
import qdarktheme
from Work_Project import Work_Project
from Project_Manage import project_manager
from file_exchange import File_Exchange
from Render_List import render_list
import Global_Vars
from Global_Vars import gv
class Drag_Function(QLabel):
    def __init__(self,parent):
        super(Drag_Function,self).__init__(parent)
        self.setAcceptDrops(True)
        self.setText("拖动到此处")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet('''background : rgba(200,200,200,0.1);
                                                   color : #747474;''')


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
        self.setStyleSheet('''background : rgba(200,200,200,0.1);
                                                   color : #747474;''')
        self.setText("拖动到此处")
        self.setCursor(Qt.OpenHandCursor)

    def dropEvent(self, event:QDropEvent) -> None:
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if "smb" in text or "Volumes" in  text:
                Function.mac_2_win(text)
            else:
                Function.win_2_mac(text)

            self.setStyleSheet('''background : rgba(200,200,200,0.1);
                                           color : #747474;''')
            self.setText("拖动到此处")

class desktop_widget(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(QSize(150,150))
        self.label = Drag_Function(self)
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





if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = desktop_widget()
    win.show()
    app.exec_()