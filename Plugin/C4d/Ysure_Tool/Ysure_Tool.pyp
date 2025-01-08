import c4d, os, json, shutil, maxon, redshift
from datetime import datetime
import re

PLUGIN_ID = 8555151
PLUGIN_NAME = "Ysure_Tool"
PLUGIN_PATH = os.path.dirname(__file__)
_user = ["Neo", "Vick", "YL", "Jie", "K", "O"]
_format = ['obj', 'fbx', 'abc', 'rs', 'usd']
task = []
pattern = r"^(.*?)(?:_v\d{3}\.\w+)$"


def upgrade_selected_project():
    if c4d.gui.MessageDialog("是否版本更新", c4d.GEMB_YESNO) == c4d.GEMB_R_V_YES:
        name = c4d.documents.GetActiveDocument().GetDocumentName()
        # content_name = name.split("_")[0]
        content_name = re.match(pattern, name).group(1)
        project_path = c4d.documents.GetActiveDocument().GetDocumentPath()
        current_file = project_path
        data_file = current_file + "\metadata\project.json"
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
                new_name = content_name + "_v" + str(new_version).zfill(3) + '.c4d'
                new_notes = c4d.gui.InputDialog("输入备注", latest_project['notes'])
                new_project = {
                    'content': content_name,
                    'version': new_version,
                    'user': latest_project['user'],
                    'dcc': latest_project['dcc'],
                    'path': (current_file + "/" + new_name).replace("\\", "/"),
                    'notes': new_notes
                }
                projects.append(new_project)
                file.seek(0)
                json.dump(projects, file, ensure_ascii=False, indent=4)
                c4d.CallCommand(202539)
                c4d.gui.MessageDialog("版本更新完成！", 0)


def get_task_list(user):
    project_path = c4d.documents.GetActiveDocument().GetDocumentPath()
    root_path = os.path.dirname(os.path.dirname(project_path))
    user_task_path = os.path.join(root_path, user).replace("\\", "/")
    print(user_task_path)
    if os.path.exists(user_task_path):
        return os.listdir(user_task_path)
    else:
        return None


