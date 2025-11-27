# -*- mode: python ; coding: utf-8 -*-

"""
Mass Auto UI - PyInstaller 打包配置文件
用于将 PV MassSpec 自动控制系统打包为 Windows 可执行文件
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules
import sys
import os

# 获取项目根目录
project_root = os.path.abspath('.')

# 收集所有必要的 PySide6 模块
pyside6_datas, pyside6_binaries, pyside6_hiddenimports = collect_all('PySide6')

# 收集 pywinauto 和相关模块
pywinauto_datas, pywinauto_binaries, pywinauto_hiddenimports = collect_all('pywinauto')
comtypes_hiddenimports = collect_submodules('comtypes')

# 需要包含的数据文件
added_files = [
    ('config', 'config'),  # 配置文件目录
    ('resources', 'resources'),  # 资源文件目录
]

# 收集所有隐藏导入
hiddenimports = [
    'serial',
    'serial.tools',
    'serial.tools.list_ports',
    'pywinauto',
    'pywinauto.application',
    'pywinauto.findwindows',
    'pywinauto.controls',
    'pywinauto.keyboard',
    'psutil',
    'pyautogui',
    'pygetwindow',
    'comtypes',
    'comtypes.client',
    'win32api',
    'win32con',
    'win32gui',
    'win32com',
    'win32com.client',
    'pywintypes',
    'pythoncom',
] + pyside6_hiddenimports + pywinauto_hiddenimports + comtypes_hiddenimports

# 合并所有数据文件
all_datas = added_files + pyside6_datas + pywinauto_datas

# 合并所有二进制文件
all_binaries = pyside6_binaries + pywinauto_binaries

block_cipher = None

a = Analysis(
    ['view\\main_ui_test.py'],
    pathex=[project_root],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
        '_tkinter',
        'PyQt5',  # 排除 PyQt5，只使用 PySide6
        'PyQt6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Mass_Auto_UI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 设置为 True 以显示控制台窗口用于调试
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 如果有图标文件，可以在这里指定
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Mass_Auto_UI',
)

