@ECHO OFF
cls


:: Instalation VARS
:: Model GIT
set manager_git=https://github.com/DeSOTAai/DeManagerTools.git
set manager_git_branch=main
:: - Model Path
set manager_path_install=%UserProfile%\Desota\DeManagerTools
set manager_path_dev=%UserProfile%\Documents\Projetos\DeSOTA\DeManagerTools
:: - Model Execs
set manager_start="%manager_path_install%\dist\Desota-ManagerTools.exe"
set manager_uninstall=%manager_path_install%\executables\Windows\demanagertools.uninstall.bat



:: -- Edit bellow if you're felling lucky ;) -- https://youtu.be/5NV6Rdv1a3I

:: - Program Installers
set python64=https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe
set python32=https://www.python.org/ftp/python/3.11.4/python-3.11.4.exe
set git64_portable=https://github.com/git-for-windows/git/releases/download/v2.41.0.windows.3/PortableGit-2.41.0.3-64-bit.7z.exe
set git32_portable=https://github.com/git-for-windows/git/releases/download/v2.41.0.windows.3/PortableGit-2.41.0.3-32-bit.7z.exe
set miniconda64=https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
set miniconda32=https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86.exe
set ressourcehacker=http://www.angusj.com/resourcehacker/resource_hacker.zip

:: - .bat ANSI Colored CLS
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
ECHO %info_h1%Step 1 - Check Re-Instalation%ansi_end%

:: Re-instalation Check
IF NOT EXIST %manager_path_install% (
    ECHO %info_h2%New install%ansi_end%
    GOTO endofreinstall
)
ECHO %info_h2%Re-Instalation required - Start Uninstall...%ansi_end%
call %manager_uninstall% /Q
IF EXIST %manager_path_install% (
    ECHO %fail%Re-Instalation Fail - Try Again after Rebooting PC%ansi_end%
    GOTO EOF_IN
)
ELSE (
    ECHO %sucess%Uninstalation Sucess%ansi_end%
)
:endofreinstall


ECHO %info_h1%Step 2 - Create Project Folder%ansi_end%
:: Create Project Folder
mkdir %manager_path_install%
call cd %manager_path_install%

ECHO %info_h1%Step 3 - Install Python%ansi_end%
:: Install Python if Required
python --version 3>NUL
IF errorlevel 1 (
    python3 --version 3>NUL
    IF errorlevel 1 (
        IF NOT EXIST %UserProfile%\Desota\Portables\python3 (
            GOTO installpython
        )
    )
)
goto skipinstallpython
:installpython
ECHO %info_h2%Installing Python...%ansi_end%
call mkdir %UserProfile%\Desota\Portables
IF %PROCESSOR_ARCHITECTURE%==AMD64 powershell -command "Invoke-WebRequest -Uri %python64% -OutFile ~\python3_installer.exe" && start /B /WAIT %UserProfile%\python3_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 TargetDir=%UserProfile%\Desota\Portables\python3 && del %UserProfile%\python3_installer.exe && goto skipinstallpython
IF %PROCESSOR_ARCHITECTURE%==x86 powershell -command "Invoke-WebRequest -Uri %python32% -OutFile ~\python3_installer.exe" && start /B /WAIT %UserProfile%\python3_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 TargetDir=%UserProfile%\Desota\Portables\python3 && del %UserProfile%\python3_installer.exe && goto skipinstallpython
IF NOT EXIST %UserProfile%\Desota\Portables\python3 (
    ECHO %fail%Python Instalation Fail - check https://www.python.org/downloads/windows/%ansi_end%
    PAUSE
    GOTO EOF_IN
)
ELSE (
    ECHO %sucess%Python Instalation Sucess%ansi_end%
)
:skipinstallpython

ECHO %info_h1%Step 4 - Clone Project from GitHub%ansi_end%
:: GIT MODEL CLONE
git --version 3>NUL
IF NOT errorlevel 1 (
    ::  Clone Descraper Repository
    call git clone --branch %manager_git_branch% %manager_git% .
    GOTO endgitclonemodel
)
:: PORTABLE GIT MODEL CLONE
:: Install Portable Git
call mkdir %UserProfile%\Desota\Portables
IF EXIST %UserProfile%\Desota\Portables\PortableGit GOTO clonerep

%info_h2%Downloading Portable Git...%ansi_end%
IF %PROCESSOR_ARCHITECTURE%==AMD64 powershell -command "Invoke-WebRequest -Uri %git64_portable% -OutFile ~\Desota\Portables\git_installer.exe" && start /B /WAIT %UserProfile%\Desota\Portables\git_installer.exe -o"%UserProfile%\Desota\Portables\PortableGit" -y && del %UserProfile%\Desota\Portables\git_installer.exe && goto clonerep
IF %PROCESSOR_ARCHITECTURE%==x86 powershell -command "Invoke-WebRequest -Uri %git32_portable% -OutFile ~\Desota\Portables\git_installer.exe" && start /B /WAIT %UserProfile%\Desota\Portables\git_installer.exe -o"%UserProfile%\Desota\Portables\PortableGit" && del %UserProfile%\Desota\Portables\git_installer.exe && goto clonerep

