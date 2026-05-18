@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Installing PyInstaller if needed...
python -m pip install pyinstaller -q

echo.
echo Building BSpiski_Country_L7_Anti-Flood.exe ...
python -m PyInstaller ^
  --onefile ^
  --console ^
  --clean ^
  --noconfirm ^
  --name "BSpiski_Country_L7_Anti-Flood" ^
  --distpath "." ^
  --workpath "_pyinstaller_work" ^
  --specpath "_pyinstaller_work" ^
  "BSpiski_Country_L7_Anti-Flood.py"

if errorlevel 1 (
    echo Build FAILED.
    pause
    exit /b 1
)

echo.
echo OK: %~dp0BSpiski_Country_L7_Anti-Flood.exe
echo.
echo Run the exe only from this project folder layout:
echo   belie spiski\RUN\BSpiski_Country_L7_Anti-Flood.exe
echo   belie spiski\IP Database\ ...
echo   belie spiski\Language\    (ru.ini, en.ini, settings.ini)
echo   belie spiski\bspiski\     (created on run)
echo.
pause
