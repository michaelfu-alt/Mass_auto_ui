# Mass Auto UI - 环境设置脚本 (PowerShell)
# 编码：UTF-8

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Mass Auto UI - 环境设置脚本" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 切换到脚本所在目录
Set-Location $PSScriptRoot

# 检查 Python
Write-Host "🔍 检查 Python 环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host $pythonVersion -ForegroundColor Green
} catch {
    Write-Host "❌ 错误：未找到 Python！" -ForegroundColor Red
    Write-Host "请先安装 Python 3.8+" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}
Write-Host ""

# 创建虚拟环境
Write-Host "📦 创建虚拟环境..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "⚠️  虚拟环境已存在，跳过创建" -ForegroundColor Yellow
} else {
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 虚拟环境创建失败！" -ForegroundColor Red
        Read-Host "按回车键退出"
        exit 1
    }
    Write-Host "✅ 虚拟环境创建成功" -ForegroundColor Green
}
Write-Host ""

# 激活虚拟环境
Write-Host "🔧 激活虚拟环境..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# 升级 pip（使用清华镜像）
Write-Host "📥 升级 pip（使用清华镜像）..." -ForegroundColor Yellow
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装依赖（使用清华镜像）
Write-Host "📦 安装依赖包（使用清华镜像）..." -ForegroundColor Yellow
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 依赖安装失败！" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Write-Host "✅ 环境设置完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📝 下一步：" -ForegroundColor Cyan
Write-Host "   1. 生成应用图标: python generate_icon.py" -ForegroundColor White
Write-Host "   2. 打包应用: .\build.ps1" -ForegroundColor White
Write-Host ""
Read-Host "按回车键退出"

