@echo off
rem Busca Python instalado en el usuario (el "python" de WindowsApps es solo el atajo a la Store)
set "PY="
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if exist "%%D\python.exe" set "PY=%%D\python.exe"
if not defined PY for /d %%D in ("%ProgramFiles%\Python3*") do if exist "%%D\python.exe" set "PY=%%D\python.exe"
if not defined PY (
  echo No se encontro Python. Instalalo desde https://www.python.org/downloads/ y volve a ejecutar.
  pause
  exit /b 1
)
"%PY%" -c "import openpyxl" 2>nul || "%PY%" -m pip install openpyxl
cd /d "%~dp0"
"%PY%" matcheador.py
pause
