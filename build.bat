@echo off
setlocal
cd /d "%~dp0" || exit /b 1

rem Build Scientific Cat as a PyInstaller onedir application.
rem Usage:
rem   build.bat          Build dist\ScientificCat\ScientificCat.exe
rem   build.bat --help   Show this help.

if /i "%~1"=="--help" goto :help
if not "%~1"=="" (
    echo [ERROR] Unknown argument: %~1
    goto :help_error
)

set "VENV_PY=.venv\Scripts\python.exe"

echo ============================================
echo  Scientific Cat - Windows build
echo ============================================

if not exist "%VENV_PY%" (
    echo [ERROR] Virtual environment was not found.
    echo Run setup_env.bat first.
    goto :error
)

for %%D in (
    "assets\styles"
    "assets\schema"
    "assets\katex"
    "assets\templates"
    "assets\icons"
) do (
    if not exist "%%~D" (
        echo [ERROR] Required resource was not found: %%~D
        goto :error
    )
)

"%VENV_PY%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller is not installed.
    echo Run setup_env.bat first.
    goto :error
)

echo Building application...
"%VENV_PY%" -m PyInstaller --noconfirm --clean ^
    --name ScientificCat ^
    --windowed ^
    --add-data "assets\styles;assets\styles" ^
    --add-data "assets\schema;assets\schema" ^
    --add-data "assets\katex;assets\katex" ^
    --add-data "assets\templates;assets\templates" ^
    --add-data "assets\icons;assets\icons" ^
    --collect-data matplotlib ^
    --collect-submodules mistletoe ^
    --hidden-import lxml._elementpath ^
    --hidden-import matplotlib.backends.backend_agg ^
    main.py
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    goto :error
)

echo Running frozen smoke test...
"dist\ScientificCat\ScientificCat.exe" --smoke-test
if errorlevel 1 (
    echo [ERROR] Frozen application smoke test failed.
    goto :error
)

echo.
echo Build completed successfully.
echo Executable: dist\ScientificCat\ScientificCat.exe
endlocal
exit /b 0

:help
echo Usage: build.bat [--help]
echo.
echo Creates dist\ScientificCat\ScientificCat.exe with bundled resources.
endlocal
exit /b 0

:help_error
echo Usage: build.bat [--help]

:error
echo.
echo Build failed.
endlocal
exit /b 1