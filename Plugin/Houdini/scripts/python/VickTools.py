from functools import cache
import csv
import os
import hou
import datetime
import toolutils
from PySide2 import QtWidgets,QtCore,QtUiTools,QtGui
try:
    import ProjectManage as PM
except:
    from ProjectSetting import ProjectManage as PM


class vicktools(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        #初始化
        self.UseVick=PM.useVick()
        self.JOB:str
        self.HIP:str
        self.HIPNAME:str
        self.Shot:str
        self.HIPFILE:str
        #初始化名称
        self.DATA:str
        self.Change:str
        self.Version:str
        self.Creator:str

        self.SetUI()

    def SetUI(self):
        # import UI File
        path=os.path.realpath(__file__).split("VickTools.py")[0]
        self.ui=QtUiTools.QUiLoader().load(path+'test.ui')
        
        # MainLayout
        mainLayout=QtWidgets.QVBoxLayout()

        # Add UI
        mainLayout.addWidget(self.ui)

        #get bottom element
        self.setprojectBTN=self.ui.findChild(QtWidgets.QPushButton,"setprobtn")
        self.changepathBTN = self.ui.findChild(QtWidgets.QPushButton, "chpbtn")
        self.cachefileBTN=self.ui.findChild(QtWidgets.QPushButton,"cachebtn")
        self.rsfileBTN=self.ui.findChild(QtWidgets.QPushButton,"rsrenderbtn")
        self.refreshCacheBTN=self.ui.findChild(QtWidgets.QPushButton,"refcache")


        #get input box
        self.shotTEXT = self.ui.findChild(QtWidgets.QLineEdit, "shot")
        self.changeTEXT=self.ui.findChild(QtWidgets.QLineEdit,"change")
        self.versionTEXT = self.ui.findChild(QtWidgets.QSpinBox, "version")
        self.creatorTEXT = self.ui.findChild(QtWidgets.QLineEdit, "creator")
        self.pathTEXT = self.ui.findChild(QtWidgets.QLineEdit,"path")

        #get list box
        self.cachelistList=self.ui.findChild(QtWidgets.QListWidget,"cachelist")
        self.cachelistList.setSpacing(10)

        #lineEdit show
        self.shotTEXT.setText("ProjectName")
        self.changeTEXT.setText("Demo")
        self.versionTEXT.setValue(1)
        self.creatorTEXT.setText("Vick")


        #link function
        self.setprojectBTN.clicked.connect(self.setproject)
        self.cachefileBTN.clicked.connect(self.addcachenode)
        self.rsfileBTN.clicked.connect(self.addredshiftrop)
        self.changepathBTN.clicked.connect(self.choose_path)
        self.refreshCacheBTN.clicked.connect(self.findCacheNode)

        #not use tools or new one
        if self.UseVick:
            self.pathTEXT.setText(hou.expandString("$JOB"))
            self.textboxshow()
        else:    
            self.setprojectBTN.setEnabled(False)
        
        # Set Layout
        self.setLayout(mainLayout)


    #set project function
    def choose_path(self):
        __jobpath=hou.ui._selectFile(title="Choose Job Path", file_type=hou.fileType.Directory)
        if str(__jobpath)[:-1]== "":
            hou.ui.displayMessage("哥们！您得选择个目录呀！",buttons=("好的",))
        else:
            self.setprojectBTN.setEnabled(True)
            self.pathTEXT.setText(str(__jobpath))
    
    def setproject(self):
        self.Shot=self.shotTEXT.text()
        self.Change=self.changeTEXT.text()
        self.Version=str(self.versionTEXT.value())
        self.Creator=self.creatorTEXT.text()
        self.JOB=self.pathTEXT.text()
        PM.setproject(self.JOB,self.Shot,self.Change,self.Version,self.Creator)
        self.textboxshow()
        if PM.havecsv(self.JOB):
            pass
        else:
            PM.csvnew(self.JOB)
        PM.csvwrite(self.JOB,PM.gettime("short"),self.Shot,self.Change,self.Version,self.Creator)
            

    def addcachenode(self):
        select_node: hou.Node=hou.selectedNodes()[0]
        parentnode:hou.Node=select_node.parent()
        PM.addcachenode(parentnode)

    def addredshiftrop(self):
        PM.addredshiftRopnode()
    #subfunction
    
    
    def textboxshow(self):
        self.hipname_already=hou.text.expandString("$HIPNAME").split("_")
        self.hip=hou.text.expandString("$JOB")
        self.pathTEXT.setText(self.hip)
        self.shotTEXT.setText(self.hipname_already[1])
        self.changeTEXT.setText(self.hipname_already[2])
        self.versionTEXT.setValue(int(self.hipname_already[3][1]))
        self.creatorTEXT.setText(self.hipname_already[4])

    def debug(self):
        print(self.changeTEXT.text())
    def movetoolderfolder(self):
        self.hipold=hou.text.expandString("$HIPNAME")

    def findCacheNode(self):
        nodes = hou.node("/obj").allSubChildren()
        self.cachelistList.clear()
        count=0
        for node in nodes:
            if node.type().name() == "filecache::2.0":
                item:QtWidgets.QListWidgetItem=QtWidgets.QListWidgetItem(node.path())
                # print(node.evalParm('loadfromdisk'))
                if node.isGenericFlagSet(hou.nodeFlag.Bypass):
                    item.setTextColor(QtGui.QColor("yellow"))
                elif node.evalParm('loadfromdisk')==1:
                    item.setTextColor(QtGui.QColor("green"))
                else:
                    item.setTextColor(QtGui.QColor("grey"))

                self.cachelistList.addItem(item)
                count+=1
        self.cachelistList.doubleClicked.connect(self.opennodepath)
        # print("test")
    def opennodepath(self,path):
        node:hou.Node=hou.node(path.data())
        panel:hou.PaneTab=hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        panel.setPwd(node.parent())
        node.setSelected(True,False)
        node.setGenericFlag(hou.nodeFlag.Template,True)




