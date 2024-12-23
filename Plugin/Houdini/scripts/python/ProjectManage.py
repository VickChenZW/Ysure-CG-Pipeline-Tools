import hou
import os
import datetime
import toolutils
import csv

def gettime(length:str) -> str:
    """
    获取当前的日期，并写为4位数
    """
    time=datetime.date.today()
    if length=="short":
        DATA=str(time).split("-")[1] + str(time).split("-")[2]
        return DATA

def useVick():
    """
    判断是否使用工具
    """
    if hou.expandString("$UseVick") == "1":
        usevick = True
    else:
        usevick = False
    return usevick

def addcachenode(node:hou.Node) -> hou.Node:
    """
    增加File Cache Node节点
    """
    DATA=gettime("short")
    animation=hou.ui.displayMessage("动画还是靜帧？",buttons=("动画","靜帧"))
    select_node: hou.Node=hou.selectedNodes()[0]
    parentnode:hou.Node=select_node.parent()
    cachenode:hou.Node=parentnode.createNode("filecache::2.0",DATA+"_Cache_")
    cachenode.setInput(0,select_node)
    cachenode.parm("filemethod").set(1)
    Basename='$JOB/geo/$SHOT/`strsplit($OS,"_",2)`/'
    
    if animation==0:
        cachenode.parm("file").set(Basename+DATA+"/$OS.$F.bego.sc")
    else:
        cachenode.parm("file").set(Basename+"$OS.bego.sc")
        cachenode.parm("timedependent").set(0)
        cachenode.parm("cachesim").set(0)
        cachenode.parm("trange").set(0)
    return cachenode

def addredshiftRopnode() -> hou.Node:
    """
    增加Rs渲染节点节点
    """
    DATA=gettime("short")
    rop:hou.Node=hou.node("/out")
    change=hou.expandString("$HIPNAME").split("_")[-3]
    rsrop:hou.Node=rop.createNode("Redshift_ROP")
    rsrop.setName(DATA+"_"+hou.expandString("$SHOT")+"_"+change)
    rsrop.parm("RS_outputFileFormat").set(3)
    rsrop.parm("RS_outputFileNamePrefix").set("$JOB/render/$SHOT/"+DATA+"/$OS.$F.png")
    return rsrop

def setproject(JOB,SHOT,CHANGE,VERSION,CEATOR):
    """
    设置Houdini文件
    """
    #get DATA
    DATA= gettime("short")
    #get HIPNAME
    HIPNAME = DATA + "_" +SHOT+ "_" + CHANGE + "_v" + VERSION + "_" +CEATOR+".hip"
    #get HIP
    HIP=JOB + "/project/"
    #get HIPNAME
    HIPFILE=HIP+HIPNAME
    # hou.hipFile.setName(self.HIPFILE)
    hou.hipFile.setName(HIPFILE)
    hou.hipFile.save()
    hou.hscript("setenv JOB=" + JOB)
    hou.hscript("setenv SHOT=" + SHOT)
    hou.hscript("setenv UseVick=1")

def havecsv(Path:str)->bool:
    path=Path
    return os.path.exists(path+'/project/usevick.csv')
    
def csvnew(Path:str):
    path=Path
    with open(path+'/project/usevick.csv','w') as f:
        csv_write =csv.writer(f)
        csv_head=["Data","ProjectName","change","version","Create"]
        csv_write.writerow(csv_head)

def csvwrite(Path,DATA,SHOT,CHANGE,VERSION,CEATOR):
    path=Path
    row=[DATA,SHOT,CHANGE,VERSION,CEATOR]
    print (row)
    with open(path+'/project/usevick.csv','a+') as f:
        writer=csv.writer(f)
        writer.writerow(row)

