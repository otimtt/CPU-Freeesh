@echo off
echo ============================================
echo  CPU Freeesh -- Build Script
echo ============================================

where pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo Building executable...
pyinstaller ^
  --onefile ^
  --windowed ^
  --name "CPU Freeesh" ^
  --icon "assets\icon.ico" ^
  --add-data "config;config" ^
  --uac-admin ^
  cpu_freeesh.py

echo.
if exist "dist\CPU Freeesh.exe" (
    echo Build SUCCESS: dist\CPU Freeesh.exe
) else (
    echo Build FAILED. Check the output above.
)
pause
