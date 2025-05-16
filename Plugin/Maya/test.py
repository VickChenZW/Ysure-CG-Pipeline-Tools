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
