@echo off
setlocal
title SHUVAM Recondition House v9 - Installer
set "SRC=%~dp0dist_v9\SHUVAM Recondition House v9"
set "DEST=%ProgramFiles%\SHUVAM Recondition House v9"
echo.
echo ============================================
echo  SHUVAM Recondition House v9 - Installer
echo ============================================
echo.
if not exist "%SRC%\SHUVAM Recondition House v9.exe" (
    echo ERROR: Source folder not found: %SRC%
    echo Please keep this install.bat next to the dist_v9 folder.
    pause
    exit /b 1
)
echo Installing to: %DEST%
if not exist "%DEST%" mkdir "%DEST%"
xcopy /E /I /Y "%SRC%\*" "%DEST%\" >nul
if errorlevel 1 (
    echo Install failed. Try running as Administrator.
    pause
    exit /b 1
)
echo Creating shortcuts...
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%DEST%\SHUVAM Recondition House v9.lnk'); $s.TargetPath='%DEST%\SHUVAM Recondition House v9.exe'; $s.WorkingDirectory='%DEST%'; $s.Save(); $d=$ws.CreateShortcut('%PUBLIC%\Desktop\SHUVAM Recondition House v9.lnk'); $d.TargetPath='%DEST%\SHUVAM Recondition House v9.exe'; $d.WorkingDirectory='%DEST%'; $d.Save(); $sm=$ws.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\SHUVAM Recondition House v9.lnk'); $sm.TargetPath='%DEST%\SHUVAM Recondition House v9.exe'; $sm.WorkingDirectory='%DEST%'; $sm.Save()"
echo.
echo Install complete!
echo Launching SHUVAM Recondition House v9 ...
start "" "%DEST%\SHUVAM Recondition House v9.exe"
pause
