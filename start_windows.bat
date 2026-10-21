@echo off
setlocal
cd /d "%~dp0"
if exist .venv\Scripts\python.exe goto run
where py >nul 2>nul
if errorlevel 1 goto python_fallback
py -3 -m venv .venv
goto check_env
:python_fallback
python -m venv .venv
:check_env
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
:run
.venv\Scripts\python.exe -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ required'"
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m glyphworld %*
if errorlevel 1 goto fail
exit /b 0
:fail
echo.
echo Falha. Instale Python 3.11+ e consulte README.md. Para reparar dependencias:
echo .venv\Scripts\python.exe -m pip install -r requirements.txt
pause
exit /b 1
