import hou,json,os
from datetime import datetime
node:hou.Node = hou.pwd()
cache_node = node.parent()
path = os.path.dirname(cache_node.parm("sopoutput").eval())
json_path = os.path.join(path,"info.json")
print(json_path)
# if not os.path.exists(json_path):
# print("111")
with open(json_path,"w") as f:
    dic = {
        "from":hou.hipFile.basename(),
        "datatime":str(datetime.now())
    }
    json.dump(dic,f)