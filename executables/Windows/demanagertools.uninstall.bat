@REM Uninstalation VARS
@REM - Model Path
set model_path=%UserProfile%\Desota\DeManagerTools


@REM -- Edit bellow if you're felling lucky ;) -- https://youtu.be/5NV6Rdv1a3I

@REM IPUT ARGS - /Q=Quietly
SET arg1=/Q

IF "%1" EQU "" GOTO noargs
IF %1 EQU /Q (
    @REM Delete Project Folder
    IF EXIST %model_path% rmdir /S /Q %model_path%
    GOTO EOF_UN
)

:noargs
@REM Delete Project Folder
IF EXIST %model_path% (
    rmdir /S %model_path%
    GOTO EOF_UN
)

:EOF_UN
@REM Inform Uninstall Completed
IF NOT EXIST %model_path% echo DeManagerTools Uninstalled!