class ExportFile(object):
    def __init__(self, user, task):
        self.user = user
        self.task = task
        self.dic = {
            'file_name': "",
            'date': "",
            'from': "",
            'to': "",
            'make': "",
            'describe': "",
        }
        self.doc = c4d.documents.GetActiveDocument()
        self.project_path = self.doc.GetDocumentPath()
        self.in_path = os.path.join(os.path.dirname(os.path.dirname(self.project_path)), self.user, self.task, "__IN__")

    def export(self, f, ani, cam, mat, tex):

        FBX_id = 1026370
        Obj_id = 1030178
        ABC_id = 1028082
        USD_id = 1055179
        RS_id = 1038650
        id = [1030178, 1026370, 1028082, 1038650, 1055179]
        format = [".obj", ".fbx", ".abc", ".rs", ".usd"]
        # if user is not None and task is not None and f is not None:

        print(os.path.dirname(os.path.dirname(self.project_path)))
        # current_name = c4d.documents.GetActiveDocument().GetActiveObject().GetName()
        name = c4d.gui.InputDialog("输入名字")
        des = c4d.gui.InputDialog("输入备注")

        path = os.path.join(self.in_path, name + format[f])

        plug = c4d.plugins.FindPlugin(id[f], c4d.PLUGINTYPE_SCENESAVER)
        if plug is None:
            raise RuntimeError("Failed to retrieve the exporter")

        data = dict()
        # Sends MSG_RETRIEVEPRIVATEDATA to fbx export plugin
        if not plug.Message(c4d.MSG_RETRIEVEPRIVATEDATA, data):
            raise RuntimeError("Failed to retrieves private data.")

        # BaseList2D object stored in "imexporter" key hold the settings

        Export = data.get("imexporter", None)
        if Export is None:
            raise RuntimeError("Failed to retrieves BaseContainer private data.")
        # FBX
        if f == 1:
            Export[c4d.FBXEXPORT_ASCII] = True
            Export[c4d.FBXEXPORT_SELECTION_ONLY] = True
            Export[c4d.FBXEXPORT_CAMERAS] = cam
            Export[c4d.FBXEXPORT_GRP_ANIMATION] = ani
            Export[c4d.FBXEXPORT_MATERIALS] = mat
            Export[c4d.FBXEXPORT_EMBED_TEXTURES] = False
            Export[c4d.FBXEXPORT_SUBSTANCES] = False
            Export[c4d.FBXEXPORT_BAKE_MATERIALS] = False

        if f == 2:

            Export[c4d.ABCEXPORT_CAMERAS] = cam
            Export[c4d.ABCEXPORT_SELECTION_ONLY] = True
            if ani == 1:
                Export[c4d.ABCEXPORT_FRAME_START] = int(
                    c4d.documents.GetActiveDocument().GetMinTime().Get() * c4d.documents.GetActiveDocument().GetFps())
                Export[c4d.ABCEXPORT_FRAME_END] = int(
                    c4d.documents.GetActiveDocument().GetMaxTime().Get() * c4d.documents.GetActiveDocument().GetFps())
            else:
                current_time = Export[c4d.ABCEXPORT_FRAME_START] = int(
                    c4d.documents.GetActiveDocument().GetTime().Get() * c4d.documents.GetActiveDocument().GetFps())
                Export[c4d.ABCEXPORT_FRAME_START] = current_time
                Export[c4d.ABCEXPORT_FRAME_END] = current_time
        # doc = c4d.documents.GetActiveDocument()

        if not c4d.documents.SaveDocument(self.doc, path,
                                          c4d.SAVEDOCUMENTFLAGS_EXPORTDIALOG | c4d.SAVEDOCUMENTFLAGS_DONTADDTORECENTLIST,
                                          id[f]):
            raise RuntimeError("Failed to save the document.")

        else:

            if tex:
                export_tex = Local_Tex()
                export_tex.get_select_tex()
                export_tex.copy_to_uesr(self.user, self.task)

            self.dic = {
                'file_name': f'{name}{format[f]}',
                'date': str(datetime.now()),
                'from': os.path.dirname(self.project_path).split("\\")[-1],
                'to': self.user,
                'make': (self.project_path + c4d.documents.GetActiveDocument().GetDocumentName()).replace("\\", "/"),
                'describe': des,
            }

            if not os.path.exists(os.path.join(self.in_path, "metadata")):
                os.makedirs(os.path.join(self.in_path, "metadata"))

            if not os.path.exists(os.path.join(self.in_path, "metadata", "in.json")):
                with open(os.path.join(self.in_path, "metadata", "in.json"), "w", encoding='utf-8') as file:
                    json.dump([], file, ensure_ascii=False, indent=4)

            with open(os.path.join(self.in_path, "metadata", "in.json"), "r+", encoding='utf-8') as file:
                project = json.load(file)
                new_project = []
                for i in project:
                    if i['file_name'] == f'{name}{format[f]}':
                        pass
                    else:
                        new_project.append(i)
                new_project.append(self.dic)
                file.seek(0)
                file.truncate()
                json.dump(new_project, file, ensure_ascii=False, indent=4)
            file.close()
        c4d.gui.MessageDialog("导出完成!", 0)
        c4d.EventAdd()

        # print (path)

    def export_c4d(self):
        des = c4d.gui.InputDialog("输入备注")
        self.dic = {
            'file_name': self.doc.GetDocumentName(),
            'date': str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'from': os.path.dirname(self.doc.GetDocumentPath()).split("\\")[-1],
            'to': self.user,
            'make': (self.doc.GetDocumentPath() + "/"+self.doc.GetDocumentName()).replace("\\", "/"),
            'describe': des
        }
        if not os.path.exists(os.path.join(self.in_path, "metadata")):
            os.makedirs(os.path.join(self.in_path, "metadata"))

        if not os.path.exists(os.path.join(self.in_path, "metadata", "proj.json")):
            with open(os.path.join(self.in_path, "metadata", "proj.json"), "w", encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)

        with open(os.path.join(self.in_path, "metadata", "proj.json"), "r+", encoding='utf-8') as f:
            project = json.load(f)
            project.append(self.dic)
            f.seek(0)
            json.dump(project, f, ensure_ascii=False, indent=4)
        f.close()
        c4d.gui.MessageDialog("导出完成!", 0)
        c4d.EventAdd()


