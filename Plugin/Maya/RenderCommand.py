# -*- coding: utf-8 -*-

import maya.cmds as cmds  # 用于获取当前场景信息等 (可选, 如果在Maya内部运行)
import subprocess
import os
import platform



def get_maya_render_executable_path(maya_version_year=None):
    """
    尝试自动查找Maya的render可执行文件路径。
    用户也可以手动提供此路径。

    Args:
        maya_version_year (int, optional): Maya的版本年份, 例如 2023, 2024。
                                           如果为None, 会尝试一些常见的默认路径。

    Returns:
        str: Maya render可执行文件的路径, 如果找到的话。否则返回 None。
    """
    render_exe_name = "render.exe"

    # 尝试从 MAYA_LOCATION 环境变量获取
    maya_location = os.environ.get("MAYA_LOCATION")
    if maya_location:
        potential_path = os.path.join(maya_location, "bin", render_exe_name)
        if os.path.exists(potential_path):
            return potential_path

    # 基于版本年份的常见路径 (Windows示例)
    if platform.system() == "Windows":
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        common_paths = []
        if maya_version_year:
            common_paths.append(
                os.path.join(program_files, f"Autodesk\\Maya{maya_version_year}\\bin\\{render_exe_name}"))
        else:  # 尝试一些常见的年份
            for year in ["2024", "2023", "2022", "2020", "2019", "2018"]:  # 可以扩展这个列表
                common_paths.append(os.path.join(program_files, f"Autodesk\\Maya{year}\\bin\\{render_exe_name}"))

        for path_to_check in common_paths:
            if os.path.exists(path_to_check):
                return path_to_check

    print("警告: 未能自动找到Maya Render可执行文件。请在脚本中手动指定 `maya_render_exe` 路径。")
    return None


