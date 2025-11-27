# Mass Auto UI - Windows 打包指南

## 📋 概述

本指南介绍如何将 Mass Auto UI（PV MassSpec 自动控制系统）打包为 Windows 独立可执行文件。

## 🔧 前置要求

1. **Python 环境**：Python 3.8+ （建议 3.10+）
2. **虚拟环境**：已创建并安装所有依赖
3. **PyInstaller**：打包工具（构建脚本会自动安装）

## 📦 打包文件说明

### 核心文件

- **`Mass_auto_ui.spec`** - PyInstaller 打包配置文件
- **`build.bat`** - Windows 批处理打包脚本
- **`build.ps1`** - PowerShell 打包脚本

### 配置说明

`Mass_auto_ui.spec` 文件包含以下配置：

- **入口文件**：`view\main_ui_test.py`
- **包含的数据**：
  - `config/` - 配置文件目录
  - `resources/` - 资源文件目录
- **隐藏导入**：
  - PySide6 相关模块
  - pywinauto 和 Windows 自动化模块
  - 串口通信模块
- **排除的模块**：
  - matplotlib, numpy, pandas 等不需要的大型库

## 🚀 打包步骤

### 方法 1：使用批处理脚本（推荐）

1. 打开命令提示符
2. 导航到项目根目录
3. 运行打包脚本：

```cmd
build.bat
```

### 方法 2：使用 PowerShell 脚本

1. 打开 PowerShell
2. 导航到项目根目录
3. 运行打包脚本：

```powershell
.\build.ps1
```

### 方法 3：手动打包

```cmd
# 激活虚拟环境
venv\Scripts\activate

# 安装 PyInstaller（如果未安装）
pip install pyinstaller

# 清理旧的构建文件
rmdir /s /q build dist

# 开始打包
pyinstaller Mass_auto_ui.spec --clean
```

## 📂 输出结构

打包完成后，会在项目根目录生成以下目录：

```
Mass_auto_ui/
├── build/              # 临时构建文件（可删除）
└── dist/
    └── Mass_Auto_UI/   # 最终输出目录
        ├── Mass_Auto_UI.exe    # 主程序
        ├── config/             # 配置文件
        ├── resources/          # 资源文件
        └── ... (其他依赖文件)
```

## ✅ 测试打包结果

### 基本测试

1. 导航到 `dist\Mass_Auto_UI\` 目录
2. 双击运行 `Mass_Auto_UI.exe`
3. 验证以下功能：
   - ✅ 界面正常显示
   - ✅ 串口列表正常加载
   - ✅ 配置文件正常读取
   - ✅ 日志正常显示

### 功能测试

1. **串口通信**：
   - 测试串口连接
   - 测试数据接收

2. **窗口控制**：
   - 测试 PV MassSpec 窗口识别
   - 测试 Recipe 加载

3. **配置管理**：
   - 测试保存/加载配置
   - 测试导入/导出设置

## ⚠️ 常见问题

### 问题 1：打包失败 - 缺少模块

**症状**：提示 `ModuleNotFoundError`

**解决方案**：
1. 检查 `Mass_auto_ui.spec` 中的 `hiddenimports` 列表
2. 添加缺失的模块到列表中
3. 重新运行打包脚本

### 问题 2：运行时找不到配置文件

**症状**：程序启动后无法加载配置

**解决方案**：
1. 确认 `config/` 目录已包含在 spec 文件的 `datas` 中
2. 检查配置文件路径是否正确
3. 重新打包

### 问题 3：程序启动后立即退出

**症状**：双击 exe 文件后，窗口闪退

**解决方案**：
1. 在 spec 文件中将 `console=True` 查看错误信息
2. 检查缺少的 DLL 或依赖
3. 使用 `--debug=all` 选项重新打包

### 问题 4：打包文件过大

**症状**：dist 目录超过 500MB

**解决方案**：
1. 检查 spec 文件中的 `excludes` 列表
2. 添加不需要的大型库（如 matplotlib, numpy）
3. 使用 UPX 压缩（已在 spec 中启用）

## 🔍 调试模式

如需启用详细的调试信息，修改 `Mass_auto_ui.spec`：

```python
exe = EXE(
    ...
    debug=True,      # 启用调试模式
    console=True,    # 显示控制台窗口
    ...
)
```

然后重新打包。

## 📝 版本控制

以下文件应该被版本控制：
- ✅ `Mass_auto_ui.spec`
- ✅ `build.bat`
- ✅ `build.ps1`
- ✅ `BUILD_GUIDE.md`

以下目录应该被忽略：
- ❌ `build/`
- ❌ `dist/`

## 🎯 优化建议

1. **减小文件大小**：
   - 移除不必要的依赖
   - 使用 `--onefile` 选项（可能影响启动速度）

2. **提高启动速度**：
   - 使用目录模式（当前配置）
   - 启用 UPX 压缩

3. **添加图标**：
   ```python
   exe = EXE(
       ...
       icon='resources/icon.ico',  # 添加应用图标
       ...
   )
   ```

## 📞 支持

如遇到其他问题，请检查：
1. PyInstaller 官方文档：https://pyinstaller.org
2. 项目 README 文档
3. 相关日志文件

---

**最后更新**: 2025-11-27
**版本**: 1.0

