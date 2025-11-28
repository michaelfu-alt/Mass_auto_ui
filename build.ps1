# Mass Auto UI - Windows 打包脚本 (PowerShell)
# 编码：UTF-8

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Mass Auto UI - Windows 打包脚本" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 切换到脚本所在目录
Set-Location $PSScriptRoot

# 检查虚拟环境
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "❌ 错误：未找到虚拟环境！" -ForegroundColor Red
    Write-Host "请先创建虚拟环境: python -m venv venv" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

# 激活虚拟环境
Write-Host "🔧 激活虚拟环境..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# 检查图标文件
Write-Host "🎨 检查应用图标..." -ForegroundColor Yellow
if (-not (Test-Path "resources\icon.ico")) {
    Write-Host "⚠️  图标文件不存在，正在生成..." -ForegroundColor Yellow
    & python generate_icon.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 图标生成失败！请确保已安装 Pillow: pip install Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple" -ForegroundColor Red
        Read-Host "按回车键退出"
        exit 1
    }
}

# 检查 PyInstaller
Write-Host "📦 检查 PyInstaller..." -ForegroundColor Yellow
try {
    & python -c "import PyInstaller" 2>$null
} catch {
    Write-Host "📥 安装 PyInstaller（使用清华镜像）..." -ForegroundColor Yellow
    & pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
}

# 清理旧的构建文件
Write-Host "🧹 清理旧的构建文件..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force
}
if (Test-Path "dist") {
    Remove-Item -Path "dist" -Recurse -Force
}

# 开始打包
Write-Host ""
Write-Host "🔨 开始打包应用程序..." -ForegroundColor Green
Write-Host ""

& pyinstaller Mass_auto_ui.spec --clean

# 检查打包结果
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ 打包失败！请检查错误信息。" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Write-Host "✅ 打包完成！" -ForegroundColor Green
Write-Host "📂 输出目录: dist\Mass_Auto_UI\" -ForegroundColor Cyan
Write-Host "🚀 可执行文件: dist\Mass_Auto_UI\Mass_Auto_UI.exe" -ForegroundColor Cyan
Write-Host ""

# 询问是否运行测试
$testRun = Read-Host "是否运行打包后的程序进行测试？(Y/N)"
if ($testRun -eq "Y" -or $testRun -eq "y") {
    Write-Host ""
    Write-Host "🧪 启动测试..." -ForegroundColor Yellow
    Write-Host ""
    Start-Process "dist\Mass_Auto_UI\Mass_Auto_UI.exe"
}

Write-Host ""
Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

