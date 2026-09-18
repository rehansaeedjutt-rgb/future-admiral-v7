@echo off
cd /d "%~dp0"
git add .
git status
echo.
set /p msg="Commit message: "
git commit -m "%msg%"
git push origin main
pause