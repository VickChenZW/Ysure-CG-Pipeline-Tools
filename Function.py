import pyperclip, os
from datetime import datetime
import json, configparser
import re


base_dir = os.path.dirname(os.path.abspath(__file__))


def get_from_clipboard():
    return pyperclip.paste()

def mac_2_win(address):
    if "smb" in address:
        backadd = address.split("YsureSuperHub")
        newpath = "Y:"+backadd[1]
        pyperclip.copy(newpath)
        if os.path.isdir(newpath):
            os.startfile(newpath)
        else:
            file = os.path.abspath(newpath)
            newpath = os.path.split(newpath)[0]+"/"
            os.startfile(newpath)
            # 选中文件，但是没有解决后缀名的问题
            # os.system(f'explorer /select, {file}')

def win_2_mac(address):
    if "Y:" in address:
        address = address.replace("\\","/")
        backadd = address.split('Y:/')
        newpath = "/Volumes/YsureSuperHub/" + backadd[1]
        pyperclip.copy(newpath)

def is_path(address):
    path = os.path.isdir(address)
    return path


def get_date():
    now = datetime.now()
    year = str(now.year)
    month = now.month
    day = now.day
    if month<10:
        month = "0" + str(month)
    else:
        month = str(month)

    if day<10:
        day = "0" + str(day)
    else:
        day = str(day)

    date = year + "." + month + "." + day
    return date

def create_path(address):
    if not os.path.exists(address):
        os.makedirs(address)
    else:
        return False

def path_2_json(address, path):
    dict = {}
    dict_list = []
    names = os.listdir(address)
    for name in names:
        if "_" in name:
            if os.path.isdir(address+"\\"+name):
                d = name.split("_")[0]
                n = name.split("_")[-1]
                # print(d,n)
                dict = ({"name": n, "date": d,  "describe": ""})
                dict_list.append(dict)
    # print(dict_list)
    with open(path, "w") as f:
         json.dump(dict_list, f)
    f.close()


def getjson(path):
    with open(path, "r") as f:
        json_file = json.load(f)
    return json_file


def json_2_path(address):
    name = []
    date = []
    path_dic_lists = getjson(address)
    if path_dic_lists != None:
        for list in path_dic_lists:
            name.append(list["name"])
            date.append(list["date"])
    return name, date



def get_Project_info(path):
    infos = []
    names = os.listdir(path)
    for name in names:
        if "_" in name:
            if os.path.isdir(path + "\\" + name):
                if os.path.exists(path + "\\" + name + "\\metadata"):
                    with open(path + "\\" + name + "\\metadata\\info.json", "r", encoding="utf-8") as f:
                        info = json.load(f)
                    f.close()
                    infos.append(info)
    return infos


def create_project_info(name, en_Name, des, path):
    info_dic = ({"name": name, "Date": get_date(), "en_Name": en_Name, "describe": des, "path": path})
    create_path(path + "/metadata")
    with open(path + "/metadata/info.json", "w", encoding='utf-8') as f:
        json.dump(info_dic, f, ensure_ascii=False)
    f.close()


def create_sub_folders(path):
    subs = ["1.File", "2.Project", "3.Comp", "4.Output"]
    outs = ["Sequence", "Video"]
    assets = ["Documents", "HDRI", "Image", "Model", "PS+AI", "Temp", "Texture", "Video"]
    for sub in subs:
        os.makedirs(path+"/"+sub)
    for out in outs:
        os.makedirs(path+"/4.Output/"+out)

    for asset in assets:
        os.makedirs(path+"/1.File/"+asset)


def create_work(path, user, name, format, version, describe):
    filename = path + "/2.Project/" + user + "/" + name + "/" + version + "." + format
    with open(filename, "w") as f:
        pass
    f.close()


def create_work_Folder(path, user, name, list):
    project_path = path+"/2.Project/"+user
    if not os.path.exists(project_path):
        os.makedirs(project_path)
    project_path+="/"+name
    if not os.path.exists(project_path):
        os.makedirs(project_path)
    for l in list:
        if not os.path.exists(project_path + "/" +l):
            os.makedirs(project_path + "/" +l)


def ini(root, project, user):
    config = configparser.ConfigParser()

    config["Settings"] = {
        "current_Root": root,
        "current_Project": project,
        "current_User": user,
    }
    if not os.path.exists(os.path.join(base_dir,"config")):
        os.makedirs(os.path.join(base_dir,"config"))

    path = os.path.join(base_dir,"config","config.ini")
    with open(path,"w") as f:
        config.write(f)
    f.close()


def get_ini():
    config = configparser.ConfigParser()
    path = os.path.join(base_dir, "config", "config.ini")
    if os.path.exists(path):
        config.read(path)

    root = config.get("Settings", "current_Root")
    project = config.get("Settings", "current_Project")
    user = config.get("Settings", "current_User")
    return root, project, user







