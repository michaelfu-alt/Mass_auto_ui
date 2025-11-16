# -*- coding: utf-8 -*-
"""
create_files.py
项目初始化脚本 —— 质谱自动化上位机 (Mass_Auto_Ui)
--------------------------------------------------
功能：
1. 自动创建完整项目结构；
2. 生成 requirements.txt；
3. 创建虚拟环境 venv；
4. 安装依赖；
5. 输出初始化完成提示。

执行方式：
    python create_files.py
"""

import os
import subprocess
import platform

# ========== 1. 定义目录结构 ==========
folders = [
    "controller",
    "view",
    "utils",
    "test",
    "logs",
    "config",
    "resources/icons",
    "data",
    "docs"
]

files = {
    "controller/serial_worker.py": "# 串口通信模块\n# 用于连接 CH340 串口并读取温度数据 TEMP=xxxx℃\n",
    "controller/massspec_runner.py": "# 质谱控制模块\n# 启动质谱软件并模拟点击“Start”按钮\n",
    "view/main_ui_test.py": "# 临时 UI 测试\n# 验证 PySide6 界面信号与布局刷新机制\n",
    "utils/logger.py": "# 日志记录模块\n# 提供 log(msg, level='INFO') 接口并写入 logs/\n",
    "utils/config_loader.py": "# 配置文件加载模块\n# 统一读取 config/app_config.json 等配置文件\n",
    "test/test_serial.py": "# 串口独立测试脚本\n# 验证下位机温度数据读取稳定性\n",
    "test/test_massspec.py": "# 质谱控制测试脚本\n# 测试 subprocess 与 pyautogui 功能\n",
    "config/app_config.json": """{
    "serial_port": "COM3",
    "baud_rate": 9600,
    "trigger_temp": 50,
    "trigger_count": 2,
    "massspec_path": "C:/Program Files/MassSpec/massspec.exe"
}""",
    "config/ui_settings.json": """{
    "window_width": 500,
    "window_height": 400,
    "theme": "light"
}""",
    "resources/style.qss": """/* UI 样式表 */
QMainWindow {
    background-color: #f8f9fa;
}
QPushButton {
    background-color: #ff8800;
    color: white;
    border-radius: 6px;
    padding: 5px;
}
QPushButton:hover {
    background-color: #ff9900;
}
""",
    "docs/architecture.md": "# 项目架构说明\n\n包含：模块结构、数据流程、通信协议、UI设计逻辑。\n",
    "requirements.txt": """PySide6>=6.5.0
pyserial>=3.5
pyautogui>=0.9.54
pygetwindow>=0.0.9
psutil>=5.9.0
"""
}

gitignore_content = """# Python 缓存
__pycache__/
*.pyc

# 虚拟环境
venv/

# 日志与数据文件
logs/
data/

# 编译与打包产物
build/
dist/
*.spec

# IDE配置
.vscode/
.idea/
"""

# ========== 2. 创建文件夹结构 ==========
root_dir = os.path.dirname(os.path.abspath(__file__))
print(f"[INFO] 初始化项目结构于: {root_dir}")

for folder in folders:
    path = os.path.join(root_dir, folder)
    os.makedirs(path, exist_ok=True)
    print(f"[OK] 文件夹已创建: {folder}")

# ========== 3. 创建文件 ==========
for filepath, content in files.items():
    full_path = os.path.join(root_dir, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] 文件已创建: {filepath}")

# ========== 4. 创建 .gitignore ==========
gitignore_path = os.path.join(root_dir, ".gitignore")
if not os.path.exists(gitignore_path):
    with open(gitignore_path, "w", encoding="utf-8") as f:
        f.write(gitignore_content)
    print("[OK] .gitignore 文件已创建")
else:
    print("[SKIP] .gitignore 已存在")

# ========== 5. 创建虚拟环境 ==========
venv_path = os.path.join(root_dir, "venv")
if not os.path.exists(venv_path):
    print("[INFO] 正在创建虚拟环境...")
    subprocess.run(["python", "-m", "venv", "venv"])
    print("[OK] 虚拟环境已建立: venv")
else:
    print("[SKIP] 虚拟环境已存在")

# ========== 6. 安装依赖 ==========
print("[INFO] 正在安装依赖包...")
if platform.system() == "Windows":
    pip_path = os.path.join("venv", "Scripts", "pip")
else:
    pip_path = os.path.join("venv", "bin", "pip")

subprocess.run([pip_path, "install", "-r", "requirements.txt"])
print("[OK] 依赖安装完成")

# ========== 7. 初始化完成提示 ==========
print("\n✅ 项目初始化完成！目录结构如下：")
for folder in folders:
    print(f"📁 {folder}")

print("""
下一步建议：
1️⃣ 运行 test/test_serial.py 测试串口读取
2️⃣ 运行 test/test_massspec.py 测试质谱控制
3️⃣ 然后在 main.py 整合逻辑
4️⃣ 使用 logs/ 保存运行记录，config/ 管理参数配置
""")