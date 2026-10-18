@echo off
setlocal
cd /d "%~dp0" || exit /b 1

rem Start Scientific Cat from the project virtual environment.
rem Usage:
rem   run.bat          Start the application.
rem   run.bat --help   Show this help.

if /i "%~1"=="--help" goto :help

set "VENV_PY=.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [ERROR] Virtual environment was not found.
    echo Run setup_env.bat first.
    endlocal
    exit /b 1
)

echo Starting Scientific Cat...
"%VENV_PY%" main.py %*
set "APP_EXIT=%ERRORLEVEL%"

if not "%APP_EXIT%"=="0" (
    echo.
    echo [ERROR] Scientific Cat exited with code %APP_EXIT%.
)

endlocal & exit /b %APP_EXIT%

:help
echo Usage: run.bat [application arguments]
echo.
echo Starts Scientific Cat with .venv\Scripts\python.exe.
endlocal
exit /b 0
