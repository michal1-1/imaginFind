@echo off
cd /d "D:\fastApi"
call venv310\Scripts\activate.bat
python services\scan_new_images.py