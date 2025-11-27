@echo off
chcp 65001 >nul
echo =====================================
echo 测试打包后的 Mass Auto UI 程序
echo =====================================
echo.

if not exist "dist\Mass_Auto_UI\Mass_Auto_UI.exe" (
    echo ❌ 错误：找不到打包后的程序！
    echo 请先运行 build.bat 进行打包。
    pause
    exit /b 1
)

echo 📂 打包位置: dist\Mass_Auto_UI\
echo 📊 打包大小: 约 655 MB
echo 📁 文件数量: 3700+ 个文件
echo.
echo 🚀 正在启动程序...
echo.

start "" "dist\Mass_Auto_UI\Mass_Auto_UI.exe"

echo ✅ 程序已启动！
echo.
echo 请检查以下功能：
echo   [1] 界面是否正常显示
echo   [2] 串口列表是否可以加载
echo   [3] 配置文件是否可以读取
echo   [4] 日志显示是否正常
echo   [5] 窗口控制功能是否正常
echo.
pause

