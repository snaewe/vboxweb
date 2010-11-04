Dim sh, scriptPath, p, WshShell, objArgs, strArgs

set sh = WScript.CreateObject("WScript.Shell")
scriptPath = Left ( WScript.ScriptFullName, InStrRev ( WScript.ScriptFullName, WScript.ScriptName) - 1 )
p = sh.RegRead("HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Python.exe\")

rem WScript.Echo p & " " & scriptPath

Set WshShell = WScript.CreateObject("WScript.Shell")

Set objArgs = WScript.Arguments
For I = 0 to objArgs.Count - 1
   strArgs = strArgs & " " & objArgs(I)
Next

WshShell.Run "cmd /C " & p & " " & scriptPath & "VBoxWebSrv.py " & strArgs & " & pause", 1, True