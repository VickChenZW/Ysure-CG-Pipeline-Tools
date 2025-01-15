# -*- coding: utf-8 -*-

bl_info = {
    "name": "YsureTool",
    "author": "Vick",
    "version": (0,1,0),
    "blender": (2, 83, 0),
    "category": "",
    "location": "",
    "description": "",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}


import bpy
import os
import json
import datetime
import re
from datetime import datetime

from pathlib import Path

# 固定的用户列表
USERS = ["Neo", "Vick", "YL", "Jie", "K", "O"]

# 固定的路径
# BASE_PATH = r"Y:\02.CG_Project\2024.12.09_EssilorPipeline\2.Project"
# FILEPATH = bpy.data.filepath
# BASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(FILEPATH)))


def export(name,path,in_path,des,user):
    file_path = bpy.data.filepath
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(file_path)))

    dic = {
        'file_name': "",
        'date': "",
        'from': "",
        'to': "",
        'make': "",
        'describe': "",
    }

    data = dict()

    dic = {
        'file_name': name,
        'date': str(datetime.datetime.now()),
        'from': os.path.dirname(os.path.dirname(file_path)).split("\\")[-1],
        'to': user,
        'make': file_path.replace('\\','/'),
        'describe': des,
    }


    with open(in_path.replace("\\","/"), "r+", encoding='utf-8') as f:
        project = json.load(f)
        exist = False
        for p in project:
            if p["file_name"]==name:
                exist = True
        if exist:
            updated_projects = []
            for p in project:
                if p["file_name"] == name:
                    p["date"] = str(datetime.datetime.now())
                    p["make"] = file_path.replace('\\','/')
                    p["describe"] = des
                updated_projects.append(p)
            f.seek(0)
            json.dump(updated_projects, f, ensure_ascii=False, indent=4)
        else:
            project.append(dic)
            f.seek(0)
            json.dump(project, f, ensure_ascii=False, indent=4)
    f.close()
    return exist

def update(current_file,user,content_name,des):
    # current_file = Global_Vars.Project + "/2.Project/" + Global_Vars.User + "/" + self.project_combo.currentText()
    data_file = current_file + "/metadata/project.json"
    # return (data_file)
    with open(data_file, 'r+', encoding='utf-8') as file:
        projects = json.load(file)
        latest_project = None

        for project in projects:
            if project['content'] == content_name and (
                    latest_project is None or project['version'] > latest_project['version']):
                latest_project = project

        if latest_project:
            new_version = latest_project['version'] + 1

            current_notes = latest_project['notes']
            old_path = latest_project['path']
            new_name = content_name + "_v" + str(new_version).zfill(3) + '.blend'
            new_notes = des
            new_project = {
                'content': content_name,
                'version': new_version,
                'user': user,
                'dcc': "Blender",
                'path': current_file + "/" + new_name,
                'notes': new_notes
            }
            projects.append(new_project)
            file.seek(0)
            json.dump(projects, file, ensure_ascii=False, indent=4)

def update_project_names(self,context):
    file_path = bpy.data.filepath
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(file_path)))
    props = context.scene.export_properties
    user = props.users
    user_folder = os.path.join(base_path, user)

    if os.path.exists(user_folder):
        project_names = os.listdir(user_folder)
    else:
        project_names = []

    global enum_items
    enum_items = []
    count = 0
    for n in os.listdir(user_folder):
        number = count
        enum_items.append((n,n,""))
        count += 1
    return (enum_items)


class OBJECT_OT_export_selected(bpy.types.Operator):
    bl_idname = "object.export_selected"
    bl_label = "导出选中物体"
    bl_options = {'REGISTER'}

    file_name: bpy.props.StringProperty(
        name="文件名",
        default="未命名",
        description="请输入文件名（不包括扩展名）"
    )

    # 定义描述输入框属性，使用 TEXTAREA 子类型创建多行文本框
    description: bpy.props.StringProperty(
        name="描述",
        default="",
        description="请输入描述信息"
    )

    def __init__(self):
        self.file_path = bpy.data.filepath
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(self.file_path)))

    def invoke(self, context, event):
        # 设置文件名输入框的默认值为当前选中物体的名字
        if context.object:
            self.file_name = context.object.name

        # 弹出一个对话框，用户可以在其中输入文件名和描述信息
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout

        # 文件名输入框
        box = layout.box()
        box.label(text="文件名")
        box.prop(self, "file_name", text="")

        # 描述输入框（多行文本框）
        box = layout.box()
        box.label(text="描述")
        box.prop(self, "description", text="")


    def execute(self, context):

        props = context.scene.export_properties
        user = props.users
        project_name = props.project_names_enum
        file_format = props.file_formats
        output_dir = os.path.join(self.base_path, user, project_name,'__IN__')
        info_dir = os.path.join(output_dir, "metadata", 'in.json')
        self.report({'INFO'},output_dir+file_format)
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            self.report({'INFO'},f'目录{output_dir}不存在')
        #
        # 获取选中的物体
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected_objects:
            self.report({'WARNING'}, "没有选中的物体")
            return {'CANCELLED'}

        for obj in selected_objects:
            # 设置文件名
            user_input = self.file_name.strip()
            filename = f"{user_input}.{file_format.lower()}"
            filepath = os.path.join(output_dir, filename)

            user_des = self.description.strip()
            exist = export(filename,filepath,info_dir,user_des,user)


            # 导出物体
            if file_format == 'FBX':
                bpy.ops.export_scene.fbx(filepath=filepath, use_selection=True, check_existing=True)
            elif file_format == 'OBJ':
                bpy.ops.export_scene.obj(filepath=filepath, use_selection=True)
            elif file_format == 'GLTF':
                bpy.ops.export_scene.gltf(filepath=filepath, export_format='GLTF_SEPARATE', use_selection=True)

            self.report({'INFO'}, f"已导出: {filename},存在{exist}")



        return {'FINISHED'}

