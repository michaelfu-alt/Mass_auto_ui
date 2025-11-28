@echo off
chcp 65001 >nul
echo ====================================
echo Mass Auto UI - Windows 打包脚本
echo ====================================
echo.

cd /d "%~dp0"

REM 检查虚拟环境
if not exist "venv\Scripts\python.exe" (
    echo ❌ 错误：未找到虚拟环境！
    echo 请先创建虚拟环境: python -m venv venv
    pause
    exit /b 1
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 检查图标文件
echo 🎨 检查应用图标...
if not exist "resources\icon.ico" (
    echo ⚠️  图标文件不存在，正在生成...
    python generate_icon.py
    if errorlevel 1 (
        echo ❌ 图标生成失败！请确保已安装 Pillow: pip install Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple
        pause
        exit /b 1
    )
)

REM 检查 PyInstaller
echo 📦 检查 PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 📥 安装 PyInstaller（使用清华镜像）...
    pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
)

REM 清理旧的构建文件
echo 🧹 清理旧的构建文件...
if exist "build" (
    rmdir /s /q build
)
if exist "dist" (
    rmdir /s /q dist
)

REM 开始打包
echo.
echo 🔨 开始打包应用程序...
echo.
pyinstaller Mass_auto_ui.spec --clean

REM 检查打包结果
if errorlevel 1 (
    echo.
    echo ❌ 打包失败！请检查错误信息。
    pause
    exit /b 1
)

echo.
echo ✅ 打包完成！
echo 📂 输出目录: dist\Mass_Auto_UI\
echo 🚀 可执行文件: dist\Mass_Auto_UI\Mass_Auto_UI.exe
echo.

REM 询问是否运行测试
set /p test_run="是否运行打包后的程序进行测试？(Y/N): "
if /i "%test_run%"=="Y" (
    echo.
    echo 🧪 启动测试...
    echo.
    start "" "dist\Mass_Auto_UI\Mass_Auto_UI.exe"
)

echo.
echo 按任意键退出...
pause >nul