# 拍屏功能
def run_maya_command_line_render(
        scene_path,
        project_path,
        output_dir,
        renderer="arnold",  # 例如: arnold, mayaSoftware, mayaHardware2, mentalRay (旧版), vray (需配置)
        start_frame=1,
        end_frame=175,
        by_frame=1,
        camera="perspShape",
        width=1920,
        height=1080,
        image_prefix=None,  # 如果为None, Maya会使用场景名或默认设置
        render_layer=None,  # 例如 "defaultRenderLayer" 或其他自定义渲染层
        maya_render_exe=None,  # Maya 'render'可执行文件的完整路径。如果为None, 脚本会尝试查找。
        maya_version=None,  # Maya 的版本年份, e.g., 2023, 用于帮助查找 render_exe
        additional_flags=None  # 额外的命令行参数列表, e.g., ["-ai:lve 2", "-ai:threads -4"]
):
    """
    使用Maya命令行渲染器渲染指定的场景文件。

    参数:
    scene_path (str): Maya场景文件 (.ma 或 .mb) 的完整路径。
    project_path (str): Maya项目的根目录路径。
    output_dir (str): 渲染图像的输出目录。
    renderer (str): 要使用的渲染器名称 (例如 'arnold', 'mayaSoftware')。
    start_frame (int): 开始帧。
    end_frame (int): 结束帧。
    by_frame (int): 帧步长。
    camera (str): 要渲染的摄影机名称 (shape node name or transform node name)。
    width (int): 输出图像宽度。
    height (int): 输出图像高度。
    image_prefix (str, optional): 输出图像文件的前缀。如果为None, Maya使用默认。
    render_layer (str, optional): 要渲染的特定渲染层名称。
    maya_render_exe (str, optional): Maya 'render' 可执行文件的完整路径。
    maya_version (int, optional): Maya的版本年份, 用于辅助查找 maya_render_exe。
    additional_flags (list, optional): 额外的命令行标志列表。
    """

    if not maya_render_exe:
        maya_render_exe = get_maya_render_executable_path(maya_version_year=maya_version)

    if not maya_render_exe or not os.path.exists(maya_render_exe):
        print(f"错误: Maya Render可执行文件路径 '{maya_render_exe}' 无效或未找到。请检查路径。")
        return False

    if not os.path.exists(scene_path):
        print(f"错误: 场景文件 '{scene_path}' 不存在。")
        return False

    if not os.path.exists(project_path):
        print(f"错误: 项目路径 '{project_path}' 不存在。")
        return False

    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"信息: 已创建输出目录: {output_dir}")
        except OSError as e:
            print(f"错误: 无法创建输出目录 '{output_dir}': {e}")
            return False

    command = [maya_render_exe]

    # 项目路径
    command.extend(["-proj", project_path])

    # 渲染器
    command.extend(["-r", renderer])

    # 帧范围
    command.extend(["-s", str(start_frame)])
    command.extend(["-e", str(end_frame)])
    command.extend(["-b", str(by_frame)])

    # 分辨率
    command.extend(["-x", str(width)])
    command.extend(["-y", str(height)])

    # 摄影机
    command.extend(["-cam", camera])

    # 输出目录 (Render Destination)
    command.extend(["-rd", output_dir])

    # 图像文件名前缀 (Image Name)
    if image_prefix:
        command.extend(["-im", image_prefix])

    # 渲染层
    if render_layer:
        command.extend(["-rl", render_layer])

    # 详细输出级别 (可选, 0-6, 默认可能是3或4)
    # command.extend(["-v", "5"]) # 增加详细程度

    # 强制覆盖现有帧 (如果需要)
    # command.append("-f") # 对于某些渲染器或版本, 这个可能不是必需的或有不同行为

    # 添加其他自定义标志
    if additional_flags:
        if isinstance(additional_flags, list):
            command.extend(additional_flags)
        else:
            print("警告: additional_flags应该是列表类型。已忽略。")

    # 场景文件路径 (通常放在命令的最后)
    command.append(scene_path)

    print("将要执行的渲染命令 (Executing render command):")
    print(" ".join(f'"{c}"' if " " in c else c for c in command))  # 打印时给带空格的参数加上引号

    try:
        # 执行命令
        # universal_newlines=True (或 text=True in Python 3.7+) 使输出为文本字符串
        # capture_output=True (Python 3.7+) 可以捕获 stdout 和 stderr
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

        # 实时打印输出 (可选)
        print("\n--- 渲染器输出 (Renderer Output) ---")
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                print(line, end='')  # end='' 防止双重换行
            process.stdout.close()

        if process.stderr:
            print("\n--- 渲染器错误输出 (Renderer Error Output) ---")  # 错误信息也可能在stdout
            for line in iter(process.stderr.readline, ''):
                print(line, end='')
            process.stderr.close()

        process.wait()  # 等待渲染完成

        if process.returncode == 0:
            print(f"\n渲染成功完成。返回码: {process.returncode}")
            return True
        else:
            print(f"\n渲染失败或出现错误。返回码: {process.returncode}")
            # 错误信息应该已经在上面 stderr 部分打印出来了
            return False

    except FileNotFoundError:
        print(f"错误: Maya Render可执行文件 '{maya_render_exe}' 未找到。请确保路径正确且文件存在。")
        return False
    except Exception as e:
        print(f"执行渲染命令时发生错误: {e}")
        return False


