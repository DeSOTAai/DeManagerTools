@ECHO OFF
:: VARS 
::DEPLOY
set manager_path_run=%userprofile%\Desota\DeManagerTools	
::DEV
::set manager_path_run=%userprofile%\Documents\Projetos\DeSOTA\DeManagerTools

:: Check if APP is allready open
IF NOT EXIST %manager_path_run%\status.txt (
	echo 0 > %manager_path_run%\status.txt
)
set /p manager_status= < %manager_path_run%\status.txt
if %manager_status% EQU 1 (
	GOTO EO_dmt-reopen
)
:: Go to Project Folder
call cd %manager_path_run%
:: Run Manager Tools
echo 1 > %manager_path_run%\status.txt
call %manager_path_run%\env\python %manager_path_run%\app.py
:EO_dmt-run
echo 0 > %manager_path_run%\status.txt
:EO_dmt-reopen
PAUSE