:clonerep
ECHO %info_h2%Cloning Project Repository...%ansi_end%
call %UserProfile%\Desota\Portables\PortableGit\bin\git.exe clone --branch %manager_git_branch% %manager_git% .
:endgitclonemodel

ECHO %info_h1%Step 5 - Create Virtual Environment for Project%ansi_end%
:: Move into Project Folder
call mkdir %UserProfile%\Desota\Portables
IF NOT EXIST %UserProfile%\Desota\Portables\miniconda3\condabin\conda.bat goto installminiconda
:: Install Conda if Required
goto skipinstallminiconda
:installminiconda
ECHO %info_h2%Downloading Portable MiniConda...%ansi_end%
IF %PROCESSOR_ARCHITECTURE%==AMD64 powershell -command "Invoke-WebRequest -Uri %miniconda64% -OutFile %UserProfile%\miniconda_installer.exe" && start /B /WAIT %UserProfile%\miniconda_installer.exe /InstallationType=JustMe /AddToPath=0 /RegisterPython=0 /S /D=%UserProfile%\Desota\Portables\miniconda3 && del %UserProfile%\miniconda_installer.exe && goto skipinstallminiconda
IF %PROCESSOR_ARCHITECTURE%==x86 powershell -command "Invoke-WebRequest -Uri %miniconda32% -OutFile %UserProfile%\miniconda_installer.exe" && start /B /WAIT %UserProfile%\miniconda_installer.exe /InstallationType=JustMe /AddToPath=0 /RegisterPython=0 /S /D=%UserProfile%\Desota\Portables\miniconda3 && del %UserProfile%\miniconda_installer.exe && && goto skipinstallminiconda
:skipinstallminiconda


:: Create/Activate Conda Virtual Environment
ECHO %info_h2%Creating MiniConda Environment...%ansi_end%
call %UserProfile%\Desota\Portables\miniconda3\condabin\conda create --prefix ./env python=3.11 -y
call %UserProfile%\Desota\Portables\miniconda3\condabin\conda activate ./env

:: Install required Libraries
ECHO %info_h1%Step 6 - Install Project Libraries%ansi_end%
call pip install -r requirements.txt


:: Create App EXE
ECHO %info_h1%Step 7 - Create APP .EXE%ansi_end%
:: call pyinstaller -w -F --uac-admin -i "Assets/icon.ico" -n "DeSOTA - Manager Tools" app.py :: DEPRECATED
:: CREATE SED FILE - https://ss64.com/nt/iexpress-sed.html
ECHO %info_h2%Manipulation .SED file...%ansi_end%
start /B /WAIT %manager_path_install%\env\python %manager_path_install%\Tools\manipulate_sed_file.py
:: retrieved from https://stackoverflow.com/a/26797258
ECHO %info_h2%Creating App .EXE file...%ansi_end%
mkdir %manager_path_install%\dist
call iexpress /N %manager_path_install%\executables\Windows\demanagertools.iexpress.SED 
::TODO - Install ResourceHacker.exe - http://www.angusj.com/resourcehacker/#download
IF EXIST %UserProfile%\Desota\Portables\ressourcehacker\ResourceHacker.exe (
    goto EO_ressourcehacker 
)
ECHO %info_h2%Installing RessourceHacker - Edit .EXE icon...%ansi_end%
mkdir %UserProfile%\Desota\Portables\ressourcehacker 
call powershell -command "Invoke-WebRequest -Uri %ressourcehacker% -OutFile ~\Desota\Portables\ressourcehacker.zip" &&  tar -xzvf %UserProfile%\Desota\Portables\ressourcehacker.zip -C %UserProfile%\Desota\Portables\ressourcehacker && del %UserProfile%\Desota\Portables\ressourcehacker.zip

::TODO - edit following paths
:EO_ressourcehacker
ECHO %info_h2%Editing .EXE icon...%ansi_end%
call %UserProfile%\Desota\Portables\ressourcehacker\ResourceHacker.exe -open "%UserProfile%\Desota\DeManagerTools\dist\Desota-ManagerTools.exe" -save "%UserProfile%\Desota\DeManagerTools\dist\Desota-ManagerTools.exe" -action addskip -res "%UserProfile%\Desota\DeManagerTools\Assets\icon.ico" -mask ICONGROUP,MAINICON,

ECHO %info_h2%Creating APP Desktop Shortcut...%ansi_end%
call copy "%manager_path_install%\dist\Desota-ManagerTools.exe %UserProfile%\desktop

ECHO %sucess%Step 8 - Starting DeSOTA - Manager Tools%ansi_end%
call %manager_start%

:EOF_IN
ECHO %info_h1%END of Installer - The Window will close in 30 secs...%ansi_end%
call timeout 30
exit