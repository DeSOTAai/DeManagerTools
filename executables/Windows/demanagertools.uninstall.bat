@ECHO OFF
:: Uninstalation VARS
:: - Model Path
set manager_path_un=%UserProfile%\Desota\DeManagerTools



:: -- Edit bellow if you're felling lucky ;) -- https://youtu.be/5NV6Rdv1a3I

:: IPUT ARGS - /Q=Quietly
SET arg1=/Q

:: - .bat ANSI Colored CLI
set header=
set info=
set sucess=
set fail=
set ansi_end=
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
if "%version%" == "10.0" GOTO set_ansi_colors_un
if "%version%" == "11.0" GOTO set_ansi_colors_un
GOTO end_ansi_colors_un
:set_ansi_colors_un
for /F %%a in ('echo prompt $E ^| cmd') do (
  set "ESC=%%a"
)
set header=%ESC%[4;95m
set info_h1=%ESC%[93m
set info_h2=%ESC%[33m
set sucess=%ESC%[7;32m
set fail=%ESC%[7;31m
set ansi_end=%ESC%[0m
:end_ansi_colors_un


:: Check if APP is running
IF EXIST %manager_path_un%\status.txt GOTO get_status_4_uninstall
GOTO start_manager_uninstall
:get_status_4_uninstall
set /p manager_status= < %manager_path_un%\status.txt
IF "%manager_status%" EQU "1" (
    ECHO %fail%Re-Instalation Fail - Close ` Desota - Manager Tools.exe ` before attempting to Re/Un-Install!!%ansi_end%
    call timeout 30
    GOTO EOF_MAN_UN
)
:start_manager_uninstall

:: Delete APP ShortCut
IF EXIST "%HOMEDRIVE%%HOMEPATH%\Desktop\Desota - Manager Tools.lnk" (
    del "%HOMEDRIVE%%HOMEPATH%\Desktop\Desota - Manager Tools.lnk" > NUL 2>NUL
)

IF "%1" EQU "" GOTO noargs
IF %1 EQU /Q (
    :: Delete Project Folder
    IF EXIST %manager_path_un% (
        rmdir /S /Q %manager_path_un%  > NUL 2>NUL
    ) 
    GOTO EOF_MAN_UN
)

:noargs
:: Delete Project Folder
IF EXIST %manager_path_un% (
    rmdir /S %manager_path_un%
    GOTO EOF_MAN_UN
)

:EOF_MAN_UN