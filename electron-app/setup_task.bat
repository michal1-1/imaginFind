@echo off
setlocal enabledelayedexpansion

:: השלב הזה מוצא את המיקום של הקובץ
set "CURRENT_DIR=%~dp0"
set "SCRIPT_PATH=%CURRENT_DIR%run_daily_scan.bat"

:: הגדרות המשימה
set "TASK_NAME=ImaginFind_DailyScan"
set "TASK_TIME=02:00"

:: הסרת משימה ישנה אם קיימת
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

:: יצירת משימה חדשה שתורץ כל יום
schtasks /create ^
 /tn "%TASK_NAME%" ^
 /tr "\"%SCRIPT_PATH%\"" ^
 /sc daily ^
 /st %TASK_TIME% ^
 /rl HIGHEST ^
 /f

pause
