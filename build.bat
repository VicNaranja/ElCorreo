@echo off
echo ============================================
echo  Empaquetando El Correo News con PyInstaller
echo ============================================

REM Cerrar ElCorreo si está en ejecución
taskkill /f /im ElCorreo.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Instalar dependencias si no están
python -m pip install flask requests beautifulsoup4 lxml pywebview pyinstaller --quiet

REM Limpiar TODOS los artefactos anteriores
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist ElCorreo.spec del /f /q ElCorreo.spec
if exist *.spec del /f /q *.spec

REM Empaquetar — siempre onefile
python -m PyInstaller ^
  --onefile ^
  --noconsole ^
  --icon elcorreo.ico ^
  --name ElCorreo ^
  --add-data "templates;templates" ^
  --add-data "static;static" ^
  --hidden-import flask ^
  --hidden-import jinja2 ^
  --hidden-import werkzeug ^
  --hidden-import bs4 ^
  --hidden-import lxml ^
  --hidden-import lxml.etree ^
  --hidden-import lxml._elementpath ^
  --hidden-import requests ^
  --hidden-import charset_normalizer ^
  --hidden-import webview ^
  --hidden-import webview.platforms.winforms ^
  --hidden-import webview.platforms.mshtml ^
  --collect-submodules webview ^
  app.py

echo.
if exist dist\ElCorreo.exe (
  echo  OK: dist\ElCorreo.exe generado correctamente.
  echo  Puedes copiar ese archivo a cualquier Windows y ejecutarlo.
) else (
  echo  ERROR: No se genero el ejecutable. Revisa los mensajes anteriores.
)
echo ============================================
pause