class Local_Tex(object):

    def __init__(self):
        self.doc = c4d.documents.GetActiveDocument()
        self.list = []
        self.root = self.doc.GetDocumentPath()
        self.no_local = []
        self.renderData = self.doc.GetActiveRenderData()
        self.rendertype = self.renderData[c4d.RDATA_RENDERENGINE]
        self.fix_tex = []
        self.existed_tex = []
        self.selected_tex = []

    def get_all_no_local_tex(self):
        c4d.documents.GetAllAssetsNew(self.doc, False, "",
                                      c4d.ASSETDATA_FLAG_NODOCUMENT | c4d.ASSETDATA_FLAG_MULTIPLEUSE | c4d.ASSETDATA_FLAG_TEXTURESONLY,
                                      self.list)
        for i in self.list:
            # print(i)
            if os.path.join(self.root, "tex") in os.path.dirname(i["filename"]):
                pass
            else:
                self.no_local.append(i)
                # print(i)

    def get_select_tex(self):
        self.get_all_no_local_tex()
        select = c4d.documents.GetActiveDocument().GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)
        for s in select:
            # print(s)
            object: c4d.BaseObject = s
            tags = object.GetTags()
            # print(tags)
            for n in self.list:
                if n['owner'] == s:
                    self.selected_tex.append(n)
            for t in tags:
                if t.GetType() == 5616:  ##材质标签
                    textag: c4d.TextureTag = t
                    owner = textag.GetMaterial()
                    for n in self.list:
                        if n['owner'] == owner:
                            self.selected_tex.append(n)
            # print(self.selected_tex)

    def copy_to_local(self):
        for n in self.no_local:
            source = n["filename"]
            name = source.split("\\")[-1]
            owner_name = n['owner'].GetName()
            if n["owner"].GetType() == 5703 or n["owner"].GetType() == 1001101:
                des = os.path.join(self.root, "tex", owner_name, name)
                if not os.path.exists(os.path.join(self.root, "tex", owner_name)):
                    os.makedirs(os.path.join(self.root, "tex", owner_name))
            else:
                des = os.path.join(self.root, "tex", name)

            if not os.path.exists(des):
                shutil.copy(source, des)
            else:
                self.existed_tex.append(name)

    def copy_to_uesr(self, user, task):
        project_path = c4d.documents.GetActiveDocument().GetDocumentPath()
        for n in self.selected_tex:
            source = n["filename"]
            name = source.split("\\")[-1]
            owner_name = n['owner'].GetName()

            tex_path = os.path.join(os.path.dirname(os.path.dirname(project_path)), user, task, "tex")
            des = os.path.join(tex_path, owner_name, name)
            # print(des)
            # des = os.path.join(self.root,"tex",owner_name,name)
            if not os.path.exists(os.path.join(tex_path, owner_name)):
                print(self.root, "tex", owner_name)
                os.makedirs(os.path.join(tex_path, owner_name))
            if not os.path.exists(des):
                shutil.copy(source, des)
            else:
                self.existed_tex.append(name)
        c4d.gui.MessageDialog(
            f'一共导出{len(self.selected_tex)}个贴图\n 已有{len(self.existed_tex)}贴图存在')

    def rename_tex(self):
        for i in self.no_local:
            baseList2D = i["owner"]
            owner_name = baseList2D.GetName()
            name = i["filename"].split("\\")[-1]
            new_name = f'{owner_name}/{name}'
            print(baseList2D.GetType())
            if baseList2D.GetType() == 1001101:  # RS texture GetType() != GetRealType()
                baseList2D[c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0, c4d.REDSHIFT_FILE_PATH] = new_name
            elif baseList2D.GetType() == 1036751:  # RS Light GetType() != GetRealType()

                if baseList2D[c4d.REDSHIFT_LIGHT_TYPE] == 4:  # Dome
                    baseList2D[c4d.REDSHIFT_LIGHT_DOME_TEX0, c4d.REDSHIFT_FILE_PATH] = name
                elif baseList2D[c4d.REDSHIFT_LIGHT_TYPE] == 5:  # IES
                    baseList2D[c4d.REDSHIFT_LIGHT_IES_PROFILE, c4d.REDSHIFT_FILE_PATH] = name
                else:  # area/point
                    baseList2D[c4d.REDSHIFT_LIGHT_PHYSICAL_TEXTURE, c4d.REDSHIFT_FILE_PATH] = name
            elif baseList2D.GetType() == 5703:  # New_Node_System
                nodespace = i["nodeSpace"]
                nodepath = i['nodePath']
                nodeMaterial: c4d.NodeMaterial = baseList2D.GetNodeMaterialReference()
                graph: maxon.GraphModelInterface = nodeMaterial.GetGraph(nodespace)
                with graph.BeginTransaction() as t:
                    node = graph.GetNode(maxon.NodePath(nodepath))
                    pathPort = node.GetInputs().FindChild(
                        "com.redshift3d.redshift4c4d.nodes.core.texturesampler.tex0").FindChild("path")
                    pathPort.SetDefaultValue(new_name)
                    t.Commit()
            elif baseList2D().GetType() == 5833:  ##
                id = i['paramId']
                baseList2D[id] = name
            self.fix_tex.append(name)
        c4d.gui.MessageDialog(
            f'一共{len(self.list)}个贴图\n共本地化{len(self.fix_tex)}个贴图!\n 处理的贴图已有{len(self.existed_tex)}贴图存在')

    def run(self):
        if c4d.gui.MessageDialog("是否本地化资产", c4d.GEMB_YESNO) == c4d.GEMB_R_V_YES:
            self.get_all_no_local_tex()
            self.copy_to_local()
            self.rename_tex()
            c4d.EventAdd()
        else:
            pass


