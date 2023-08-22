@REM  VARS 
for %%a in ("%~dp0..\..") do set "manager_path_run=%%~fa"
@REM Go to Project Folder
call cd %manager_path_run%
@REM Run DeRunner
call %manager_path_run%\env\python app.py
PAUSE