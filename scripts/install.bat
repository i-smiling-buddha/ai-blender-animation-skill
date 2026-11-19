@echo off
setlocal
set "DST=%USERPROFILE%\.claude\skills\ultimate-blender"
echo Installing ultimate-blender to %DST% ...
if not exist "%DST%" mkdir "%DST%"
xcopy "%~dp0..\skills\ultimate-blender\*" "%DST%\" /E /I /Y /Q >nul
if errorlevel 1 (echo Install failed. & pause & exit /b 1)
echo Done! Claude Code restart karo.
pause
