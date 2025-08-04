import maya.cmds as cmds
import maya.mel as mel

# Make a new window
#
window = cmds.window( title="Long Name", iconName='Short Name', widthHeight=(200, 55) )
cmds.columnLayout( adjustableColumn=True )
cmds.button( label='Do Nothing' )
cmds.button( label='Close', command=('cmds.deleteUI(\"' + window + '\", window=True)') )
cmds.setParent( '..' )
cmds.showWindow( window )

# Resize the main window
#

# This is a workaround to get MEL global variable value in Python
gMainWindow = mel.eval('$tmpVar=$gMainWindow')
cmds.window( gMainWindow, edit=True, widthHeight=(900, 777) )

# Add a menu to the right of the main window's menu bar.
#
import maya.cmds as cmds;

cmds.setParent ( "" )
menuName = "menuTest"
cmds.optionMenu( menuName, label='test menu')
cmds.menuItem( label='item 1', parent = menuName )
cmds.menuItem( label='item 2', parent = menuName )
cmds.menuItem( label='item 3', parent = menuName )

cmds.window ("MayaWindow", edit=True, menuBarCornerWidget = (menuName, "topRight") )


# Shelf Button Code for Python 3 (Maya 2022+)
import sys
import importlib # 导入 importlib 模块

path_ = 'E:/TD/Ysure-CG-Pipeline-Tools/Plugin/Maya'
if path_ not in sys.path:
    sys.path.append(path_)

# 尝试导入模块，如果之前未导入，则正常导入
try:
    import Maya_Plugin as MP
except ImportError:
    # 处理第一次导入失败的情况 (虽然理论上路径已添加)
    print(f"Error: Could not import Maya_Plugin from {path_}")
    MP = None

if MP:
    # 关键步骤：重新加载模块
    importlib.reload(MP)
        try:
        # 先尝试关闭可能存在的旧窗口实例
        if MP.SimplePipelineToolUI.tool_instance is not None:
            print("Closing existing SimplePipelineToolUI instance.")
            MP.SimplePipelineToolUI.tool_instance.close()

        # 使用静态方法显示 UI
        MP.SimplePipelineToolUI.show_ui()

    except Exception as e:
        # 打印更详细的错误信息
        import traceback
        traceback.print_exc()
        cmds.error(f"启动 SimplePipelineTool UI 时发生错误: {e}")
else:
    print("Failed to load Maya_Plugin. UI cannot be shown.")