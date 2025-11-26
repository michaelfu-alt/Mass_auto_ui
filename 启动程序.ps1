# PowerShell脚本 - 启动PV MassSpec自动控制系统
Write-Host "正在启动 PV MassSpec 自动控制系统..." -ForegroundColor Green

# 切换到脚本所在目录
Set-Location $PSScriptRoot

# 使用虚拟环境的Python
$pythonPath = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
$scriptPath = Join-Path $PSScriptRoot "view\main_ui_test.py"

Write-Host "Python路径: $pythonPath" -ForegroundColor Cyan

# 检查Python是否存在
if (Test-Path $pythonPath) {
    # 显示Python版本
    Write-Host "Python版本:" -ForegroundColor Cyan
    & $pythonPath --version
    
    # 运行程序
    Write-Host "`n启动主程序..." -ForegroundColor Green
    & $pythonPath $scriptPath
} else {
    Write-Host "错误: 未找到Python解释器" -ForegroundColor Red
    Write-Host "路径: $pythonPath" -ForegroundColor Red
}

# 保持窗口打开
Write-Host "`n程序已退出。按任意键继续..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

