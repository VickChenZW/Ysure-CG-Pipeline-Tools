import sys
import os
import hou
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *

base_dir = os.path.dirname(os.path.abspath(__file__))


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
        self.refresh_btn.setIcon(QIcon(os.path.join(base_dir,"icon","refresh.ico")))
        self.refresh_btn.pressed.connect(self.refresh_all)
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
        selected_dir = hou.ui.selectFile(
            file_type=hou.fileType.Directory,
            start_directory=self.folder_path
        )
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
        columns = 6
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

        if found_path:
            selected_node = hou.selectedNodes()
            if selected_node and selected_node[0].type().name() == 'rslightdome::2.0':
                selected_node[0].parm('env_map').set(found_path)
        else:
            print(f"未找到对应的HDR文件: {base_name}")

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

class MegascansWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.megascans_path = r'D:\source\Megascans Library'
        self.surface_list = ['Albedo', 'AO', 'Displacement', 'Normal', 'Roughness']
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        path_layout = QHBoxLayout()
        type_layout = QHBoxLayout()

        self.path_line_edit = QLineEdit()
        self.path_line_edit.setText(self.megascans_path)
        path_layout.addWidget(self.path_line_edit)

        self.browse_btn = QPushButton('选择目录')
        self.browse_btn.clicked.connect(self.browse_directory)
        path_layout.addWidget(self.browse_btn)



        self.surface_btn = QPushButton('Surface')
        self.surface_btn.pressed.connect(lambda t='surface': self.load_image(t))
        type_layout.addWidget(self.surface_btn)

        self.model_btn = QPushButton('Model')
        self.model_btn.pressed.connect(lambda t='3d': self.load_image(t))
        type_layout.addWidget(self.model_btn)

        self.model_btn = QPushButton('Plant')
        self.model_btn.pressed.connect(lambda t='3dplant': self.load_image(t))
        type_layout.addWidget(self.model_btn)

        layout.addLayout(path_layout)
        layout.addLayout(type_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        self.grid_widget = QWidget()
        self.scroll_area.setWidget(self.grid_widget)
        self.grid_layout = QGridLayout()
        self.grid_widget.setLayout(self.grid_layout)

        self.setLayout(layout)

    def browse_directory(self):
        selected_dir = hou.ui.selectFile(
            file_type=hou.fileType.Directory,
            start_directory=self.folder_path
        )
        if selected_dir:
            self.folder_path = selected_dir
            self.path_line_edit.setText(self.folder_path)
            self.update_combo()

    def traverse_images(self, target_path):
        self.image_files = []
        self.source_files = []
        for i in os.scandir(target_path):
            for n in os.scandir(i.path):
                if n.name == "previews":
                    for t in os.scandir(n.path):
                        self.image_files.append(t.path)
                        self.source_files.append(os.path.dirname(os.path.dirname(t.path)))
                        break
        # print(self.image_files)

    def load_image(self, t):
        m_path = self.megascans_path
        target_path = os.path.join(m_path, 'Downloaded', t)

        self.clear_layout(self.grid_layout)
        self.traverse_images(target_path)

        if not self.image_files:
            return

        self.image_loader = ImageLoader(self.image_files)
        self.image_loader.imagesLoaded.connect(lambda image, tt=t: self.display_images(image, tt))
        self.image_loader.start()

    def display_images(self, images, t):
        columns = 6
        self.grid_layout.setVerticalSpacing(10)
        self.grid_layout.setHorizontalSpacing(10)

        for col in range(columns):
            self.grid_layout.setColumnStretch(col, 1)

        for idx, pixmap in enumerate(images):
            label = SourceLabel(pixmap, self.source_files[idx])
            label.setToolTip(os.path.basename(self.image_files[idx]))
            label.setAlignment(Qt.AlignCenter)
            label.mouseDoubleClickEvent = lambda event, i=idx, tt=t: self.hou_process(i, tt)

            row = idx // columns
            col = idx % columns
            self.grid_layout.addWidget(label, row, col)

        rows_needed = (len(images) + columns - 1) // columns
        if rows_needed <= 0:
            rows_needed = 1

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.grid_layout.addItem(spacer, rows_needed, 0, 1, columns)


    def hou_process(self,index,t):
        if t == 'surface':
            self.make_mat(index, None)
        elif t == '3d':
            self.add_model(index)
            # self.make_mat(index)
        elif t == '3dplant':
            self.add_plant(index)

    def add_model(self, index):
        path = self.source_files[index]
        fullname = os.path.basename(path)
        node: hou.Node = hou.node('/obj/')
        asset_node = node.createNode('Vick::assetimport', fullname)
        # set_mat_node.parm('num_materials').set(10)
        for i in os.scandir(path):
            if i.name.endswith('LOD0.fbx'):
                asset_node.parm('file').set(i.path)
                asset_node.parm('format').set('0')
        self.make_mat(index, asset_node)

        geo = asset_node.node('Get_Mat').geometry()
        if geo:
            uni_mats = geo.findGlobalAttrib('mats')
            mats = geo.stringListAttribValue(uni_mats)
        else:
            mats = []

        if len(mats) > 1:
            asset_node.parm('mat_folder').set(len(mats))
        else:
            asset_node.parm('mat_folder').set(1)
            asset_node.parm('group1').set('*')
            asset_node.parm('shop1').set(f'{asset_node.path()}/Mat/{fullname}_Mat')

    def add_plant(self, index):
        path = self.source_files[index]
        fullname = os.path.basename(path)
        node: hou.Node = hou.node('/obj/')
        asset_node = node.createNode('Vick::assetimport', fullname)
        asset_node.parm('format').set('3')
        asset_node.parm('setoutside').set(0)
        custom_node: hou.Node = asset_node.node('custom_input')
        objmerge_node: hou.Node = custom_node.createNode('object_merge')
        objmerge_node.parm('pack').set(1)
        var = 0
        for i in os.scandir(path):
            if i.name.startswith('Var'):
                objmerge_node.parm('numobj').set(var+1)
                for n in os.scandir(i.path):
                    if n.name.endswith('LOD0.fbx'):
                        # 处理单个var
                        file_node: hou.Node = custom_node.createNode('file',)
                        file_node.parm('file').set(n.path)

                        # 处理位移
                        trans_node = custom_node.createNode('xform', 'transform')
                        trans_node.setInput(0, file_node)
                        trans_node.parm('scale').set('0.01')

                        # 删除属性
                        attr_del_node = custom_node.createNode('attribdelete')
                        attr_del_node.setInput(0, trans_node)
                        attr_del_node.parm('ptdel').set('fbx_*')
                        attr_del_node.parm('vtxdel').set('Cd')

                        # 增加材质
                        set_mat_node = custom_node.createNode('material')
                        set_mat_node.setInput(0, attr_del_node)
                        set_mat_node.parm('shop_materialpath1').set(asset_node.node('Mat').path()+'/'+fullname+'_Mat')
                        set_mat_node.parm('group1').set('*')
                        # 增加空节点
                        null_node = custom_node.createNode('null',i.name)
                        null_node.setInput(0, set_mat_node)

                        # 增加到objmerge
                        objmerge_node.parm(f'objpath{var+1}').set(null_node.path())
                        break
                var += 1

        #连接到output
        output_node: hou.Node = custom_node.node('output0')
        output_node.setInput(0, objmerge_node)
        self.make_mat(index, asset_node)

        geo = asset_node.node('Get_Mat').geometry()
        if geo:
            uni_mats = geo.findGlobalAttrib('mats')
            mats = geo.stringListAttribValue(uni_mats)
        else:
            mats = []

        if len(mats) > 1:
            asset_node.parm('mat_folder').set(len(mats))
        else:
            asset_node.parm('mat_folder').set(1)
            asset_node.parm('group1').set('*')
            asset_node.parm('shop1').set(f'{asset_node.path()}/Mat/{fullname}_Mat')

    def make_mat(self, index, node):
        path = self.source_files[index]

        fullname = os.path.basename(path)
        name = fullname.split("_")[-1]
        if os.path.exists(os.path.join(path, 'Textures')):
            path = os.path.join(path, 'Textures', 'Atlas')
        if node:
            mat_node = node.node('Mat')
        else:
            mat_node = hou.node('/mat')
        rs_node: hou.Node = mat_node.createNode("redshift_vopnet", f"{fullname}_Mat")
        rs_standard_material_node = hou.node(rs_node.path() + "/StandardMaterial1")

        # 定义优先级顺序
        preferred_extensions = ['.exr', '.png', '.jpg']

        for i in self.surface_list:
            # 创建纹理节点
            tex_node: hou.Node = rs_node.createNode("redshift::TextureSampler", i)

            # 根据材质类型连接到标准材质节点
            if i == 'Albedo':
                rs_standard_material_node.setInput(0, tex_node)
            elif i == 'Roughness':
                rs_standard_material_node.setInput(6, tex_node)
                tex_node.parm('tex0_colorSpace').set('Raw')
            elif i == 'Normal':
                # 创建BumpMap节点并连接
                bump_node: hou.Node = rs_node.createNode("redshift::BumpMap", "Normal_Map")
                bump_node.parm('inputType').set('1')
                out_node = hou.node(rs_node.path() + "/redshift_material1")
                out_node.setInput(2, bump_node)
                bump_node.setInput(0, tex_node)
                tex_node.parm('tex0_colorSpace').set('Raw')

            elif i == 'Opacity':
                sprite_node: hou.Node = rs_node.createNode('redshift::Sprite', 'Opacity')
                out_node = hou.node(rs_node.path() + "/redshift_material1")
                out_node.setInput(0, sprite_node)
                sprite_node.setInput(0, rs_standard_material_node)
                # sprite_node.parm('tex0').set()

            # 寻找符合条件的纹理文件（按优先级顺序）
            selected_file = None
            files = []
            for entry in os.scandir(path):
                if i in entry.name:  # 确保文件名包含当前材质类型（如Albedo）
                    files.append(entry)

            # 按优先级排序文件
            files.sort(key=lambda x:
            preferred_extensions.index(os.path.splitext(x.name)[1])
            if os.path.splitext(x.name)[1] in preferred_extensions
            else float('inf'))

            if files:
                selected_file = files[0].path  # 选择第一个符合条件的文件
                print(f"Selected {i} texture: {selected_file}")
            else:
                print(f"Warning: No {i} texture found in {path}")

            # 设置纹理路径
            if selected_file:
                tex_node.parm('tex0').set(selected_file)
            else:
                # 可选：处理未找到的情况（如提示或默认值）
                pass




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
        self.tab_widget.addTab(MegascansWidget(),"Megascans")
        self.layout.addWidget(self.tab_widget)
        self.setLayout(self.layout)

#######
