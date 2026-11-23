@echo off
setlocal
set "DST=%USERPROFILE%\.claude\skills\ai-blender-animation-skill"
echo Installing ai-blender-animation-skill to %DST% ...
if not exist "%DST%" mkdir "%DST%"
xcopy "%~dp0..\skills\ai-blender-animation-skill\*" "%DST%\" /E /I /Y /Q >nul
if errorlevel 1 (echo Install failed. & pause & exit /b 1)
echo Done! Claude Code restart karo.
pause
