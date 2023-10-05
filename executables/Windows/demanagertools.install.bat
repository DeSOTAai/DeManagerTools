@ECHO OFF
cls
:: Instalation VARS
:: Model GIT
set manager_git=https://github.com/DeSOTAai/DeManagerTools.git
set manager_git_branch=main
:: - Model Path
set desota_root_path=%UserProfile%\Desota
set manager_path_install=%desota_root_path%\DeManagerTools
:: - Model Execs
set manager_start="%UserProfile%\Desota\DeManagerTools\dist\Desota - Manager Tools.exe"
set manager_uninstall=%manager_path_install%\executables\Windows\demanagertools.uninstall.bat



:: -- Edit bellow if you're felling lucky ;) -- https://youtu.be/5NV6Rdv1a3I

:: - Program Installers
set python64=https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe
set python32=https://www.python.org/ftp/python/3.11.4/python-3.11.4.exe
set git64_portable=https://github.com/git-for-windows/git/releases/download/v2.41.0.windows.3/PortableGit-2.41.0.3-64-bit.7z.exe
set git32_portable=https://github.com/git-for-windows/git/releases/download/v2.41.0.windows.3/PortableGit-2.41.0.3-32-bit.7z.exe
set miniconda64=https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
set miniconda32=https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86.exe

:: - DeSOTA Services Manager Files
set stop_all_services=%desota_root_path%\Configs\Services\models_stopper.bat
set start_req_services=%desota_root_path%\Configs\Services\models_starter.bat

