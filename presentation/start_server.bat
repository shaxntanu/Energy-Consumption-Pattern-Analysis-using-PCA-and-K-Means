@echo off
echo Starting local server for presentation...
echo.
echo Open your browser and navigate to:
echo http://localhost:8000/index.html
echo.
echo Press Ctrl+C to stop the server
echo.
cd /d "%~dp0"
python -m http.server 8000
