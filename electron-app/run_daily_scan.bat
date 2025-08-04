@echo off
echo [%date% %time%] Starting daily scan... >> D:\fastApi\task_log.txt

REM Go to project directory
cd /d "D:\fastApi"

REM Activate virtual environment and run scan
call "D:\fastApi\venv310\Scripts\activate.bat"
python "D:\fastApi\services\scan_new_images.py" >> D:\fastApi\task_log.txt 2>&1

echo [%date% %time%] Scan completed with exit code: %ERRORLEVEL% >> D:\fastApi\task_log.txt

REM Exit with the same code
exit /b %ERRORLEVEL%