@echo off
cd /d C:\ALMACEN\ClaudeElCorreo

echo Cerrando procesos anteriores...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
taskkill /f /im ElCorreo.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo Limpiando cache...
if exist __pycache__ rmdir /s /q __pycache__

echo Arrancando servidor...
set RENDER=1
start "" "http://127.0.0.1:5000"
python app.py
pause
