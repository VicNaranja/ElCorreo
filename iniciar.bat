@echo off
echo Iniciando El Correo News...
python -m pip install flask requests beautifulsoup4 lxml pywebview --quiet 2>nul
python app.py
pause
