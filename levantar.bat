@echo off
rem Levanta el servidor del taller y abre el deck en el navegador.
rem Uso: doble clic, o "levantar.bat 9000" para usar otro puerto.
cd /d "%~dp0"
set PUERTO=%1
if "%PUERTO%"=="" set PUERTO=8765

set PY=
where py >nul 2>nul && set PY=py -3
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set PY="%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not defined PY where python >nul 2>nul && set PY=python
if not defined PY (
  echo No se encontro Python. Instalalo desde https://www.python.org/downloads/ y vuelve a intentar.
  pause
  exit /b 1
)

rem Abre el navegador 2 segundos despues, cuando el servidor ya esta escuchando
start "" /b cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:%PUERTO%/index.html"
echo Taller en http://127.0.0.1:%PUERTO%/index.html  -  Ctrl+C o cerrar esta ventana para detenerlo.
%PY% servidor.py %PUERTO%
