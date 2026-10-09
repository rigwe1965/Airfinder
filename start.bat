@echo off
rem Double-click to start the Airfinder server (Flask serves frontend + API on one port).
cd /d "%~dp0"

if not exist .env (
  echo Missing .env - copy .env.example to .env and set SUPER_ADMIN_EMAIL / SUPER_ADMIN_PASSWORD.
  pause
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found on PATH.
  pause
  exit /b 1
)

rem Install dependencies only when requirements.txt changed (psycopg2 is Postgres/Render only)
if not exist .deps_installed goto install
for /f %%i in ('powershell -nologo -noprofile -c "if ((Get-Item requirements.txt).LastWriteTime -gt (Get-Item .deps_installed).LastWriteTime) {1} else {0}"') do if "%%i"=="1" goto install
goto run

:install
echo Installing dependencies...
findstr /v /b /i "psycopg2" requirements.txt > .requirements.local.txt
python -m pip install -q -r .requirements.local.txt
if errorlevel 1 (
  pause
  exit /b 1
)
type nul > .deps_installed

:run
echo Starting Airfinder at http://localhost:5000  (close this window or Ctrl+C to stop)
start "" http://localhost:5000
python run.py
pause
