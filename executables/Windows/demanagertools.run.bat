@ECHO OFF
:: VARS 
set manager_path_run=%userprofile%\Desota\DeManagerTools
:: Go to Project Folder
call cd %manager_path_run%
:: Run Manager Tools
call %manager_path_run%\env\python %manager_path_run%\app.py
PAUSE