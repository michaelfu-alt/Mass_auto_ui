@echo off
chcp 65001 >nul
echo ====================================
echo Mass Auto UI - 环境设置脚本
echo ====================================
echo.

cd /d "%~dp0"

REM 检查 Python
echo 🔍 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到 Python！
    echo 请先安装 Python 3.8+ 
    pause
    exit /b 1
)

python --version
echo.

REM 创建虚拟环境
echo 📦 创建虚拟环境...
if exist "venv" (
    echo ⚠️  虚拟环境已存在，跳过创建
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ❌ 虚拟环境创建失败！
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
)
echo.

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

REM 升级 pip（使用清华镜像）
echo 📥 升级 pip（使用清华镜像）...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

REM 安装依赖（使用清华镜像）
echo 📦 安装依赖包（使用清华镜像）...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if errorlevel 1 (
    echo ❌ 依赖安装失败！
    pause
    exit /b 1
)

echo.
echo ✅ 环境设置完成！
echo.
echo 📝 下一步：
echo    1. 生成应用图标: python generate_icon.py
echo    2. 打包应用: build.bat
echo.
pause

