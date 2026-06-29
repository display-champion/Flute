@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo みんレポ 差枚ランキングビューアを起動します...
python server.py
pause
