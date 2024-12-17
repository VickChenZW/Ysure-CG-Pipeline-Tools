' VBScript to run an ExtendScript in After Effects

Option Explicit

Dim objShell, strAfterEffectsPath, strExtendScriptPath, intReturn

' 设置 After Effects 的路径
strAfterEffectsPath = """C:\Program Files\Adobe\Adobe After Effects 2022\Support Files\AfterFX.exe""" ' 根据你的安装位置调整此路径

' 设置 ExtendScript 文件的路径
strExtendScriptPath = "E:\learn\Python\Ysure-CG-Pipeline-Tools\Plugin\Ae\js.jsx" ' 替换为你的 .jsx 文件的实际路径

' 创建 WScript.Shell 对象
Set objShell = CreateObject("WScript.Shell")

' 使用 After Effects 打开 ExtendScript
intReturn = objShell.Run(strAfterEffectsPath & " -r " & Chr(34) & strExtendScriptPath & Chr(34), 1, True)

' 检查命令是否成功执行
' If intReturn = 0 Then
'     WScript.Echo "脚本已成功执行。"
' Else
'     WScript.Echo "执行脚本时出错。错误代码: " & intReturn
' End If

' 清理
Set objShell = Nothing