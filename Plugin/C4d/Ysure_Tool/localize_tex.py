import c4d, redshift
import os,shutil, re

import maxon

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
        c4d.documents.GetAllAssetsNew(self.doc,False,"",c4d.ASSETDATA_FLAG_NODOCUMENT|c4d.ASSETDATA_FLAG_MULTIPLEUSE|c4d.ASSETDATA_FLAG_TEXTURESONLY,self.list)
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
            object:c4d.BaseObject = s
            tags = object.GetTags()
            # print(tags)
            for t in tags:
                if t.GetType() == 5616:      ##材质标签
                    textag:c4d.TextureTag = t
                    material = textag.GetMaterial()
                    self.get_all_no_local_tex()
                    for n in self.list:
                        if n['owner'] == material:
                            self.selected_tex.append(n)
            print(self.selected_tex)



    def copy_to_local(self):
        for n in self.no_local:
            source = n["filename"]
            name = source.split("\\")[-1]
            owner_name = n['owner'].GetName()
            des = os.path.join(self.root,"tex",owner_name,name)
            if not os.path.exists(os.path.join(self.root,"tex",owner_name)):
                os.makedirs(os.path.join(self.root,"tex",owner_name))
            if not os.path.exists(des):
                shutil.copy(source,des)
            else:
                self.existed_tex.append(name)

    def copy_to_uesr(self,user,task):
        project_path = c4d.documents.GetActiveDocument().GetDocumentPath()
        for n in self.selected_tex:
            source = n["filename"]
            name = source.split("\\")[-1]
            owner_name = n['owner'].GetName()

            tex_path = os.path.join(os.path.dirname(os.path.dirname(project_path)), user, task, "tex")
            des = os.path.join(tex_path,owner_name,name)
            # des = os.path.join(self.root,"tex",owner_name,name)
            if not os.path.exists(os.path.join(self.root,"tex",owner_name)):
                os.makedirs(os.path.join(self.root,"tex",owner_name))
            if not os.path.exists(des):
                shutil.copy(source,des)
            else:
                self.existed_tex.append(name)

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
                    baseList2D[c4d.REDSHIFT_LIGHT_DOME_TEX0, c4d.REDSHIFT_FILE_PATH] = new_name
                elif baseList2D[c4d.REDSHIFT_LIGHT_TYPE] == 5:  # IES
                    baseList2D[c4d.REDSHIFT_LIGHT_IES_PROFILE, c4d.REDSHIFT_FILE_PATH] = new_name
                else:  # area/point
                    baseList2D[c4d.REDSHIFT_LIGHT_PHYSICAL_TEXTURE, c4d.REDSHIFT_FILE_PATH] = new_name
            elif baseList2D.GetType() == 5703:  # New_Node_System
                nodespace = i["nodeSpace"]
                nodepath = i['nodePath']
                nodeMaterial:c4d.NodeMaterial = baseList2D.GetNodeMaterialReference()
                graph:maxon.GraphModelInterface = nodeMaterial.GetGraph(nodespace)
                with graph.BeginTransaction() as t:
                    node = graph.GetNode(maxon.NodePath(nodepath))
                    pathPort =node.GetInputs().FindChild("com.redshift3d.redshift4c4d.nodes.core.texturesampler.tex0").FindChild("path")
                    pathPort.SetDefaultValue(new_name)
                    t.Commit()
            elif baseList2D().GetType() == 5833: ##
                id = i['paramId']
                baseList2D[id] = name
            self.fix_tex.append(name)
        c4d.gui.MessageDialog(f'一共{len(self.list)}个贴图\n共本地化{len(self.fix_tex)}个贴图!\n 处理的贴图已有{len(self.existed_tex)}贴图存在')

