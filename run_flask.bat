@echo off
cd /d "%~dp0"
call venv\Scripts\activate
echo.
echo  Starting AeroAnalytics...
echo  Opening http://localhost:5000
echo.
python flask_app/server.py
pause
