import c4d
import os,shutil

import maxon

def localize_tex():
    doc = c4d.documents.GetActiveDocument()
    list = []
    c4d.documents.GetAllAssetsNew(doc,False,"",c4d.ASSETDATA_FLAG_TEXTURESONLY,list)
    root = doc.GetDocumentPath()
    no_local = []
    for i in list:
        if os.path.dirname(i["filename"]) == root:
            pass
        else:
            no_local.append(i)
            print(i)
    fix_name = []
    for n in no_local:
        source = n["filename"]
        name = source.split("\\")[-1]
        des = os.path.join(root,"tex",name)
        shutil.copy(source,des)
        shader: c4d.Material = n["owner"]
        id = n.get("paramId", c4d.NOTOK)
        nodespace = n["nodeSpace"]
        nodepath = n['nodePath']
        print(shader.GetNodeMaterialReference())
        nodeMaterial:c4d.NodeMaterial = shader.GetNodeMaterialReference()
        graph:maxon.GraphModelInterface = nodeMaterial.GetGraph(nodespace)
        with graph.BeginTransaction() as t:
            node = graph.GetNode(maxon.NodePath(nodepath))
            pathPort =node.GetInputs().FindChild("com.redshift3d.redshift4c4d.nodes.core.texturesampler.tex0").FindChild("path")
            pathPort.SetDefaultValue(name)
            t.Commit()
        fix_name.append(name)
    c4d.gui.MessageDialog(f'{fix_name}本地化成功，共处理{len(fix_name)}个贴图！')