:: - .bat ANSI Colored CLI
set header=
set info=
set sucess=
set fail=
set ansi_end=
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
if "%version%" == "10.0" GOTO set_ansi_colors
if "%version%" == "11.0" GOTO set_ansi_colors
GOTO end_ansi_colors
:set_ansi_colors
for /F %%a in ('echo prompt $E ^| cmd') do (
  set "ESC=%%a"
)
set header=%ESC%[4;95m
set info_h1=%ESC%[93m
set info_h2=%ESC%[33m
set sucess=%ESC%[7;32m
set fail=%ESC%[7;31m
set ansi_end=%ESC%[0m
:end_ansi_colors

:: IPUT ARGS - /reinstall="overwrite model + remove service" ; /startmodel="Start Model Service"
:: SET arg1=/reinstall
:: SET arg2=/startmanager

ECHO %header%Welcome to DeSOTA - Task Manager Installer!%ansi_end%
ECHO %info_h1%Step 1/9 - Check Re-Instalation%ansi_end%

:: Re-instalation Check
IF EXIST %stop_all_services% (
    ECHO Stopping All Desota Services...
    call %stop_all_services%
)

IF NOT EXIST %manager_path_install% (
    ECHO %info_h2%New install%ansi_end%
    GOTO endofreinstall
)
ECHO %info_h2%Re-Instalation required%ansi_end%

ECHO Start Uninstalation...
call %manager_uninstall% /Q
IF EXIST %manager_path_install% (
    GOTO EOF_IN_noTimeOUT
) ELSE (
    ECHO %sucess%Uninstalation Sucess%ansi_end%
)
:endofreinstall


ECHO %info_h1%Step 2/9 - Create Project Folder%ansi_end%
:: Create Project Folder
mkdir %manager_path_install% > NUL 2>NUL
call cd %manager_path_install%

ECHO %info_h1%Step 3/9 - Install Python%ansi_end%
:: Install Python if Required
python --version 3 > NUL 2>NUL
IF errorlevel 1 (
    python3 --version 3 > NUL 2>NUL
    IF errorlevel 1 (
        IF NOT EXIST %UserProfile%\Desota\Portables\python3 (
            GOTO installpython
        )
    )
)
goto skipinstallpython
:installpython
ECHO %info_h2%Installing Python...%ansi_end%
call mkdir %UserProfile%\Desota\Portables > NUL 2>NUL
IF %PROCESSOR_ARCHITECTURE%==AMD64 powershell -command "Invoke-WebRequest -Uri %python64% -OutFile ~\python3_installer.exe" && start /B /WAIT %UserProfile%\python3_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 TargetDir=%UserProfile%\Desota\Portables\python3 && del %UserProfile%\python3_installer.exe && goto skipinstallpython
IF %PROCESSOR_ARCHITECTURE%==x86 powershell -command "Invoke-WebRequest -Uri %python32% -OutFile ~\python3_installer.exe" && start /B /WAIT %UserProfile%\python3_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 TargetDir=%UserProfile%\Desota\Portables\python3 && del %UserProfile%\python3_installer.exe && goto skipinstallpython
IF NOT EXIST %UserProfile%\Desota\Portables\python3 (
    ECHO %fail%Python Instalation Fail - check https://www.python.org/downloads/windows/%ansi_end%
    GOTO EOF_IN
)
ELSE (
    ECHO %sucess%Python Instalation Sucess%ansi_end%
)
:skipinstallpython

ECHO %info_h1%Step 4/9 - Clone Project from GitHub%ansi_end%
:: GIT MODEL CLONE
git --version 3  > NUL 2>NUL
IF NOT errorlevel 1 (
    ::  Clone Descraper Repository
    call git clone --branch %manager_git_branch% %manager_git% .  > NUL 2>NUL
    GOTO endgitclonemodel
)
:: PORTABLE GIT MODEL CLONE
:: Install Portable Git
call mkdir %UserProfile%\Desota\Portables  > NUL 2>NUL
IF EXIST %UserProfile%\Desota\Portables\PortableGit GOTO clonerep

%info_h2%Downloading Portable Git...%ansi_end%
IF %PROCESSOR_ARCHITECTURE%==AMD64 powershell -command "Invoke-WebRequest -Uri %git64_portable% -OutFile ~\Desota\Portables\git_installer.exe" && start /B /WAIT %UserProfile%\Desota\Portables\git_installer.exe -o"%UserProfile%\Desota\Portables\PortableGit" -y && del %UserProfile%\Desota\Portables\git_installer.exe && goto clonerep
IF %PROCESSOR_ARCHITECTURE%==x86 powershell -command "Invoke-WebRequest -Uri %git32_portable% -OutFile ~\Desota\Portables\git_installer.exe" && start /B /WAIT %UserProfile%\Desota\Portables\git_installer.exe -o"%UserProfile%\Desota\Portables\PortableGit" && del %UserProfile%\Desota\Portables\git_installer.exe && goto clonerep

:clonerep
ECHO %info_h2%Cloning Project Repository...%ansi_end%
call %UserProfile%\Desota\Portables\PortableGit\bin\git.exe clone --branch %manager_git_branch% %manager_git% .  > NUL 2>NUL
:endgitclonemodel

ECHO %info_h1%Step 5/9 - Create Virtual Environment for Project%ansi_end%
:: Move into Project Folder
call mkdir %UserProfile%\Desota\Portables  > NUL 2>NUL
IF NOT EXIST %UserProfile%\Desota\Portables\miniconda3\condabin\conda.bat goto installminiconda
:: Install Conda if Required
goto skipinstallminiconda
:installminiconda
ECHO %info_h2%Downloading Portable MiniConda...%ansi_end%
IF %PROCESSOR_ARCHITECTURE%==AMD64 powershell -command "Invoke-WebRequest -Uri %miniconda64% -OutFile ~\miniconda_installer.exe" && start /B /WAIT %UserProfile%\miniconda_installer.exe /InstallationType=JustMe /AddToPath=0 /RegisterPython=0 /S /D=%UserProfile%\Desota\Portables\miniconda3 && del %UserProfile%\miniconda_installer.exe && goto skipinstallminiconda
IF %PROCESSOR_ARCHITECTURE%==x86 powershell -command "Invoke-WebRequest -Uri %miniconda32% -OutFile ~\miniconda_installer.exe" && start /B /WAIT %UserProfile%\miniconda_installer.exe /InstallationType=JustMe /AddToPath=0 /RegisterPython=0 /S /D=%UserProfile%\Desota\Portables\miniconda3 && del %UserProfile%\miniconda_installer.exe && && goto skipinstallminiconda
:skipinstallminiconda


:: Create/Activate Conda Virtual Environment
ECHO %info_h2%Creating MiniConda Environment...%ansi_end%
call %UserProfile%\Desota\Portables\miniconda3\condabin\conda create --prefix ./env python=3.11 -y  > NUL 2>NUL
call %UserProfile%\Desota\Portables\miniconda3\condabin\conda activate ./env  > NUL 2>NUL
call %UserProfile%\Desota\Portables\miniconda3\condabin\conda install pip -y > NUL 2>NUL

:: Install required Libraries
ECHO %info_h1%Step 6/9 - Install Project Packages%ansi_end%
call pip install -r requirements.txt  > NUL 2>NUL
pip freeze

:: Create App EXE
ECHO %info_h1%Step 7/9 - Create APP .EXE%ansi_end%

:: If you're working on this, clearly you know more than me!
:: inspired in https://pythonassets.com/posts/create-executable-file-with-pyinstaller-cx_freeze-py2exe/
:: doc: https://cx-freeze.readthedocs.io/en/stable/script.html
cxfreeze -c app.py --base-name=Win32GUI --target-dir dist --target-name="Desota - Manager Tools" --icon=icon.ico > NUL
::debug
::cxfreeze -c app.py --target-dir dist --target-name="Desota - Manager Tools" --icon=icon.ico > NUL 

:: Dectivate Conda Virtual Environment
call %UserProfile%\Desota\Portables\miniconda3\condabin\conda deactivate  > NUL 2>NUL

:: Create App ShortCut
ECHO %info_h2%Creating APP Desktop Shortcut...%ansi_end%
IF EXIST "%HOMEDRIVE%%HOMEPATH%\Desktop\Desota - Manager Tools.lnk" (
	del "%HOMEDRIVE%%HOMEPATH%\Desktop\Desota - Manager Tools.lnk"
)
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%HOMEDRIVE%%HOMEPATH%\Desktop\Desota - Manager Tools.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = %manager_start%  >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript CreateShortcut.vbs  > NUL 2>NUL
del CreateShortcut.vbs  > NUL 2>NUL

:: Create DeSOTA Configs
ECHO %info_h1%Step 8/9 - DeSOTA Configurations%ansi_end%
ECHO %info_h2%Creating DeSOTA Configs...%ansi_end%
mkdir %desota_root_path%\Configs > NUL 2>NUL
IF NOT EXIST %desota_root_path%\Configs\user.config.yaml (
    call copy %manager_path_install%\Assets\user.config_template.yaml %desota_root_path%\Configs\user.config.yaml  > NUL 2>NUL
    call %manager_path_install%\env\python %manager_path_install%\Tools\SetUserConfigs.py --key system --value win  > NUL 2>NUL
)


ECHO %info_h1%Step 9/9 - End of Installer%ansi_end%

ECHO %sucess%Starting DeSOTA - Manager Tools%ansi_end%
ECHO %info_h1%You can close this window!%ansi_end%
call %manager_start%

ECHO %info_h1%This window will close in 30 secs...%ansi_end%
:EOF_IN
call timeout 30
:EOF_IN_noTimeOUT
exit