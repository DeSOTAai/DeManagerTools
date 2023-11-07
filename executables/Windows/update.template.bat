@ECHO OFF
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

ECHO Upgrading DeManagerTools to version: __version__ >> __demanager_log__
ECHO %header%Welcome to this fresh upgrade%ansi_end%
ECHO    program name   : DeSOTA - Manager Tools
ECHO    program version: __version__

:: QUIET UNISTALL

:: Download Program : meanwhile Exe has been closed for project delete (why i don delete first) 
ECHO.
ECHO %info_h1%Downloading Program%ansi_end%
powershell -command "Invoke-WebRequest -Uri __download_url__ -OutFile __tmp_compress_file__ -erroraction 'silentlycontinue'" >NUL 2>NUL
ECHO %sucess%Done%ansi_end%

:: Create BackUP:
ECHO.
ECHO %info_h1%Creating Program BackUP%ansi_end%
xcopy __program_dir__ __backup_dir__ /E /H /C /I >NUL 2>NUL
ECHO %sucess%Done%ansi_end%

:: Delete Project Folder
ECHO.
ECHO %info_h1%Removing Program%ansi_end%
IF EXIST __program_dir__ rmdir /S /Q __program_dir__ >NUL 2>NUL

:: Check if folder still exist
IF EXIST __program_dir__ (
  ECHO %fail%Done%ansi_end%
)
IF NOT EXIST __program_dir__ (
  ECHO %sucess%Done%ansi_end%
)

:: Uncompress Program
ECHO.
ECHO %info_h1%Uncompressing Download%ansi_end%
mkdir __program_dir__ >NUL 2>NUL
tar -xzvf __tmp_compress_file__ -C __program_dir__ --strip-components 1 >NUL 2>NUL
del __tmp_compress_file__
ECHO %sucess%Done%ansi_end%

:: Start Program
ECHO.
ECHO %info_h1%Starting Program%ansi_end%
ECHO %info_h1%WARNING: DON'T CLOSE THIS TERMINAL!%ansi_end%
ECHO %sucess%Configurations ongoing%ansi_end%
__program_exe__
IF errorlevel 1 GOTO upgrade_error
ECHO %sucess%Done%ansi_end%
ECHO Upgrading DeManagerTools v__version__ : SUCESS >> __demanager_log__
IF EXIST __backup_dir__ rmdir /S /Q __backup_dir__ >NUL 2>NUL
::retrieved from https://stackoverflow.com/a/20333152
(goto) 2>nul & del "%~f0" & exit

:upgrade_error
ECHO %fail%Fail%ansi_end%
ECHO Upgrading DeManagerTools v__version__ : FAIL >> __demanager_log__

:: Regress to BackUP
ECHO.
ECHO %info_h1%Regress to Previous Version%ansi_end%
IF EXIST __program_dir__ rmdir /S /Q __program_dir__ >NUL 2>NUL
move /Y __backup_dir__ __program_dir__
__program_exe__
IF errorlevel 1 (
  ECHO %fail%Regress to Previous Version Error%ansi_end%
  ECHO   Tip: Re-Start your Computer then run this file 
  ECHO        __upgrade_path__
  PAUSE
  exit
)
IF EXIST __backup_dir__ rmdir /S /Q __program_dir__ >NUL 2>NUL
exit