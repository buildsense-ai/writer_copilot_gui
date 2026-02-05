@echo off
REM Paper-CLI Wrapper Script for Windows
REM Usage: run-paper.bat [command] [args...]

set "CLI_DIR=%~dp0"
set "CLI_DIR=%CLI_DIR:~0,-1%"
set "WORK_DIR=%CD%"

set "PYTHONPATH=%CLI_DIR%;%PYTHONPATH%"

if exist "%CLI_DIR%\.env" (
    for /f "usebackq tokens=1,* delims==" %%a in ("%CLI_DIR%\.env") do (
        set "%%a=%%b"
    )
)

cd /d "%WORK_DIR%"
python -m src.main %*

set EXIT_CODE=%ERRORLEVEL%
exit /b %EXIT_CODE%
