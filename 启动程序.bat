@echo off
chcp 65001 >nul
echo 正在启动 PV MassSpec 自动控制系统...
cd /d "%~dp0"
echo 使用虚拟环境: %~dp0venv\Scripts\python.exe
"%~dp0venv\Scripts\python.exe" "%~dp0view\main_ui_test.py"
pause

