@Echo off
echo.
echo VBoxWebSrv Windows
echo.

::
:: reset vars
::
set act=%1
set puname=%2
set pwset1=%3
set pwset2=%3
set arg1=%1
set arg2=%2
set arg3=%3

:: Search the registry tree for the required values
IF NOT EXIST "%PYTHON%" (
	FOR /F "skip=2 tokens=3" %%A IN ('REG QUERY "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Python.exe"') DO (
	   IF EXIST "%%A" SET PYTHON=%%A
	)
)
if NOT EXIST "%PYTHON%" GOTO NOPYTHON

:PROMPTACT
echo.
echo Commands: start, adduser, deluser 
echo.
if "%act%" == "" set /p act= Enter a command to run: 

if "%act%" == "start" (
	echo Starting...
	GOTO RUNPYTHON
)
if "%act%" == "adduser" GOTO PROMPTUSER
if "%act%" == "deluser" GOTO PROMPTUSER
echo %act% not understood.
set act=
GOTO PROMPTACT

:PROMPTUSER
if "%act%" == "deluser" (
	if "%puname%" == "" set /p puname= Enter a user to remove: 
) 
if "%act%" == "adduser" (
	if "%puname%" == "" set /p puname= Enter a user to add: 
) 
if "%puname%" == "" goto PROMPTUSER
if "%act%" == "deluser" goto DELUSER
if "%act%" == "adduser" goto PROMPTPW

GOTO RUNPYTHON

::
:: Prompt for password
::
:PROMPTPW
if "%pwset1%" == "" set /p pwset1= Enter password: 
if "%pwset1%" == "" GOTO PROMPTPW
if "%pwset2%" == "" set /p pwset2= Again: 
if "%pwset1%" == "%pwset2%" GOTO ADDUSER
echo Passwords do not match.
set pwset1=
set pwset2=
GOTO PROMPTPW

::
:: Add a user
::
:ADDUSER
set arg1="adduser"
set arg2=%puname%
set arg3="%pwset1%"
GOTO RUNPYTHON
 
::
:: Python not found
::
:NOPYTHON
echo Unable to find python.exe. Please set the PYTHON environment variable.
pause
GOTO :END

::
:: Delete a user
::
:DELUSER
set arg1="deluser"
set arg2=%puname%
set arg3=
GOTO RUNPYTHON

::
:: Start server
::
:RUNPYTHON
%PYTHON% %~dp0VBoxWebSrv.py %arg1% %arg2% %arg3%
pause

:END