def ffmpeg(img_path, out_path):
    # Make me a .mov
    # https://stackoverflow.com/questions/14430593/encoding-a-readable-movie-by-quicktime-using-ffmpeg
    # ffmpeg -i /tmp/%04d.JPEG -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -f mp4 -vcodec libx264 -pix_fmt yuv420p .v1.mp4
    # add -y to the command line after input file path to force overwriting if file exists
    # See link below for more info about adding metadata with ffmpeg
    # https://ubuntuforums.org/showthread.php?t=1193808
    # You can simply press enter where you want the newline as you are typing your command.
    # http://ffmpeg.gusari.org/viewtopic.php?f=11&t=3032
    # by default ffmpeg outputs 25fps, change this with: -r 24
    convert2mov_command = 'ffmpeg'
    convert2mov_command += ' -i ' + string.replace(flipbook_output_path, '$F4', '%04d')
    convert2mov_command += ' -y'
    convert2mov_command += ' -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2"'
    convert2mov_command += ' -f mp4 -vcodec libx264 -pix_fmt yuv420p'
    convert2mov_command += ' -r 24'
    # Set the Constant Rate Factor of the video
    # http://slhck.info/video/2017/02/24/crf-guide.html
    convert2mov_command += ' -crf 22'
    # Set the bitrate of the vide0
    # https://gist.github.com/ksharsha/b06d184391290bc3b87fdadadb73c5bc#file-ffmpeg-compress
    # convert2mov_command+=' -b:v 750k'
    convert2mov_command += ' -metadata title="' + hou.getenv('HIPNAME') + '"'
    # Metadata comment block:
    convert2mov_command += ' -metadata comment="'
    convert2mov_command += 'SOURCE: ' + hou.hipFile.path() + '\n'
    convert2mov_command += 'SNAPSHOT: ' + backup_file_path + '\n'
    convert2mov_command += 'USER: ' + hou.getenv('USER') + '\n'
    convert2mov_command += 'VERSION: ' + hou.applicationVersionString() + '\n'
    convert2mov_command += 'PLATFORM: ' + hou.applicationPlatformInfo()
    convert2mov_command += '"'
    # Metadata can be viewed using ffprobe, which comes with ffmpeg

    convert2mov_command += ' ' + mp4_output_path

    print
    'running "%s"' % convert2mov_command
    os.system(convert2mov_command)
    # Newline
    # os.system('echo')
    print
    'done'

    # Taking temporary L on gif feature to finish main part
    # Make me a .gif
    # convert2gif_command = '/usr/local/bin/convert -loop 0 ' + src_frames + ' -fuzz 0% -layers Optimize ' + out_gif

    # Cleanup
    # Remove the .JPEGs generated by the flipbook

    # Remove the quotes at the beginning and ending of the path
    flipbook_output_path = flipbook_output_path.strip('"\'')
    # Replace the %04d ffmpeg frame indicator with * wildcard
    flipbook_output_path = flipbook_output_path.translate(None, "'").replace('%04d', '*')
    # This is done to handle paths that contain spaces, we have to encapsulate the dir path in quotes.
    # the wildcard part of the command must be outside the quotes, so that's why there's some dirname, basename finessing
    flipbook_output_path = '"' + os.path.dirname(flipbook_output_path) + '"' + '/' + os.path.basename(
        flipbook_output_path)

    command = 'rm -Rf %s' % flipbook_output_path
    # command+= str(flipbook_output_path)
    print
    'running %s' % command
    os.system(command)


