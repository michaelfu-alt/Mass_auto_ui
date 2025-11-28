# Mass Auto UI - 快速开始指南

## 🚀 从 Git Clone 到打包的完整流程

### 1️⃣ 克隆仓库

```bash
git clone <repository_url>
cd Mass_auto_ui
```

### 2️⃣ 设置环境（自动）

**Windows 命令提示符:**
```cmd
setup_env.bat
```

**PowerShell:**
```powershell
.\setup_env.ps1
```

脚本会自动：
- ✅ 创建虚拟环境 `venv`
- ✅ 使用清华镜像升级 pip
- ✅ 使用清华镜像安装所有依赖

### 3️⃣ 生成应用图标

```cmd
# 激活虚拟环境（如果未激活）
venv\Scripts\activate

# 生成图标
python generate_icon.py
```

这将生成 `resources/icon.ico`（橘红色背景，白色 "Auto PV Mass" 文字）

### 4️⃣ 打包应用

**使用批处理脚本:**
```cmd
build.bat
```

**使用 PowerShell 脚本:**
```powershell
.\build.ps1
```

打包脚本会自动：
- ✅ 检查图标是否存在（不存在则自动生成）
- ✅ 检查并安装 PyInstaller（使用清华镜像）
- ✅ 清理旧的构建文件
- ✅ 执行打包（onedir 模式）

### 5️⃣ 运行打包后的应用

打包完成后，可执行文件位于：
```
dist\Mass_Auto_UI\Mass_Auto_UI.exe
```

双击运行即可。

## 📋 重要说明

### 打包模式
- ✅ **onedir 模式**：输出为目录，包含 exe 和所有依赖文件
- 📂 输出目录：`dist/Mass_Auto_UI/`
- 🎨 应用图标：已配置为 `resources/icon.ico`

### 清华镜像使用
所有 pip 安装命令都使用清华镜像：
```
https://pypi.tuna.tsinghua.edu.cn/simple
```

### 虚拟环境
- 📦 虚拟环境目录：`venv/`
- 🔧 激活方式：
  - CMD: `venv\Scripts\activate`
  - PowerShell: `.\venv\Scripts\Activate.ps1`

## ⚠️ 常见问题

### PowerShell 执行策略错误
如果遇到执行策略限制，运行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 图标生成失败
确保已安装 Pillow：
```cmd
pip install Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 打包失败
1. 检查虚拟环境是否已激活
2. 检查所有依赖是否已安装
3. 检查图标文件是否存在

## 📚 更多信息

详细文档请参考：
- `BUILD_GUIDE.md` - 完整的构建指南
- `readme.md` - 项目功能说明

---

**最后更新**: 2025-01-XX