class Flipbook(object):
    def __init__(self):
        self.doc = c4d.documents.GetActiveDocument()
        self.rd = self.doc.GetActiveRenderData().GetClone().GetData()
        self.project_path = c4d.documents.GetActiveDocument().GetDocumentPath()

        self.project_name = self.doc.GetDocumentName()
        self.content_name = re.match(pattern, self.project_name).group(1)
        self.flipbook_path = os.path.join(self.project_path, "flipbook", self.content_name)

    def create_sub_folder(self):
        if not os.path.exists(self.flipbook_path):
            os.makedirs(self.flipbook_path)

    def renderFlipbook(self):
        file = os.path.join(self.flipbook_path,
                            os.path.splitext(self.project_name)[0] + "_" + datetime.now().strftime('%Y-%m-%d %H-%M-%S'))
        # print(file)
        if c4d.gui.MessageDialog("是否确定拍屏", c4d.GEMB_YESNO) == c4d.GEMB_R_V_YES:
            x = c4d.gui.InputDialog("输入分辨率", "1920")
            self.rd.SetInt32(c4d.RDATA_FRAMESEQUENCE, c4d.RDATA_FRAMESEQUENCE_ALLFRAMES)
            self.rd.SetLong(c4d.RDATA_RENDERENGINE, c4d.RDATA_RENDERENGINE_PREVIEWHARDWARE)
            # self.rd.SetBool(c4d.RDATA_TEXTURES, True)
            self.rd.SetBool(c4d.RDATA_GLOBALSAVE, True)
            self.rd.SetBool(c4d.RDATA_SAVEIMAGE, True)
            self.rd.SetBool(c4d.RDATA_ALPHACHANNEL, False)
            # self.rd.SetBool(c4d.RDATA_OPTION_REFLECTION,True)
            self.rd.SetInt32(c4d.RDATA_FORMATDEPTH, c4d.RDATA_FORMATDEPTH_8)
            self.rd.SetInt32(c4d.RDATA_FORMAT, 1125)
            self.rd.SetFilename(c4d.RDATA_PATH, file)
            self.rd.SetInt32(c4d.RDATA_XRES, int(x))
            y = int(x) / self.rd.GetReal(c4d.RDATA_FILMASPECT)
            self.rd.SetInt32(c4d.RDATA_YRES, int(y))
            bmp = c4d.bitmaps.MultipassBitmap(int(self.rd[c4d.RDATA_XRES]), int(self.rd[c4d.RDATA_YRES]),
                                              c4d.COLORMODE_RGB)
            if c4d.documents.RenderDocument(self.doc, self.rd, bmp, c4d.RENDERFLAGS_EXTERNAL) != c4d.RENDERRESULT_OK:
                raise RuntimeError("Failed to render the temporary document.")
            else:
                c4d.gui.MessageDialog(f"导出成功\n{file}")
            c4d.EventAdd()
        else:
            pass


