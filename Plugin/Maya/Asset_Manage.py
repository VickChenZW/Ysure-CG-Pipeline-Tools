import sys
import os
import maya.cmds as cmds
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *

base_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), '../../..'))


class ImageLabel(QLabel):
    # doubleClicked = Signal(str)

    def __init__(self, pixmap: QPixmap, path: str):
        super().__init__()
        self.setPixmap(pixmap)
        self.path = path
        self.setMouseTracking(True)
        self.setStyleSheet("QLabel { background: transparent; }")
        self.hovered = False

    def enterEvent(self, event):
        self.setStyleSheet("QLabel { border: 2px solid yellow; }")
        self.hovered = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("QLabel { background: transparent; }")
        self.hovered = False
        super().leaveEvent(event)

    # def mousePressEvent(self, event):
    #     if event.button() == Qt.LeftButton and self.hdr_path:
    #         drag = QDrag(self)
    #         mime_data = QMimeData()
    #         mime_data.setText(self.hdr_path)
    #         drag.setMimeData(mime_data)
    #         drag.setPixmap(self.pixmap())
    #         drag.exec_(Qt.CopyAction)
    #     super().mousePressEvent(event)
    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        if ev.buttons() == Qt.LeftButton and self.path:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self.path)
            drag.setMimeData(mime)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec_(Qt.MoveAction)

    # def mouseDoubleClickEvent(self, event):
    #     self.doubleClicked.emit(self.hdr_path)
    #     super().mouseDoubleClickEvent(event)


class ImageLoader(QThread):
    imagesLoaded = Signal(list)

    def __init__(self, image_files):
        super().__init__()
        self.image_files = image_files

    def run(self):
        images = []
        for file_path in self.image_files:
            pixmap = QPixmap(file_path).scaled(200, 200, Qt.KeepAspectRatio, Qt.FastTransformation)
            images.append(pixmap)
        self.imagesLoaded.emit(images)


class ImageGridWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.folder_path = r'Y:\07.Personal\Vick\5.Source\HDRI'
        self.image_files = []
        self.hdr_paths = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("HDRI管理器")
        self.setGeometry(100, 100, 1200, 800)

        path_layout = QHBoxLayout()
        combo_layout = QHBoxLayout()
        layout = QVBoxLayout(self)

        self.path_line_edit = QLineEdit()
        self.path_line_edit.setText(self.folder_path)
        self.path_line_edit.textChanged.connect(self.update_folder_path)
        path_layout.addWidget(self.path_line_edit)

        self.browse_btn = QPushButton('选择目录')
        self.browse_btn.clicked.connect(self.browse_directory)
        path_layout.addWidget(self.browse_btn)

        self.path_combo = QComboBox()
        self.path_combo.currentIndexChanged.connect(self.load_images)
        # self.path_combo.setMinimumWidth(800)
        combo_layout.addWidget(self.path_combo)

        self.refresh_btn = QPushButton()
        self.refresh_btn.setMaximumWidth(50)
        self.refresh_btn.pressed.connect(self.refresh_all)
        self.refresh_btn.setIcon(QIcon(os.path.join(base_dir,"icon","refresh.ico")))
        combo_layout.addWidget(self.refresh_btn)

        layout.addLayout(path_layout)
        layout.addLayout(combo_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        self.grid_widget = QWidget()
        self.scroll_area.setWidget(self.grid_widget)
        self.grid_layout = QGridLayout()
        self.grid_widget.setLayout(self.grid_layout)

        # self.update_combo()

    def browse_directory(self):
        selected_dir = cmds.fileDialog2(fileMode=3, startingDirectory=self.folder_path)
        print(selected_dir)
        if selected_dir:
            self.folder_path = selected_dir
            self.path_line_edit.setText(self.folder_path)
            self.update_combo()

    def update_folder_path(self):
        new_path = self.path_line_edit.text()
        if os.path.exists(new_path):
            self.folder_path = new_path
            self.update_combo()

    def update_combo(self):
        self.path_combo.clear()
        for entry in os.scandir(self.folder_path):
            if entry.is_dir():
                self.path_combo.addItem(entry.name)

    def refresh_all(self):
        self.update_combo()
        self.load_images()

    def traverse_images(self, target_path):
        self.image_files = []
        self.hdr_paths = []
        thumb_dir = os.path.join(target_path, '.Thumbnails')
        if not os.path.exists(thumb_dir):
            return
        for file_name in os.listdir(thumb_dir):
            if file_name.lower().endswith(('.jpg', '.png', '.exr', '.hdr')):
                thumb_path = os.path.join(thumb_dir, file_name)
                self.image_files.append(thumb_path)

                # 查找HDR路径
                base_name = os.path.splitext(file_name)[0]
                target_hdr_dir = os.path.join(target_path, 'HDRIs')
                found_path = None

                # 优先查找原名
                for ext in ['.exr', '.hdr']:
                    path = os.path.join(target_hdr_dir, f"{base_name}{ext}")
                    if os.path.exists(path):
                        found_path = path
                        break

                # 如果未找到，尝试带_sm后缀
                if not found_path:
                    for ext in ['.exr', '.hdr']:
                        path = os.path.join(target_hdr_dir, f"{base_name}_sm{ext}")
                        if os.path.exists(path):
                            found_path = path
                            break

                self.hdr_paths.append(found_path)  # 即使未找到也添加None

    def load_images(self):
        selected_dir = self.path_combo.currentText()
        target_path = os.path.join(self.folder_path, selected_dir)

        self.clear_layout(self.grid_layout)
        self.traverse_images(target_path)

        if not self.image_files:
            return

        self.image_loader = ImageLoader(self.image_files)
        self.image_loader.imagesLoaded.connect(self.display_images)
        self.image_loader.start()

    def display_images(self, images):
        columns = 4
        self.grid_layout.setVerticalSpacing(10)
        self.grid_layout.setHorizontalSpacing(10)

        for col in range(columns):
            self.grid_layout.setColumnStretch(col, 1)

        for idx, pixmap in enumerate(images):
            label = ImageLabel(pixmap, self.hdr_paths[idx])
            label.setToolTip(os.path.basename(self.image_files[idx]))
            label.setAlignment(Qt.AlignCenter)

            label.mouseDoubleClickEvent = lambda event, i=idx: self.open_image(i)

            row = idx // columns
            col = idx % columns
            self.grid_layout.addWidget(label, row, col)

        rows_needed = (len(images) + columns - 1) // columns
        if rows_needed <= 0:
            rows_needed = 1

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.grid_layout.addItem(spacer, rows_needed, 0, 1, columns)

    def traverse_images(self, target_path):
        self.image_files = []
        self.hdr_paths = []
        thumb_dir = os.path.join(target_path, '.Thumbnails')
        if not os.path.exists(thumb_dir):
            return
        for file_name in os.listdir(thumb_dir):
            if file_name.lower().endswith(('.jpg', '.png', '.exr', '.hdr')):
                thumb_path = os.path.join(thumb_dir, file_name)
                self.image_files.append(thumb_path)

                # 查找HDR路径
                base_name = os.path.splitext(file_name)[0]
                target_hdr_dir = os.path.join(target_path, 'HDRIs')
                found_path = None

                # 优先查找原名
                for ext in ['.exr', '.hdr']:
                    path = os.path.join(target_hdr_dir, f"{base_name}{ext}")
                    if os.path.exists(path):
                        found_path = path
                        break

                # 如果未找到，尝试带_sm后缀
                if not found_path:
                    for ext in ['.exr', '.hdr']:
                        path = os.path.join(target_hdr_dir, f"{base_name}_sm{ext}")
                        if os.path.exists(path):
                            found_path = path
                            break

                self.hdr_paths.append(found_path)  # 即使未找到也添加None

    def open_image(self, index):
        base_name = os.path.basename(self.image_files[index])
        target_dir = os.path.join(
            self.folder_path,
            self.path_combo.currentText(),
            'HDRIs'
        )

        base_name_no_ext = os.path.splitext(base_name)[0]
        found_path = None

        for ext in ['.exr', '.hdr']:
            temp_path = os.path.join(target_dir, f"{base_name_no_ext}{ext}")
            if os.path.exists(temp_path):
                found_path = temp_path
                break

        if not found_path:
            for ext in ['.exr', '.hdr']:
                temp_path = os.path.join(target_dir, f"{base_name_no_ext}_sm{ext}")
                if os.path.exists(temp_path):
                    found_path = temp_path
                    break

        # if found_path:
        #     selected_node = hou.selectedNodes()
        #     if selected_node and selected_node[0].type().name() == 'rslightdome::2.0':
        #         selected_node[0].parm('env_map').set(found_path)
        # else:
        #     print(f"未找到对应的HDR文件: {base_name}")

    def clear_layout(self, layout):
        if not layout:
            return

        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue

            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout:
                    self.clear_layout(sub_layout)
                else:
                    del item

class SourceLabel(QLabel):
    # doubleClicked = Signal(str)

    def __init__(self, pixmap: QPixmap, path: str):
        super().__init__()
        self.setPixmap(pixmap)
        self.path = path
        self.setMouseTracking(True)
        self.setStyleSheet("QLabel { background: transparent; }")
        self.hovered = False

    def enterEvent(self, event):
        self.setStyleSheet("QLabel { border: 2px solid yellow; }")
        self.hovered = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("QLabel { background: transparent; }")
        self.hovered = False
        super().leaveEvent(event)


    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        if ev.buttons() == Qt.LeftButton and self.path:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self.path)
            drag.setMimeData(mime)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec_(Qt.MoveAction)


class AssetManage(QWidget):
    def __init__(self):
        super().__init__()
        self.image_view = ImageGridWidget()
        self.layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.West)
        style_sheet = "QTabBar::tab { width: 20px; height: 100px; }"
        self.tab_widget.setStyleSheet(style_sheet)
        self.tab_widget.addTab(self.image_view, "HDRI")
        # self.tab_widget.addTab(MegascansWidget(),"Megascans")
        self.layout.addWidget(self.tab_widget)
        self.setLayout(self.layout)

#######
