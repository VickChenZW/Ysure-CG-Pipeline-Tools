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
from pathlib import Path

# 固定的用户列表
USERS = ["Neo", "Vick", "YL", "Jie", "K", "O"]

# 固定的路径
# BASE_PATH = r"Y:\02.CG_Project\2024.12.09_EssilorPipeline\2.Project"
FILEPATH = bpy.data.filepath
BASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(FILEPATH)))


def export(name,path,in_path,des,user):
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
        'from': os.path.dirname(os.path.dirname(FILEPATH)).split("\\")[-1],
        'to': user,
        'make': FILEPATH.replace('\\','/'),
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
                    p["date"]=str(datetime.datetime.now())
                    p["make"]=FILEPATH.replace('\\','/')
                    p["describe"]=des
                updated_projects.append(p)
            f.seek(0)
            json.dump(updated_projects, f, ensure_ascii=False, indent=4)
        else:
            project.append(dic)
            f.seek(0)
            json.dump(project, f, ensure_ascii=False, indent=4)
    f.close()
    return exist
    #
    # print(path)

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
def update_project_names(self, context):
    props = context.scene.export_properties
    user = props.users
    user_folder = os.path.join(BASE_PATH, user)

    if os.path.exists(user_folder):
        project_names = os.listdir(user_folder)
    else:
        project_names = []
        print(f"User folder does not exist: {user_folder}")  # 调试打印

    enum_items = []
    count = 0
    for n in project_names:
        identifier = n
        name = n
        description = ""
        number = count
        enum_items.append((identifier,name,description,number))
        count += 1
    return enum_items



# 定义属性组用于存储下拉框选项
class ExportProperties(bpy.types.PropertyGroup):



    users: bpy.props.EnumProperty(
        name="用户",
        items=[(user, user, "") for user in USERS],
        default=USERS[1],
        update=update_project_names
    )

    project_names_enum: bpy.props.EnumProperty(
        name="项目名字",
        items=update_project_names,
        default=None,
        # update=lambda self, context: None  # 空更新函数，防止默认值问题
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

# 定义操作符用于导出物体
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

    def invoke(self, context, event):
        # 设置文件名输入框的默认值为当前选中物体的名字
        if context.object:
            self.file_name = context.object.name

        # 弹出一个对话框，用户可以在其中输入文件名和描述信息
        return context.window_manager.invoke_props_dialog(self,width=400)

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
        output_dir = os.path.join(BASE_PATH, user, project_name,'__IN__')
        info_dir = os.path.join(output_dir,"metadata",'in.json')
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
            # self.report({'INFO'},filepath)


            # 导出物体
            if file_format == 'FBX':
                bpy.ops.export_scene.fbx(filepath=filepath, use_selection=True, check_existing=True)
            elif file_format == 'OBJ':
                bpy.ops.export_scene.obj(filepath=filepath, use_selection=True)
            elif file_format == 'GLTF':
                bpy.ops.export_scene.gltf(filepath=filepath, export_format='GLTF_SEPARATE', use_selection=True)

            self.report({'INFO'}, f"已导出: {filename},存在{exist}")



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
        user = os.path.dirname(os.path.dirname(FILEPATH)).split("\\")[-1]
        project_name = props.project_names_enum
        output_dir = os.path.join(BASE_PATH, user, project_name, '__IN__')
        info_dir = os.path.join(output_dir, "metadata", 'in.json')
        old_name = FILEPATH.split("\\")[-1].split(".")[0]
        old_version = int(old_name.split("_")[-1].split("v")[-1])
        new_version = old_version+1
        work_path = os.path.dirname(FILEPATH).replace("\\","/")
        name = old_name.split("_")[0]
        new_name = old_name.split("v")[0]+"v"+str(new_version).zfill(3)+".blend"

        update(work_path,user,name,des)
        # 获取当前文件名
        # bpy.ops.wm.save_as_mainfile(file)
        bpy.ops.wm.save_as_mainfile(filepath=work_path + "/" + new_name, copy=False)
        self.report({'INFO'},'更新成功')
        return {'FINISHED'}
# 定义面板
class OBJECT_PT_export_panel(bpy.types.Panel):
    bl_label = "Ysure流程工具"
    bl_idname = "OBJECT_PT_export_panel"
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

        # 动态显示项目名字

        row = layout.row()
        row.prop(props, "project_names_enum")  # 直接使用 EnumProperty

        layout.prop(props, "file_formats")

        layout.operator("object.export_selected", text="导出")


# 注册类
classes = (
    ExportProperties,
    OBJECT_OT_export_selected,
    OBJECT_OT_update_version_operator,
    OBJECT_PT_export_panel
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