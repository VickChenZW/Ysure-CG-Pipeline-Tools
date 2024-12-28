import hou,json,os
from datetime import datetime
node:hou.Node = hou.pwd()
cache_node = node.parent()
path = os.path.dirname(cache_node.parm("sopoutput").eval())
json_path = os.path.join(path,"info.json")

with open(json_path,"w") as f:
    dic = {
        "file_name": "test.fbx",
        "date": "2024-12-24 17:35:42.034408",
        "from": "Vick",
        "to": "Vick",
        "make": "Y:/02.CG_Project/2024.12.09_EssilorPipeline/2.Project/Vick/testtest_v002.c4d",
        "describe": "haha",
        "path": "Y:/02.CG_Project/2024.12.09_EssilorPipeline/2.Project/Vick/test/__IN__/test.fbx"
    }
    dic = {
        "from":hou.hipFile.basename(),
        "datatime":datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    json.dump(dic,f)