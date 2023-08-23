@ECHO OFF
:: Uninstalation VARS
:: - Model Path
set model_path=%UserProfile%\Desota\DeManagerTools


:: -- Edit bellow if you're felling lucky ;) -- https://youtu.be/5NV6Rdv1a3I

:: IPUT ARGS - /Q=Quietly
SET arg1=/Q

IF "%1" EQU "" GOTO noargs
IF %1 EQU /Q (
    :: Delete Project Folder
    IF EXIST %model_path% rmdir /S /Q %model_path%
    GOTO EOF_UN
)

:noargs
:: Delete Project Folder
IF EXIST %model_path% (
    rmdir /S %model_path%
    GOTO EOF_UN
)

:EOF_UN