class ChangeRenderPath(object):
    def __init__(self, name, is_mul: str, take: bool):
        self.name = name
        self.is_mul = is_mul
        self.take = take
        self._pattern = r"^(.*?)(?:_v\d{3}\.\w+)$"
        self.doc = c4d.documents.GetActiveDocument()
        self.render_date = self.doc.GetActiveRenderData()

        self.change_render_path()
        # self.change_aov_path(self.is_mul)

    def change_render_path(self):
        # self.doc = c4d.documents.GetActiveDocument()
        render_path = os.path.join(self.doc.GetDocumentPath(), "render")
        list = os.listdir(render_path)
        project_name = self.doc.GetDocumentName()
        content_name = re.match(self._pattern, project_name).group(1)
        version = 1
        if c4d.gui.MessageDialog("是否迭代渲染文件", c4d.GEMB_YESNO) == c4d.GEMB_R_V_YES:
            up = True
        else:
            up = False
        for i in list:
            if not "metadata" in i:
                parts = i.split("_")[1:-2]
                name_part = "_".join(parts)
                # print(name_part)
                ver_part = int(i.split("_")[-1].split('v')[-1])
                if name_part == content_name and ver_part >= version:
                    if up:
                        version = ver_part + 1
                    else:
                        version = ver_part
        ver_str = str(version).zfill(3)

        if self.name.endswith("_") or self.name.endswith("."):
            pass
        else:
            self.name += "_"
        if self.take:
            self.render_date[c4d.RDATA_PATH] = f'render/$YYYY$MM$DD_$prj_.take_v{ver_str}/$take/{self.name}$take_'
        else:
            self.render_date[c4d.RDATA_PATH] = f'render/$YYYY$MM$DD_$prj_v{ver_str}/{self.name}'

        self.doc.SetActiveRenderData(self.render_date)

        ## 更改RS的AOV
        vprs = redshift.FindAddVideoPost(self.render_date, redshift.VPrsrenderer)
        print(vprs)
        print(dir(vprs))
        print(vprs.GetParameter(c4d.RDATA_MULTIPASS_SAVEONEFILE, 0))
        aovs = redshift.RendererGetAOVs(vprs)
        if self.is_mul:
            print("True")
            vprs[c4d.REDSHIFT_RENDERER_AOV_MULTIPART] = True
            vprs[c4d.REDSHIFT_RENDERER_AOV_PATH] = 'AOV/$prj_$take_AOV_'
            for aov in aovs:
                aov.SetParameter(c4d.REDSHIFT_AOV_FILE_PATH, '$filepath$pass/$pass_')
        else:
            vprs[c4d.REDSHIFT_RENDERER_AOV_MULTIPART] = False
            vprs[c4d.REDSHIFT_RENDERER_AOV_PATH] = '$prj_AOV'
            for aov in aovs:
                aov.SetParameter(c4d.REDSHIFT_AOV_FILE_PATH, '$filepath$filename_$pass/$pass_')
        # aovs = redshift.RendererGetAOVs(vprs)

        redshift.RendererSetAOVs(vprs, aovs)
        c4d.EventAdd()
        c4d.gui.MessageDialog("设置完成")