class Flipbook(object):
    def __init__(self):
        self.doc = c4d.documents.GetActiveDocument()
        self.rd = self.doc.GetActiveRenderData().GetClone().GetData()
    def renderFlipbook(self):
        file = r"C:\Users\Victo\Videos\test.mp4"
        self.rd.SetInt32(c4d.RDATA_FRAMESEQUENCE, c4d.RDATA_FRAMESEQUENCE_ALLFRAMES)
        self.rd.SetLong(c4d.RDATA_RENDERENGINE, c4d.RDATA_RENDERENGINE_PREVIEWHARDWARE)
        self.rd.SetBool(c4d.RDATA_TEXTURES, True)
        self.rd.SetBool(c4d.RDATA_GLOBALSAVE, True)
        self.rd.SetBool(c4d.RDATA_SAVEIMAGE, True)
        self.rd.SetBool(c4d.RDATA_ALPHACHANNEL, False)
        self.rd.SetInt32(c4d.RDATA_FORMATDEPTH, c4d.RDATA_FORMATDEPTH_8)
        self.rd.SetInt32(c4d.RDATA_FORMAT, 1125)
        self.rd.SetFilename(c4d.RDATA_PATH, file)
        self.rd.SetInt32(c4d.RDATA_XRES,1920)
        self.rd.SetInt32(c4d.RDATA_YRES, 1080)
        bmp = c4d.bitmaps.MultipassBitmap(int(self.rd[c4d.RDATA_XRES]), int(self.rd[c4d.RDATA_YRES]), c4d.COLORMODE_RGB)
        c4d.documents.RenderDocument(self.doc,self.rd, bmp ,c4d.RENDERFLAGS_PREVIEWRENDER|c4d.RENDERFLAGS_EXTERNAL)


class ChangeRenderPath():
    def __init__(self):
        self._pattern = r"^(.*?)(?:_v\d{3}\.\w+)$"
        self.doc = c4d.documents.GetActiveDocument()
        self.render_date = self.doc.GetActiveRenderData()

    def change_render_path(self):
        # self.doc = c4d.documents.GetActiveDocument()
        render_path = os.path.join(self.doc.GetDocumentPath(),"render")
        list = os.listdir(render_path)
        project_name = self.doc.GetDocumentName()
        content_name = re.match(self._pattern,project_name).group(1)
        version = 1
        for i in list:
            if not "metadata" in i:
                parts = i.split("_")[1:-2]
                name_part = "_".join(parts)
                print(name_part)
                ver_part = int(i.split("_")[-1].split('v')[-1])
                if name_part ==content_name and ver_part>=version:
                    version = ver_part+1
        ver_str = str(version).zfill(3)


        self.render_date[c4d.RDATA_PATH]=f'render/$YYYY$MM$DD_$prj_v{ver_str}/$prj_'
        self.doc.SetActiveRenderData(self.render_date)
        # print(render_date[c4d.RDATA_PATH])
        c4d.gui.MessageDialog("设置完成，请自行更改文件输出名字")

    def change_aov_path(self,is_mutil):
        if is_mutil:
            self.render_date[c4d.RDATA_MULTIPASS_SAVEONEFILE] = True
            self.render_date[c4d.RDATA_MULTIPASS_FILENAME] = 'AOV/$prj_$take_AOV_'
        else:
            self.render_date[c4d.RDATA_MULTIPASS_SAVEONEFILE] = False
            self.render_date[c4d.RDATA_MULTIPASS_FILENAME] = '$prj_AOV'


        ## 更改RS的AOV
        vprs = redshift.FindAddVideoPost(self.render_date, redshift.VPrsrenderer)
        aovs = redshift.RendererGetAOVs(vprs)
        for aov in aovs:
            aov.SetParameter(c4d.REDSHIFT_AOV_FILE_PATH, '$filepath$filename_$pass/$pass_')
            print(aov.GetParameter(c4d.REDSHIFT_AOV_FILE_PATH))
        redshift.RendererSetAOVs(vprs, aovs)



if __name__ == "__main__":
    fb = ChangeRenderPath()
    fb.change_aov_path()