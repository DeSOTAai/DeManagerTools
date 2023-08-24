@ECHO OFF
:: VARS 
set manager_path_run=%userprofile%\Documents\Projetos\DeSOTA\DeManagerTools
:: Check if APP is allready open
tasklist /fi "ImageName eq Desota-ManagerTools.exe" /fo csv 2>NUL | find /I "desota-managertools.exe">NUL
IF "%ERRORLEVEL%"=="0" (
    GOTO EO_dmt-run
)
:: Go to Project Folder
call cd %manager_path_run%
:: Run Manager Tools
call %manager_path_run%\env\python %manager_path_run%\app.py
:EO_dmt-run
exit