import hou, json, os
from datetime import datetime


class OutJson(object):
    def __init__(self):
        self.root_path = hou.hipFile.path()
        self.from_user = self.root_path
        self.user = hou.pwd().parm("user_text").eval()
        self.take = hou.pwd().parm("takes_text").eval()
        self.notes = hou.pwd().parm("notes").eval()
        for _ in range(3):
            self.root_path = os.path.dirname(self.root_path)

        for _ in range(2):
            self.from_user = os.path.dirname(self.from_user)
        self.from_user = os.path.basename(self.from_user)

        # self.des_path = os.path.dirname(hou.pwd().parm('sopoutput').eval())
        self.des_path = os.path.join(self.root_path, self.user, self.take, '__IN__')

    def write_json(self):
        metadata_path = os.path.join(self.des_path,"metadata")
        if not os.path.exists(metadata_path):
            os.makedirs(metadata_path)

        json_path = os.path.join(metadata_path,"in.json")
        if not os.path.exists(json_path):
            with open(json_path, 'r+', encoding='utf-8') as f:
                dic = []
                json.dump(dic, f)

        with open(json_path, 'r+', encoding='utf-8') as f:
            file = json.load(f)
            new_file = []
            for i in file:
                if i['file_name'] == os.path.basename(hou.pwd().parm('sopoutput').eval()):
                    pass
                else:
                    new_file.append(i)
            dic = {
                "file_name": os.path.basename(hou.pwd().parm('sopoutput').eval()),
                "date": str(datetime.now()),
                "from": self.from_user,
                "to": self.user,
                "make": hou.hipFile.path(),
                "describe": self.notes,
            }
            new_file.append(dic)
            f.seek(0)
            f.truncate()
            json.dump(new_file, f, ensure_ascii=False, indent=4)
        f.close()
        print("写入成功!")

out = OutJson()
out.write_json()
