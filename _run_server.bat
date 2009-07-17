@ECHO OFF
REM NOTE: Since 4NT has another syntax of "start", 
REM		  this won't work correctly!
set VBOX_PATH=V:\VBox\trunk\
set VBOX_OUT=%VBOX_PATH%\out\win.amd64\release\bin\
set VBOX_SDK_PATH=%VBOX_OUT%\sdk
set VBOX_WEB_PATH=%VBOX_PATH%\src\VBox\Frontends\VBoxWeb

set PYTHONPATH=%VBOX_SDK_PATH%\bindings\glue\python
set PYTHON=C:\Python26

start /D %VBOX_WEB_PATH% %PYTHON%\python VBoxWebSrv.py
start /D %VBOX_OUT% %VBOX_OUT%\VBoxHeadless -startvm "WinXP SP2"
start /D %VBOX_OUT% %VBOX_OUT%\VBoxHeadless -startvm "Win2K"

:update
svn update
echo "Sleeping ..."
sleep 60
goto update

:exit
