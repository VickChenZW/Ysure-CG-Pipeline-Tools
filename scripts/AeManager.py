import subprocess
import os
import sys

# --- 配置部分 ---
# 请将这里的路径替换为你电脑上 After Effects 可执行文件的实际路径
# 示例路径 (Windows): "C:/Program Files/Adobe/Adobe After Effects 2023/Support Files/AfterFX.exe"
# 示例路径 (macOS): "/Applications/Adobe After Effects 2023/Adobe After Effects 2023.app"
# 根据你的安装版本和操作系统修改
AFTER_EFFECTS_EXECUTABLE = r"C:\Program Files\Adobe\Adobe After Effects 2023\Support Files\AfterFX.exe"

# 请将这里的路径替换为你想要 After Effects 启动时自动运行的 ExtendScript (.jsx) 文件的实际路径
# 例如："/path/to/your/create_ae_project.jsx"
EXTENDSCRIPT_FILE_PATH = r"C:\Users\Victo\Desktop\test.jsx"

# --- 配置保存路径和文件名 (由Python控制) ---
# 请将这里的路径替换为你希望 After Effects 项目保存的目录
# 例如 (Windows): "C:/AfterEffectsProjects"
# 例如 (macOS): "/Users/YourUsername/Documents/AfterEffectsProjects"
DESIRED_SAVE_DIRECTORY = r"C:\Users\Victo\Desktop"

# 指定希望保存的项目文件名
DESIRED_SAVE_FILENAME = "My_Automated_Project_From_Python.aep"

# --- 函数部分 ---

def launch_after_effects_and_run_script(ae_path, script_path, save_dir, save_file):
    """
    启动 After Effects 并自动运行指定的 ExtendScript 脚本，
    通过环境变量传递保存路径和文件名。

    Args:
        ae_path (str): After Effects 可执行文件的完整路径。
        script_path (str): 要运行的 .jsx 脚本文件的完整路径。
        save_dir (str): 希望保存项目的目录。
        save_file (str): 希望保存的项目文件名。
    """
    if not os.path.exists(ae_path):
        print(f"错误：找不到 After Effects 可执行文件：{ae_path}")
        print("请检查 AFTER_EFFECTS_EXECUTABLE 变量中的路径是否正确。")
        return

    if not os.path.exists(script_path):
        print(f"错误：找不到 ExtendScript 脚本文件：{script_path}")
        print("请检查 EXTENDSCRIPT_FILE_PATH 变量中的路径是否正确。")
        return

    # --- 设置环境变量 ---
    # ExtendScript 将从这些环境变量中读取保存信息
    # 使用 AE_SAVE_DIR 和 AE_SAVE_FILENAME 作为环境变量名
    os.environ['AE_SAVE_DIR'] = save_dir
    os.environ['AE_SAVE_FILENAME'] = save_file
    print(f"设置环境变量：AE_SAVE_DIR={os.environ['AE_SAVE_DIR']}, AE_SAVE_FILENAME={os.environ['AE_SAVE_FILENAME']}")

    print(f"正在启动 After Effects 并尝试运行脚本：{script_path}")

    try:
        # 构建命令
        # 使用 -r 参数指定启动时运行的脚本
        command = [ae_path, "-r", script_path]

        # 使用 Popen 启动进程，并传递当前的环境变量
        # os.environ.copy() 是为了复制当前环境，避免只传递我们设置的变量
        process = subprocess.Popen(command, env=os.environ.copy())

        print("命令已发送。After Effects 应该正在启动并运行脚本。")

        # 可选：如果不想让这些环境变量保留在系统中，可以在AE启动后删除它们
        # 注意：这并不能保证在 ExtendScript 读取之前删除，所以通常不推荐
        # del os.environ['AE_SAVE_DIR']
        # del os.environ['AE_SAVE_FILENAME']

    except FileNotFoundError:
        print(f"错误：找不到命令或可执行文件 '{ae_path}'。请确认路径是否正确。")
    except Exception as e:
        print(f"启动 After Effects 时发生错误：{e}")

# --- 主执行部分 ---
if __name__ == "__main__":
    # 确保用户已经修改了路径和配置
    if AFTER_EFFECTS_EXECUTABLE == "请在这里填写你的After Effects可执行文件路径" or \
       EXTENDSCRIPT_FILE_PATH == "请在这里填写你的.jsx脚本文件路径" or \
       DESIRED_SAVE_DIRECTORY == "请在这里填写你希望保存项目的目录":
        print("请先编辑脚本，将 AFTER_EFFECTS_EXECUTABLE, EXTENDSCRIPT_FILE_PATH 和 DESIRED_SAVE_DIRECTORY 变量替换为你的实际路径。")
    else:
        launch_after_effects_and_run_script(
            AFTER_EFFECTS_EXECUTABLE,
            EXTENDSCRIPT_FILE_PATH,
            DESIRED_SAVE_DIRECTORY,
            DESIRED_SAVE_FILENAME
        )