class GUI(c4d.gui.GeDialog):
    def __init__(self):
        super().__init__()

    def CreateLayout(self):
        self.SetTitle("test")

        if self.GroupBegin(0, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 0, 0, '导出给别人', 0, 0, 0):
            self.GroupBorderSpace(20, 20, 20, 20)
            self.GroupSpace(10, 10)
            if self.TabGroupBegin(1, c4d.BFH_SCALEFIT | c4d.BFV_TOP, c4d.TAB_TABS):
                if self.GroupBegin(10, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 2, 3, '版本更新', 0, 0, 0):
                    self.AddButton(100, c4d.BFH_LEFT, 0, 0, "版本更新")
                    self.AddButton(102, c4d.BFH_LEFT, 0, 0, "本地化资产")
                self.GroupEnd()
                if self.GroupBegin(11, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 1, 5, '导出给别人', 0, 0, 0):
                    if self.GroupBegin(14, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 2, 5, '导出给别人', 0, 0, 0):
                        self.AddStaticText(11, c4d.BFH_LEFT, 0, 0, '选择用户', 0)
                        self.AddComboBox(1000, c4d.BFH_LEFT, 80, 10, False, False)
                        index = 10001
                        for user in _user:
                            self.AddChild(1000, index, user)
                            index += 1

                        self.AddStaticText(11, c4d.BFH_LEFT, 0, 0, '选择工程', 0)
                        self.AddComboBox(1002, c4d.BFH_LEFT, 80, 10, False, False)


                        self.AddStaticText(11, c4d.BFH_LEFT, 0, 0, '选择格式', 0)
                        self.AddComboBox(1001, c4d.BFH_LEFT, 80, 10, False, False)
                        index = 20001
                        for format in _format:
                            self.AddChild(1001, index, format)
                            index += 1


                    self.GroupEnd()
                    if self.GroupBegin(13, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 5, 5, 'test', 0, 0, 0):
                        self.AddCheckbox(2006, c4d.BFH_LEFT, 0, 0, "发送C4d")
                        self.AddCheckbox(2000, c4d.BFH_LEFT, 0, 0, "动画")
                        self.AddCheckbox(2001, c4d.BFH_LEFT, 0, 0, "摄影机")
                        self.AddCheckbox(2002, c4d.BFH_LEFT, 0, 0, "材质")
                        self.AddCheckbox(2003, c4d.BFH_LEFT, 0, 0, "贴图")
                        self.AddButton(101, c4d.BFH_CENTER, 0, 0, "导出选择物体给他人")
                    self.GroupEnd()
                self.GroupEnd()
                if self.GroupBegin(12, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 4, 3, '渲染', 0, 0, 0):
                    self.AddButton(103, c4d.BFH_CENTER, 0, 0, "更改渲染保存路径")
                    self.AddEditText(105, c4d.BFH_CENTER, 150, 0, 0)
                    self.SetString(105, "$prj_")
                    self.AddCheckbox(2004, c4d.BFH_RIGHT, 0, 0, "多层AOV")
                    self.AddCheckbox(2005, c4d.BFH_RIGHT, 0, 0, "多场次")
                    self.AddButton(104, c4d.BFH_CENTER, 0, 0, "拍屏")

                self.GroupEnd()
            self.GroupEnd()
        self.GroupEnd()

    def Command(self, id, msg):
        global tasks
        if id == 100:
            name = self.GetInt32(1000)
            # print()
            upgrade_selected_project()
            # load()

        if id == 1000:

            self.AddChild(1002, 30001, "test")
            self.FreeChildren(1002)
            user = _user[self.GetInt32(1000) - 10001]
            # get_task_list(user)
            if get_task_list(user):
                index = 30001
                tasks = []
                for task in get_task_list(user):
                    self.AddChild(1002, index, task)
                    tasks.append(task)
                    index += 1
            print("change")

        if id == 2006:
            prj = self.GetBool(2006)
            if prj:
                for i in [1001, 2000, 2001, 2002, 2003]:
                    self.Enable(i, False)
                print("1")
            else:
                for i in [1001, 2000, 2001, 2002, 2003]:
                    self.Enable(i, True)
                print("0")

        if id == 101:
            name = self.GetInt32(1000)
            user = _user[name - 10001]
            f = self.GetInt32(1001) - 20001
            t = self.GetInt32(1002) - 30001
            # format = _format[f-20001]
            ani = self.GetBool(2000)
            cam = self.GetBool(2001)
            mat = self.GetBool(2002)
            tex = self.GetBool(2003)

            prj = self.GetBool(2006)

            if all((user, tasks[t], f)):
                export = ExportFile(user, tasks[t])
                if prj:
                    export.export_c4d()
                else:
                    export.export(f, ani, cam, mat, tex)

            else:
                c4d.gui.MessageDialog("none", 0)
        if id == 102:
            lt = Local_Tex()
            lt.run()

        if id == 103:
            crp = ChangeRenderPath(self.GetString(105), self.GetBool(2004), self.GetBool(2005))
            # print(self.GetBool(2004))

        if id == 104:
            fb = Flipbook()
            fb.renderFlipbook()

        return True


class Command(c4d.plugins.CommandData):
    def __init__(self):
        self.dialog = None

    def Execute(self, doc):
        if self.dialog == None:
            self.dialog = GUI()

        self.dialog.Open(c4d.DLG_TYPE_ASYNC, PLUGIN_ID, xpos=- 1, ypos=- 1, defaultw=400, defaulth=400, subid=0)

        return True


if __name__ == "__main__":
    icon = c4d.bitmaps.BaseBitmap()
    icon_path = os.path.join(PLUGIN_PATH, "icon", "Y.png")
    icon.InitWith(icon_path)
    c4d.plugins.RegisterCommandPlugin(PLUGIN_ID, PLUGIN_NAME, 0, icon, "Display a basic GUI", Command())