# --- 如何使用 (示例) ---
if __name__ == "__main__":
    # --- 请根据您的环境修改以下参数 ---

    # 1. Maya 'render' 可执行文件的路径 (如果脚本无法自动找到)
    #    Windows 示例: r"C:\Program Files\Autodesk\Maya2023\bin\render.exe"
    #    macOS 示例: "/Applications/Autodesk/maya2023/Maya.app/Contents/bin/Render"
    #    Linux 示例: "/usr/autodesk/maya2023/bin/Render"
    custom_maya_render_exe = None  # 设置为None则尝试自动查找, 或提供完整路径
    maya_version_year_for_search = 2024  # 帮助自动查找, 例如 2022, 2023, 2024

    # 2. Maya 项目路径 (包含 sourceimages, scenes, images 等文件夹的根目录)
    #    如果从Maya内部运行此脚本, 可以尝试获取当前项目路径
    try:
        current_project_path = cmds.workspace(query=True, rootDirectory=True)
    except NameError:  # 如果不在Maya环境中 (cmds未定义)
        current_project_path = r"D:\Path\To\Your\MayaProject"  # <--- 修改这里

    my_project_path = current_project_path

    # 3. Maya 场景文件路径 (.ma 或 .mb)
    #    如果从Maya内部运行此脚本, 可以尝试获取当前场景路径
    try:
        current_scene_path = cmds.file(query=True, sceneName=True)
        if not current_scene_path:  # 如果场景未保存
            current_scene_path = os.path.join(my_project_path, "scenes", "my_scene.mb")  # <--- 提供一个默认或示例
    except NameError:
        current_scene_path = os.path.join(my_project_path, "scenes", "my_scene.mb")  # <--- 修改这里

    my_scene_path = current_scene_path

    # 4. 渲染图像的输出目录 (通常在项目下的 'images' 文件夹)
    my_output_dir = os.path.join(my_project_path, "images", "cmd_render_output")  # <--- 修改这里 (子文件夹名)

    # 5. 渲染器名称
    my_renderer = "hw2"  # 或者 "mayaSoftware", "mayaHardware2" 等

    # 6. 帧范围
    my_start_frame = 1
    my_end_frame = 5  # 渲染少量帧作为测试

    # 7. 摄影机
    my_camera = "Cam_020"  # 或者场景中的其他摄影机名 (shape节点或transform节点)

    # 8. 分辨率
    my_width = 1920
    my_height = 1080

    # 9. 输出图像文件名前缀 (可选)
    #    例如: "myRenderShot_v01" -> myRenderShot_v01.0001.exr
    #    如果为None, Maya会使用默认命名 (通常基于场景名和渲染层)
    my_image_prefix = os.path.splitext(os.path.basename(my_scene_path))[0] + "_cmd"

    # 10. 渲染层 (可选, 如果不指定或为None, 则渲染当前激活的或默认的渲染层)
    my_render_layer = None  # 或者 "masterLayer", "myCustomLayer"

    # 11. 额外的渲染器特定标志 (可选)
    #     例如 Arnold 的日志详细级别, 线程数等
    #     my_additional_flags = ["-ai:lve", "2", "-ai:threads", "-2"] # Arnold: log verbosity error, use all cores-2
    my_additional_flags = None
    if my_renderer == "arnold":
        # Arnold 渲染通常不需要 -threads 标志，它会默认使用合适的线程数。
        # -set ArnoldRenderOptions.AASamples 5 (设置AA采样)
        # -ai:lve 2 (Arnold log verbosity: 0=off, 1=errors, 2=warns+info, 3=debug)
        my_additional_flags = ["-ai:lve", "2"]
        # 如果要覆盖Arnold渲染设置中的线程数:
        # my_additional_flags.extend(["-ai:threads", "4"]) # 使用4个线程

    # --- 执行渲染 ---
    print("准备执行Maya命令行渲染...")

    # 确保在Maya主线程中运行 (如果从Maya内部调用此脚本)
    # 或者作为一个独立的Python脚本运行
    # if not cmds.about(batch=True): # 这个检查主要用于UI脚本，对于命令行调用可能不那么相关

    success = run_maya_command_line_render(
        scene_path=my_scene_path,
        project_path=my_project_path,
        output_dir=my_output_dir,
        renderer=my_renderer,
        start_frame=my_start_frame,
        end_frame=my_end_frame,
        camera=my_camera,
        width=my_width,
        height=my_height,
        image_prefix=my_image_prefix,
        render_layer=my_render_layer,
        maya_render_exe=custom_maya_render_exe,  # 传递自定义路径或None
        maya_version=maya_version_year_for_search,
        additional_flags=my_additional_flags
    )

    if success:
        print("\n命令行渲染任务已提交并执行完毕。请检查输出目录: {}".format(my_output_dir))
        # 可选: 渲染完成后打开输出文件夹
        if platform.system() == "Windows":
           os.startfile(my_output_dir)
    else:
        print("\n命令行渲染任务执行失败或出现问题。请检查上面的日志输出。")

