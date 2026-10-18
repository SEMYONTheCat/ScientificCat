@echo off
setlocal
cd /d "%~dp0" || exit /b 1

rem Scientific Cat environment setup.
rem Usage:
rem   setup_env.bat                  Install runtime and development dependencies.
rem   setup_env.bat --check          Install dependencies and run all quality checks.
rem   setup_env.bat --runtime-only   Install runtime dependencies only.
rem   setup_env.bat --help           Show this help.

set "VENV_DIR=.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "PYTHON_CMD="
set "RUN_CHECKS=0"
set "RUNTIME_ONLY=0"

:parse_args
if "%~1"=="" goto :args_done
if /i "%~1"=="--check" (
    set "RUN_CHECKS=1"
    shift
    goto :parse_args
)
if /i "%~1"=="--runtime-only" (
    set "RUNTIME_ONLY=1"
    shift
    goto :parse_args
)
if /i "%~1"=="--help" goto :help
echo [ERROR] Unknown argument: %~1
goto :help_error

:args_done
if "%RUN_CHECKS%"=="1" if "%RUNTIME_ONLY%"=="1" (
    echo [ERROR] --check cannot be combined with --runtime-only.
    goto :error
)

echo ============================================
echo  Scientific Cat - environment setup
echo ============================================

python --version >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=python"
if defined PYTHON_CMD goto :python_found

py -3 --version >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
    echo [ERROR] Python 3.10 or newer was not found.
    echo Install Python from https://www.python.org/downloads/
    goto :error
)

:python_found
echo [1/4] Python:
%PYTHON_CMD% --version

echo [2/4] Virtual environment:
if not exist "%VENV_PY%" (
    echo Creating %VENV_DIR% ...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 goto :error
) else (
    echo Using existing %VENV_DIR%.
)

echo [3/4] Installing dependencies:
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 goto :error
"%VENV_PY%" -m pip install --upgrade -r requirements.txt
if errorlevel 1 goto :error

if "%RUNTIME_ONLY%"=="0" (
    if exist requirements-dev.txt (
        "%VENV_PY%" -m pip install --upgrade -r requirements-dev.txt
        if errorlevel 1 goto :error
    )
)

echo [4/4] Environment is ready.
if "%RUN_CHECKS%"=="0" goto :success

echo.
echo Running Ruff...
"%VENV_PY%" -m ruff check .
if errorlevel 1 goto :checks_failed

echo Running mypy...
"%VENV_PY%" -m mypy --no-incremental core services
if errorlevel 1 goto :checks_failed

echo Running pytest...
set "QT_QPA_PLATFORM=offscreen"
"%VENV_PY%" -m pytest tests -q
set "TEST_EXIT=%ERRORLEVEL%"
set "QT_QPA_PLATFORM="
if not "%TEST_EXIT%"=="0" goto :checks_failed

echo.
echo All checks passed.
goto :success

:checks_failed
echo.
echo [ERROR] One or more quality checks failed.
goto :error

:success
echo.
echo Setup completed successfully.
echo Start the application with run.bat
endlocal
exit /b 0

:help
echo Usage: setup_env.bat [--check] [--runtime-only] [--help]
echo.
echo   --check          Run Ruff, mypy, and pytest after installation.
echo   --runtime-only   Do not install development dependencies.
echo   --help           Show this help.
endlocal
exit /b 0

:help_error
echo Usage: setup_env.bat [--check] [--runtime-only] [--help]

:error
echo.
echo Setup failed.
endlocal
exit /b 1