class ChangeRenderPath(bpy.types.Operator):
    bl_idname = "render.change_render_path"
    bl_label = "修改渲染目录"
    bl_options = {'REGISTER'}

    render_name: bpy.props.StringProperty(
        name="渲染名",
        default="",
        description="请输入描述信息"
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
            layout = self.layout
            # 文件名输入框
            box = layout.box()
            box.label(text="渲染名")
            box.prop(self, "render_name", text="")

    def execute(self,context):
        file_path = bpy.data.filepath
        render_path = os.path.join(os.path.dirname(file_path), 'render')
        _pattern = r"^(.*?)(?:_v\d{3}\.\w+)$"
        render_name = self.render_name.strip()
        list = os.listdir(render_path)
        project_name = os.path.basename(file_path)
        project_name_without_pre = "".join(project_name.split('.')[0:-1])
        content_name = re.match(_pattern, project_name).group(1)
        version = 1
        for i in list:
            if not "metadata" in i:
                parts = i.split("_")[1:-2]
                name_part = "_".join(parts)
                # print(name_part)
                ver_part = int(i.split("_")[-1].split('v')[-1])
                if name_part == content_name and ver_part >= version:
                        version = ver_part + 1
        ver_str = str(version).zfill(3)
        path = os.path.join(render_path,f'{datetime.now().strftime("%Y%m%d")}_{project_name_without_pre}_{ver_str}',render_name+"_")
        bpy.context.scene.render.filepath = path

        return {'FINISHED'}


class OBJECT_OT_update_version_operator(bpy.types.Operator):
    bl_idname = "object.update_version"
    bl_label = "更新版本"
    bl_options = {'REGISTER', 'UNDO'}

    description: bpy.props.StringProperty(
        name="描述",
        default="",
        description="请输入版本更新的描述信息",
    )

    def __init__(self):
        self.file_path = bpy.data.filepath
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(self.file_path)))

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="描述")
        box.prop(self, "description", text="")

    def execute(self, context):
        props = context.scene.export_properties
        # user = props.users
        des = self.description.strip()
        user = os.path.dirname(os.path.dirname(self.file_path)).split("\\")[-1]
        project_name = props.project_names_enum
        output_dir = os.path.join(self.base_path, user, project_name, '__IN__')
        info_dir = os.path.join(output_dir, "metadata", 'in.json')
        old_name = self.file_path.split("\\")[-1].split(".")[0]
        old_version = int(old_name.split("_")[-1].split("v")[-1])
        new_version = old_version+1
        work_path = os.path.dirname(self.file_path).replace("\\","/")
        name = old_name.split("_")[0]
        new_name = old_name.split("v")[0]+"v"+str(new_version).zfill(3)+".blend"

        update(work_path, user, name, des)

        bpy.ops.wm.save_as_mainfile(filepath=work_path + "/" + new_name, copy=False)
        self.report({'INFO'},'更新成功')
        return {'FINISHED'}
# 定义属性组用于存储下拉框选项
class ExportProperties(bpy.types.PropertyGroup):

    users: bpy.props.EnumProperty(
        name="用户",
        items=[(user, user, "") for user in USERS],
        default=USERS[1],
        update=update_project_names,
    )

    project_names_enum: bpy.props.EnumProperty(
        name="项目名字",
        items=update_project_names,
        default=None,
    )

    file_formats: bpy.props.EnumProperty(
        name="三维格式",
        items=[
            ('FBX', "FBX", ""),
            ('OBJ', "OBJ", ""),
            ('GLTF', "glTF 2.0", ""),
        ],
        default='FBX'
    )


    output_directory: bpy.props.StringProperty(
        name="输出目录",
        subtype='DIR_PATH',
        default=""
    )

class Main(bpy.types.Panel):
    bl_label = "Ysure流程工具"
    bl_idname = "OBJECT_PT_YsuerPipeline_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ysure流程工具'


    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.export_properties
        layout.label(text="版本更新")
        layout.operator("object.update_version", text="更新版本")
        layout.label(text="导出选中物体")
        layout.prop(props, "users")
        layout.prop(props, "project_names_enum")  # 直接使用 EnumProperty
        layout.prop(props, "file_formats")
        layout.operator("object.export_selected", text="导出")
        layout.operator("render.change_render_path", text="更改渲染目录")


# 注册类
classes = (
    ExportProperties,
    OBJECT_OT_export_selected,
    OBJECT_OT_update_version_operator,
    ChangeRenderPath,
    Main
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.export_properties = bpy.props.PointerProperty(type=ExportProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.export_properties


if __name__ == "__main__":
    register()