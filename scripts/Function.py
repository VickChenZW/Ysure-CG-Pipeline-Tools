import configparser
import json
from datetime import datetime

import os, sys
import pyperclip

base_dir = os.path.dirname(os.path.abspath(__file__))


def get_resource_path(relative_path):
    """ 获取资源的绝对路径，适用于开发环境和 Nuitka/PyInstaller 打包后 """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Nuitka/PyInstaller 在 --onefile 模式下会创建临时目录 _MEIPASS
        # 注意：Nuitka 的 --onefile 行为可能略有不同，有时文件在可执行文件旁边
        base_path = sys._MEIPASS
        print(f"Running in onefile bundle, _MEIPASS: {base_path}")
    elif getattr(sys, 'frozen', False):
        # 在 --standalone 模式下，或某些 Nuitka --onefile 模式下
        # 资源通常位于可执行文件所在的目录
        base_path = os.path.dirname(os.path.abspath(sys.executable))
        print(f"Running as frozen executable, base path: {base_path}")
    else:
        # 在开发环境中运行（直接 python main.py）
        # 假设资源相对于当前脚本文件 (__file__)
        base_path = os.path.dirname(os.path.abspath(__file__))
        print(f"Running in development mode, base path: {base_path}")

    resource_path = os.path.join(base_path, relative_path)
    print(f"Calculated resource path for '{relative_path}': {resource_path}")
    # 添加检查，确保路径存在，便于调试
    # if not os.path.exists(resource_path):
    #    print(f"Warning: Resource path does not exist: {resource_path}")
    #    # 可以考虑列出 base_path 下的内容帮助调试
    #    try:
    #        print(f"Contents of base_path ({base_path}): {os.listdir(base_path)}")
    #    except OSError as e:
    #        print(f"Could not list contents of base_path: {e}")

    return resource_path


def get_from_clipboard():
    """
    从剪贴板获取信息
    :return:
    """
    return pyperclip.paste()


def mac_2_win(address):
    """
    mac地址转换为win的地址
    :param address: str
    :return: str
    """
    if "smb" in address or "Volumes" in address:
        # print(address)
        path_without_disk = address.split("YsureSuperHub")
        new_path = "Y:" + path_without_disk[1]
        pyperclip.copy(new_path)
        if os.path.isdir(new_path):
            os.startfile(new_path)
        else:
            new_path = os.path.split(new_path)[0] + "/"
            os.startfile(new_path)


def win_2_mac(address):
    """
    win地址转换为mac的地址
    :param address: str
    :return: str
    """
    if "Y:" in address:
        address = address.replace("\\", "/")
        path_without_disk = address.split('Y:/')
        new_path = "/Volumes/YsureSuperHub/" + path_without_disk[1]
        pyperclip.copy(new_path)


def get_date():
    now = datetime.now()
    year = str(now.year)
    month = now.month
    day = now.day
    if month < 10:
        month = "0" + str(month)
    else:
        month = str(month)

    if day < 10:
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
        os.makedirs(path + "/" + sub)
    for out in outs:
        os.makedirs(path + "/4.Output/" + out)

    for asset in assets:
        os.makedirs(path + "/1.File/" + asset)


def create_work_Folder(path, user, name, type_lists):
    project_path = path + "/2.Project/" + user
    if not os.path.exists(project_path):
        os.makedirs(project_path)
    project_path += "/" + name
    if not os.path.exists(project_path):
        os.makedirs(project_path)
    for file_type in type_lists:
        if not os.path.exists(project_path + "/" + file_type):
            os.makedirs(project_path + "/" + file_type)


def ini(root, project, user):
    config = configparser.ConfigParser()

    config["Settings"] = {
        "current_Root": root,
        "current_Project": project,
        "current_User": user
    }

    # config_path = get_resource_path(os.path.join(base_dir, "../config"))
    config_path = os.path.join(base_dir, "../config")

    if not os.path.exists(config_path):
        os.makedirs(config_path)

    path = os.path.join(config_path, "config.ini")
    with open(path, "w") as f:
        config.write(f)
    f.close()


def get_ini():
    config = configparser.ConfigParser()
    # path = get_resource_path(os.path.join(base_dir, "../config", "config.ini"))
    path = os.path.join(base_dir, "../config", "config.ini")
    if os.path.exists(path):
        config.read(path)

    root = config.get("Settings", "current_Root")
    project = config.get("Settings", "current_Project")
    user = config.get("Settings", "current_User")

    return root, project, user
