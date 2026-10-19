@echo off
rem Ejecuta la carpeta CRUD Mascota y genera los reportes en la carpeta reports
rem Requiere: npm install -g newman newman-reporter-htmlextra
cd /d "%~dp0"
if not exist reports mkdir reports
call newman run "Taller Petstore.postman_collection.json" ^
  -e "Petstore - QA.postman_environment.json" ^
  --folder "CRUD Mascota" ^
  -r cli,htmlextra,junit ^
  --reporter-htmlextra-export reports\reporte.html ^
  --reporter-junit-export reports\junit.xml
rem El codigo de salida indica si pasaron todos los tests (0 = todo bien)
exit /b %ERRORLEVEL%
