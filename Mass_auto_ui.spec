# -*- mode: python ; coding: utf-8 -*-

"""
Mass Auto UI - PyInstaller 打包配置文件
用于将 PV MassSpec 自动控制系统打包为 Windows 可执行文件
"""

import sys
import os

# 获取项目根目录
project_root = os.path.abspath('.')

# 需要包含的数据文件
added_files = [
    ('config', 'config'),  # 配置文件目录
    ('resources', 'resources'),  # 资源文件目录
]

# 只收集必要的隐藏导入（精简版 - 不使用 collect_all）
hiddenimports = [
    # 串口通信
    'serial',
    'serial.tools',
    'serial.tools.list_ports',
    
    # PySide6 核心模块（只包含必要的）
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    
    # Windows 自动化
    'pywinauto',
    'pywinauto.application',
    'pywinauto.findwindows',
    'pywinauto.controls',
    'pywinauto.controls.hwndwrapper',
    'pywinauto.controls.uiawrapper',
    'pywinauto.keyboard',
    
    # Windows API
    'win32api',
    'win32con',
    'win32gui',
    'win32com',
    'win32com.client',
    'pywintypes',
    'pythoncom',
    
    # 系统工具
    'psutil',
    'pyautogui',
    'pygetwindow',
    
    # COM 相关
    'comtypes',
    'comtypes.client',
]

block_cipher = None

a = Analysis(
    ['view\\main_ui_test.py'],
    pathex=[project_root],
    binaries=[],
    datas=added_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 大型科学计算库
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'Pillow',
        
        # 其他 UI 框架
        'tkinter',
        '_tkinter',
        'PyQt5',
        'PyQt6',
        
        # PySide6 不需要的模块（大幅减小体积）
        'PySide6.Qt3DAnimation',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DExtras',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DRender',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtGraphs',
        'PySide6.QtGraphsWidgets',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineQuick',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebChannel',
        'PySide6.QtWebSockets',
        'PySide6.QtWebView',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuick3D',
        'PySide6.QtQuickControls2',
        'PySide6.QtQuickWidgets',
        'PySide6.QtQuickTest',
        'PySide6.QtDesigner',
        'PySide6.QtHelp',
        'PySide6.QtLocation',
        'PySide6.QtPositioning',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'PySide6.QtSensors',
        'PySide6.QtSerialBus',
        'PySide6.QtSpatialAudio',
        'PySide6.QtRemoteObjects',
        'PySide6.QtScxml',
        'PySide6.QtStateMachine',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
        'PySide6.QtBluetooth',
        'PySide6.QtNfc',
        'PySide6.QtAxContainer',
        'PySide6.QtNetworkAuth',
        'PySide6.QtHttpServer',
        'PySide6.QtTextToSpeech',
        
        # 测试和文档
        'pytest',
        'test',
        'tests',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 过滤掉不需要的数据文件（QML、示例等）
def filter_datas(datas):
    """过滤掉 QML、示例等不需要的文件，大幅减小体积"""
    filtered = []
    exclude_patterns = [
        'qml',  # QML 文件
        'examples',  # 示例文件
        'translations',  # 翻译文件（如果不需要多语言）
    ]
    
    for dest, source, kind in datas:
        should_exclude = False
        for pattern in exclude_patterns:
            if pattern in dest.lower() or pattern in source.lower():
                should_exclude = True
                break
        
        if not should_exclude:
            filtered.append((dest, source, kind))
    
    return filtered

# 应用过滤
a.datas = filter_datas(a.datas)

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

