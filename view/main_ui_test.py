import sys
import threading
import time
import serial
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, QFrame, QSizePolicy,
    QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QObject
import json, os
from pywinauto import Application, Desktop
from pywinauto.findwindows import ElementNotFoundError
import subprocess
import psutil

# 修复Windows控制台中文编码问题
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


START_BYTE = 0x73
STOP_BYTE = 0x65
CMD_TEMP_START = [0x01, 0x01]
CMD_TEMP_STOP = [0x00, 0x01]


def calc_checksum(data_bytes):
    checksum = sum(data_bytes) & 0xFFFF
    high = (checksum >> 8) & 0xFF
    low = checksum & 0xFF
    return high, low


def build_command(cmd_bytes):
    data_len = len(cmd_bytes)
    check_high, check_low = calc_checksum(cmd_bytes)
    return bytes([START_BYTE, data_len]) + bytes(cmd_bytes) + bytes([check_high, check_low, STOP_BYTE])


def parse_response(data: bytes):
    """解析下位机返回帧或TEMP文本"""
    lines = []
    i = 0
    while i < len(data):
        if data[i] == START_BYTE and (i + 1) < len(data):
            try:
                end_index = data.index(STOP_BYTE, i)
                frame = data[i:end_index + 1]
                payload = frame[2:-3]
                if b'OK' in payload:
                    lines.append("[OK] 收到下位机确认帧")
                i = end_index + 1
            except ValueError:
                break
        elif 0x20 <= data[i] <= 0x7E or data[i] in (0x0D, 0x0A):
            text_data = b""
            while i < len(data) and (0x20 <= data[i] <= 0x7E or data[i] in (0x0D, 0x0A)):
                text_data += bytes([data[i]])
                i += 1
            text_str = text_data.decode(errors='ignore').strip()
            if text_str:
                lines.append(f"[TEMP] {text_str}")
        else:
            i += 1
    return lines


class WindowMonitor(QObject):
    """监测和控制Recipe窗口和按钮"""
    window_status_changed = Signal(bool, str)  # (是否存在, 状态消息)
    
    def __init__(self):
        super().__init__()
        self.window_title = "Recipe: Setup Summary"  # 窗口名称关键字
        self.button_name = "Start Once"
        self.window = None
        self.window_uia = None  # UIA后端的窗口
        self.button = None
        self.backend = "win32"  # 默认使用win32查找窗口
        
    def check_window_exists(self):
        """检查窗口是否存在"""
        try:
            # 使用win32后端查找窗口
            print("\n使用 win32 后端查找窗口...")
            desktop = Desktop(backend="win32")
            windows = desktop.windows()
            
            for win in windows:
                try:
                    title = win.window_text()
                    if self.window_title in title:
                        self.window = win
                        print(f"\n=== 找到窗口 (win32): {title} ===")
                        self._print_window_controls()
                        
                        # 同时获取UIA后端的窗口对象
                        try:
                            print("\n尝试用 UIA 后端连接同一个窗口...")
                            desktop_uia = Desktop(backend="uia")
                            for win_uia in desktop_uia.windows():
                                if self.window_title in win_uia.window_text():
                                    self.window_uia = win_uia
                                    print(f"✅ 成功获取 UIA 窗口对象")
                                    break
                        except Exception as e:
                            print(f"⚠️ 获取UIA窗口失败: {e}")
                        
                        # 查找按钮
                        if self._check_button_exists():
                            self.window_status_changed.emit(True, f"✅ 找到窗口和按钮")
                            return True
                        else:
                            self.window_status_changed.emit(False, f"⚠️ 找到窗口但未找到按钮")
                            return False
                except Exception:
                    continue
                    
            self.window_status_changed.emit(False, "❌ 未找到Recipe窗口")
            return False
        except Exception as e:
            self.window_status_changed.emit(False, f"❌ 检查窗口失败: {e}")
            return False
    
    def _print_window_controls(self):
        """打印窗口的所有子控件信息（调试用）"""
        try:
            if not self.window:
                print("Window object is None")
                return
            
            print("\n" + "=" * 80)
            print(f"窗口标题: {self.window.window_text()}")
            print(f"窗口类名: {self.window.class_name()}")
            print("=" * 80)
            print("窗口的所有子控件:")
            print("-" * 80)
            
            children = self.window.children()
            print(f"总共找到 {len(children)} 个子控件\n")
            
            for idx, child in enumerate(children):
                try:
                    ctrl_type = child.friendly_class_name()
                    ctrl_title = child.window_text()
                    ctrl_id = child.control_id()
                    ctrl_class = child.class_name()
                    is_visible = child.is_visible()
                    is_enabled = child.is_enabled()
                    
                    print(f"控件 [{idx}]:")
                    print(f"  类型(Type):     {ctrl_type}")
                    print(f"  标题(Title):    '{ctrl_title}'")
                    print(f"  ID:             {ctrl_id}")
                    print(f"  类名(Class):    {ctrl_class}")
                    print(f"  可见(Visible):  {is_visible}")
                    print(f"  启用(Enabled):  {is_enabled}")
                    print("-" * 80)
                except Exception as e:
                    print(f"控件 [{idx}]: Error reading control - {e}")
                    print("-" * 80)
            
            print("=" * 80 + "\n")
        except Exception as e:
            print(f"Error printing controls: {e}")
    
    def get_controls_list(self):
        """获取窗口所有子控件信息列表"""
        controls_info = []
        try:
            if not self.window:
                return ["窗口不存在，请先检查窗口"]
            
            controls_info.append(f"窗口标题: {self.window.window_text()}")
            controls_info.append(f"窗口类名: {self.window.class_name()}\n")
            
            children = self.window.children()
            controls_info.append(f"找到 {len(children)} 个子控件:\n")
            controls_info.append("=" * 60 + "\n")
            
            for idx, child in enumerate(children):
                try:
                    ctrl_type = child.friendly_class_name()
                    ctrl_title = child.window_text()
                    ctrl_id = child.control_id()
                    ctrl_class = child.class_name()
                    is_visible = child.is_visible()
                    is_enabled = child.is_enabled()
                    
                    controls_info.append(f"控件 [{idx}]:")
                    controls_info.append(f"  类型(Type):     {ctrl_type}")
                    controls_info.append(f"  标题(Title):    '{ctrl_title}'")
                    controls_info.append(f"  ID:             {ctrl_id}")
                    controls_info.append(f"  类名(Class):    {ctrl_class}")
                    controls_info.append(f"  可见(Visible):  {is_visible}")
                    controls_info.append(f"  启用(Enabled):  {is_enabled}")
                    controls_info.append("-" * 60 + "\n")
                except Exception as e:
                    controls_info.append(f"[{idx}] Error: {e}\n")
            
            return controls_info
        except Exception as e:
            return [f"获取控件列表失败: {e}"]
    
    def _check_button_exists(self):
        """检查按钮是否存在"""
        try:
            print("\n" + "="*60)
            print("开始查找 'Start Once' 按钮...")
            print("="*60)
            
            # 方法1: 使用 UIA 后端查找按钮（推荐用于按钮操作）
            if self.window_uia:
                try:
                    print("方法1: 使用 UIA 后端查找按钮...")
                    self.button = self.window_uia.child_window(title="Start Once", control_type="Button")
                    if self.button.exists():
                        print("✅ 找到按钮 - UIA后端成功!")
                        self.backend = "uia"
                        return True
                except Exception as e:
                    print(f"⚠️ UIA方法1失败: {e}")
                
                # UIA方法2: 通过automation_id查找
                try:
                    print("方法2: UIA - 通过automation_id...")
                    buttons = self.window_uia.descendants(control_type="Button")
                    print(f"  找到 {len(buttons)} 个Button控件")
                    for btn in buttons:
                        try:
                            btn_name = btn.window_text()
                            if btn_name == "Start Once":
                                self.button = btn
                                print(f"✅ 找到按钮 - UIA遍历成功: '{btn_name}'")
                                self.backend = "uia"
                                return True
                        except:
                            continue
                except Exception as e:
                    print(f"⚠️ UIA方法2失败: {e}")
            
            # 方法3: Win32后端 - 遍历所有子控件
            if self.window:
                try:
                    print("\n方法3: Win32 - 遍历所有子控件...")
                    children = self.window.children()
                    print(f"  窗口共有 {len(children)} 个子控件")
                    
                    for idx, child in enumerate(children):
                        try:
                            child_title = child.window_text()
                            child_class = child.class_name()
                            child_id = child.control_id()
                            
                            if child_class == "Button":
                                print(f"  控件[{idx}] - Button: '{child_title}' (ID:{child_id})")
                            
                            if child_title == "Start Once" and child_class == "Button":
                                self.button = child
                                print(f"✅ 找到按钮 - Win32遍历成功! 控件[{idx}], ID={child_id}")
                                self.backend = "win32"
                                return True
                        except Exception as e:
                            continue
                    
                    print("⚠️ Win32遍历完成，未找到按钮")
                except Exception as e:
                    print(f"❌ Win32方法失败: {e}")
            
            print("\n" + "="*60)
            print("❌ 所有方法都未能找到按钮")
            print("="*60 + "\n")
            return False
            
        except Exception as e:
            print(f"❌ _check_button_exists 严重错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def click_start_button(self):
        """点击Start Once按钮"""
        try:
            print("\n" + "="*60)
            print("准备点击 Start Once 按钮...")
            print(f"使用后端: {self.backend}")
            print("="*60)
            
            if not self.button:
                print("⚠️ 按钮对象不存在，尝试重新查找...")
                if not self.check_window_exists():
                    return False, "窗口或按钮不存在"
            
            # 使用UIA后端时的点击方法
            if self.backend == "uia":
                try:
                    print("方法1: UIA - 使用click()...")
                    self.button.click()
                    print("✅ UIA click() 成功")
                    return True, "✅ 成功点击Start Once按钮 (UIA)"
                except Exception as e:
                    print(f"⚠️ UIA click()失败: {e}")
                    try:
                        print("方法2: UIA - 使用invoke()...")
                        self.button.invoke()
                        print("✅ UIA invoke() 成功")
                        return True, "✅ 成功点击Start Once按钮 (UIA invoke)"
                    except Exception as e2:
                        print(f"❌ UIA invoke()失败: {e2}")
            
            # 使用Win32后端时的点击方法
            else:
                try:
                    # 确保窗口可见
                    if self.window and not self.window.is_visible():
                        print("窗口不可见，尝试激活...")
                        self.window.set_focus()
                    
                    print("方法3: Win32 - 使用click()...")
                    self.button.click()
                    print("✅ Win32 click() 成功")
                    return True, "✅ 成功点击Start Once按钮 (Win32)"
                except Exception as e:
                    print(f"❌ Win32 click()失败: {e}")
            
            return False, f"❌ 所有点击方法都失败"
            
        except Exception as e:
            error_msg = f"❌ 点击按钮失败: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return False, error_msg
    
    def bring_window_to_top(self, window_title_keyword):
        """将指定窗口置顶"""
        try:
            print(f"\n尝试将包含 '{window_title_keyword}' 的窗口置顶...")
            
            # 先尝试UIA后端
            try:
                desktop_uia = Desktop(backend="uia")
                windows = desktop_uia.windows()
                for win in windows:
                    try:
                        title = win.window_text()
                        if window_title_keyword in title:
                            win.set_focus()
                            print(f"✅ UIA - 窗口已置顶: {title}")
                            return True, f"✅ 窗口已置顶: {title}"
                    except Exception:
                        continue
            except Exception as e:
                print(f"⚠️ UIA置顶失败: {e}")
            
            # 再尝试Win32后端
            try:
                desktop = Desktop(backend="win32")
                windows = desktop.windows()
                for win in windows:
                    try:
                        title = win.window_text()
                        if window_title_keyword in title:
                            win.set_focus()
                            print(f"✅ Win32 - 窗口已置顶: {title}")
                            return True, f"✅ 窗口已置顶: {title}"
                    except Exception:
                        continue
            except Exception as e:
                print(f"❌ Win32置顶失败: {e}")
            
            return False, f"❌ 未找到包含 '{window_title_keyword}' 的窗口"
        except Exception as e:
            return False, f"❌ 置顶窗口失败: {e}"


class SerialWorker(QObject):
    data_received = Signal(str)
    connection_closed = Signal()

    def __init__(self, port):
        super().__init__()
        self.port = port
        self.baud = 9600
        self.running = False
        self.ser = None

    def connect_serial(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            return True
        except Exception as e:
            self.data_received.emit(f"[ERROR] 串口连接失败: {e}")
            return False

    def start_listening(self):
        if not self.ser or not self.ser.is_open:
            return
        self.running = True
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def stop_listening(self):
        self.running = False
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
                self.connection_closed.emit()
            except Exception:
                pass

    def _listen_loop(self):
        retry_count = 0
        while self.running:
            try:
                if self.ser and self.ser.in_waiting:
                    data = self.ser.read_all()
                    for line in parse_response(data):
                        self.data_received.emit(line)
                time.sleep(0.2)
            except (serial.SerialException, OSError) as e:
                self.data_received.emit(f"[WARN] 串口异常: {e}，尝试自动重连...")
                try:
                    self.ser.close()
                except Exception:
                    pass
                time.sleep(3)
                try:
                    self.ser = serial.Serial(self.port, self.baud, timeout=1)
                    retry_count = 0
                    self.data_received.emit("[INFO] 串口自动重连成功。")
                except Exception as e2:
                    retry_count += 1
                    self.data_received.emit(f"[ERROR] 自动重连失败 {retry_count} 次: {e2}")
                    if retry_count >= 3:
                        self.data_received.emit("[FATAL] 连续重连失败，停止监听。")
                        break

    def send_command(self, cmd_bytes, wait_response=True):
        if not self.ser or not self.ser.is_open:
            self.data_received.emit("[WARN] 串口未打开")
            return
        cmd_frame = build_command(cmd_bytes)
        self.ser.write(cmd_frame)
        if wait_response:
            time.sleep(0.3)
            if self.ser.in_waiting:
                data = self.ser.read_all()
                for line in parse_response(data):
                    self.data_received.emit(line)


class TempMonitorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PV MassSpec - 自动控制系统")
        self.resize(950, 700)
        self._build_ui()
        self.serial_worker = None
        self.window_monitor = WindowMonitor()
        self._connect_signals()
        self._trigger_counter = 0
        self.trigger_activated = False
        self.temp_threshold = 50.0
        self.trigger_times = 2
        self.mass_window_keyword = ""  # 质谱窗口关键字（用于置顶）
        self.config_path = os.path.join(os.path.dirname(__file__), "../config/config.json")
        self._load_config()

    def _build_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 标题栏和设置按钮
        title_layout = QHBoxLayout()
        title = QLabel("PV MassSpec - 自动控制系统")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 8px;")
        
        settings_layout = QHBoxLayout()
        settings_layout.addStretch()
        self.save_settings_btn = QPushButton("💾 保存设置")
        self.load_settings_btn = QPushButton("📂 载入设置")
        self.save_settings_btn.setStyleSheet("padding: 5px 15px;")
        self.load_settings_btn.setStyleSheet("padding: 5px 15px;")
        settings_layout.addWidget(self.save_settings_btn)
        settings_layout.addWidget(self.load_settings_btn)
        
        title_frame = QFrame()
        title_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")
        title_frame_layout = QVBoxLayout(title_frame)
        title_frame_layout.addWidget(title)
        title_frame_layout.addLayout(settings_layout)
        
        main_layout.addWidget(title_frame)
        
        # 添加Recipe窗口准备区域（顶部）
        recipe_prepare_frame = QFrame()
        recipe_prepare_frame.setStyleSheet("QFrame { background-color: #fff3cd; border: 2px solid #ffc107; border-radius: 5px; padding: 10px; }")
        recipe_prepare_layout = QVBoxLayout(recipe_prepare_frame)
        
        prepare_title = QLabel("⚠️ 准备工作：请先打开PV MassSpec软件")
        prepare_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #856404;")
        recipe_prepare_layout.addWidget(prepare_title)
        
        prepare_hint = QLabel("打开PV MassSpec软件后，点击Start/Monitor/Review and Start, 确保'Recipe: Setup Summary'窗口可见，然后点击下方按钮确认")
        prepare_hint.setWordWrap(True)
        prepare_hint.setStyleSheet("color: #856404;")
        recipe_prepare_layout.addWidget(prepare_hint)
        
        prepare_btn_row = QHBoxLayout()
        self.confirm_recipe_btn = QPushButton("✅ 我已打开Recipe，确认窗口")
        self.confirm_recipe_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; font-weight: bold; padding: 8px; }")
        self.recipe_window_status = QLabel("状态：⚪ 等待确认")
        prepare_btn_row.addWidget(self.confirm_recipe_btn)
        prepare_btn_row.addWidget(self.recipe_window_status)
        prepare_btn_row.addStretch()
        recipe_prepare_layout.addLayout(prepare_btn_row)
        
        main_layout.addWidget(recipe_prepare_frame)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)

        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setSpacing(10)

        serial_frame = QFrame()
        serial_layout = QVBoxLayout(serial_frame)
        serial_layout.setContentsMargins(10, 5, 10, 5)
        serial_title = QLabel("🔌 串口设置")
        serial_layout.addWidget(serial_title)

        serial_row = QHBoxLayout()
        self.serial_combo = QComboBox()
        self.serial_combo.addItems(["/dev/cu.usbserial-1130", "COM3", "COM4"])
        self.connect_btn = QPushButton("连接")
        self.disconnect_btn = QPushButton("断开")
        serial_row.addWidget(QLabel("端口:"))
        serial_row.addWidget(self.serial_combo)
        serial_row.addWidget(self.connect_btn)
        serial_row.addWidget(self.disconnect_btn)
        serial_layout.addLayout(serial_row)

        self.temp_label = QLabel("实时温度：-- ℃")
        self.status_label = QLabel("状态：🟡 未启动")
        status_row = QHBoxLayout()
        status_row.addWidget(self.temp_label)
        status_row.addWidget(self.status_label)
        serial_layout.addLayout(status_row)
        left_layout.addWidget(serial_frame)

        log_frame = QFrame()
        log_layout = QVBoxLayout(log_frame)
        
        # 日志标题和复制按钮
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("📜 串口日志"))
        log_header.addStretch()
        self.copy_log_btn = QPushButton("📋 复制日志")
        self.clear_log_btn = QPushButton("🗑️ 清空日志")
        log_header.addWidget(self.copy_log_btn)
        log_header.addWidget(self.clear_log_btn)
        log_layout.addLayout(log_header)
        
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        # 设置支持HTML格式显示
        self.log_box.setAcceptRichText(True)
        log_layout.addWidget(self.log_box)
        left_layout.addWidget(log_frame)
        top_layout.addWidget(left_frame, 2)

        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        
        # 启动条件设置区域（上移到顶部）
        condition_frame = QFrame()
        condition_layout = QVBoxLayout(condition_frame)
        condition_layout.addWidget(QLabel("🔧 启动条件设置"))

        temp_row = QHBoxLayout()
        temp_row.addWidget(QLabel("启动温度 m (℃)："))
        self.temp_threshold_input = QLineEdit("50.0")
        temp_row.addWidget(self.temp_threshold_input)
        condition_layout.addLayout(temp_row)

        count_row = QHBoxLayout()
        count_row.addWidget(QLabel("触发次数 n："))
        self.trigger_count_input = QLineEdit("2")
        count_row.addWidget(self.trigger_count_input)
        condition_layout.addLayout(count_row)

        btn_row = QHBoxLayout()
        self.set_condition_btn = QPushButton("设定条件")
        self.clear_condition_btn = QPushButton("清除条件")
        btn_row.addWidget(self.set_condition_btn)
        btn_row.addWidget(self.clear_condition_btn)
        condition_layout.addLayout(btn_row)

        right_layout.addWidget(condition_frame)
        
        # 质谱窗口设置区域
        mass_frame = QFrame()
        mass_layout = QVBoxLayout(mass_frame)
        mass_layout.addWidget(QLabel("⚙️ 质谱窗口设置"))
        
        mass_keyword_row = QHBoxLayout()
        mass_keyword_row.addWidget(QLabel("窗口关键字:"))
        self.mass_window_input = QLineEdit("")
        mass_keyword_row.addWidget(self.mass_window_input)
        mass_layout.addLayout(mass_keyword_row)
        
        mass_hint = QLabel("提示：输入质谱窗口标题中的关键字，用于自动置顶")
        mass_hint.setStyleSheet("font-size: 10px; color: #666;")
        mass_hint.setWordWrap(True)
        mass_layout.addWidget(mass_hint)
        
        right_layout.addWidget(mass_frame)
        
        # 调试工具区域
        debug_frame = QFrame()
        debug_layout = QVBoxLayout(debug_frame)
        debug_layout.addWidget(QLabel("🔍 调试工具"))
        
        debug_btn_row = QHBoxLayout()
        self.list_controls_btn = QPushButton("列出所有控件")
        self.test_click_btn = QPushButton("测试点击按钮")
        debug_btn_row.addWidget(self.list_controls_btn)
        debug_btn_row.addWidget(self.test_click_btn)
        debug_layout.addLayout(debug_btn_row)
        
        right_layout.addWidget(debug_frame)
        
        right_layout.addStretch()

        top_layout.addWidget(right_frame, 3)

        main_layout.addLayout(top_layout)

        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        self.start_btn = QPushButton("启动监控")
        self.stop_btn = QPushButton("停止监控")
        self.test_btn = QPushButton("测试脚本")
        self.exit_btn = QPushButton("退出")
        control_layout.addStretch()
        for btn in [self.start_btn, self.stop_btn, self.test_btn, self.exit_btn]:
            control_layout.addWidget(btn)
        main_layout.addWidget(control_frame)

        self.setCentralWidget(main_widget)

    def _connect_signals(self):
        self.connect_btn.clicked.connect(self._connect_serial)
        self.disconnect_btn.clicked.connect(self._disconnect_serial)
        self.start_btn.clicked.connect(self._start_monitor)
        self.stop_btn.clicked.connect(self._stop_monitor)
        # 绑定启动条件设置按钮
        self.set_condition_btn.clicked.connect(self._set_conditions)
        self.clear_condition_btn.clicked.connect(self._clear_conditions)
        # 绑定Recipe窗口确认按钮
        self.confirm_recipe_btn.clicked.connect(self._confirm_recipe_window)
        # 绑定调试工具按钮
        self.list_controls_btn.clicked.connect(self._list_window_controls)
        self.test_click_btn.clicked.connect(self._test_click_button)
        # 绑定日志操作按钮
        self.copy_log_btn.clicked.connect(self._copy_log)
        self.clear_log_btn.clicked.connect(self._clear_log)
        # 绑定设置按钮
        self.save_settings_btn.clicked.connect(self._save_settings_dialog)
        self.load_settings_btn.clicked.connect(self._load_settings_dialog)
        # 绑定窗口监测信号
        self.window_monitor.window_status_changed.connect(self._on_window_status_changed)

    def _connect_serial(self):
        port = self.serial_combo.currentText()
        self.serial_worker = SerialWorker(port)
        if self.serial_worker.connect_serial():
            self.serial_worker.data_received.connect(self._update_log)
            self.serial_worker.connection_closed.connect(self._on_disconnected)
            self._update_log(f"[OK] 已连接串口: {port}")
            self.status_label.setText("状态：🟢 已连接")
            self._save_config()
        else:
            self.status_label.setText("状态：🔴 连接失败")

    def _disconnect_serial(self):
        if self.serial_worker:
            self.serial_worker.stop_listening()
            self.status_label.setText("状态：🔘 已断开")
            self._update_log("[INFO] 串口已断开。")

    def _start_monitor(self):
        if not self.serial_worker:
            self._update_log("[WARN] 请先连接串口。")
            return
        self.serial_worker.send_command(CMD_TEMP_START, wait_response=False)
        self.serial_worker.start_listening()
        self.status_label.setText("状态：🟡 正在监控")
        self._update_log("[INFO] 已启动温度监控。")

    def _stop_monitor(self):
        if self.serial_worker:
            self.serial_worker.send_command(CMD_TEMP_STOP, wait_response=True)
            self.serial_worker.stop_listening()
            self.status_label.setText("状态：⚪ 已停止")
            self._update_log("[INFO] 已停止监控。")

    def _update_log(self, text):
        import re
        # 调试输出：收到的原始文本
        try:
            print(f"[DEBUG] 收到日志信号: {text}")
        except UnicodeEncodeError:
            print(f"[DEBUG] Log received (encoding error, text length: {len(text)})")

        match = re.search(r"TEMP[=\s]*([0-9]+(?:\.[0-9]+)?)", text)
        if match:
            temp_value = float(match.group(1))
            try:
                print(f"[DEBUG] 提取温度值: {temp_value}")
            except UnicodeEncodeError:
                print(f"[DEBUG] Temperature extracted: {temp_value}")
            self.temp_label.setText(f"实时温度：{temp_value:.1f} ℃")

            # ===== 启动条件检测 =====
            if not hasattr(self, "temp_threshold"):
                self.temp_threshold = 50.0
            if not hasattr(self, "trigger_times"):
                self.trigger_times = 2

            # 检测触发逻辑
            if not getattr(self, "trigger_activated", False):
                if temp_value >= self.temp_threshold:
                    self._trigger_counter += 1
                    debug_msg = f"[DEBUG] 达到阈值: {self._trigger_counter}/{self.trigger_times}"
                    try:
                        print(debug_msg)
                    except UnicodeEncodeError:
                        print(f"[DEBUG] Threshold reached: {self._trigger_counter}/{self.trigger_times}")
                    self.log_box.append(debug_msg)
                    if self._trigger_counter >= self.trigger_times:
                        info_msg = "[INFO] 启动条件满足，准备执行自动控制..."
                        try:
                            print(info_msg)
                        except UnicodeEncodeError:
                            print("[INFO] Trigger condition met, executing auto control...")
                        self.log_box.append(info_msg)
                        self._trigger_auto_control()
                        self.trigger_activated = True

                        # 启动保护逻辑：10秒后允许重新触发
                        def reset_trigger():
                            self.trigger_activated = False
                            self._trigger_counter = 0
                            self._update_log("[INFO] 启动保护解除，可再次检测触发条件。")
                        threading.Timer(10.0, reset_trigger).start()
                else:
                    if self._trigger_counter != 0:
                        try:
                            print("[DEBUG] 温度下降，重置计数器。")
                        except UnicodeEncodeError:
                            print("[DEBUG] Temperature dropped, resetting counter.")
                    self._trigger_counter = 0
        else:
            try:
                print("[DEBUG] 未匹配到温度数据。")
            except UnicodeEncodeError:
                print("[DEBUG] No temperature data matched.")

        # 将日志追加到文本框
        self.log_box.append(text)
    
    def _update_log_colored(self, text, color="black"):
        """添加带颜色的日志"""
        # 颜色映射
        color_map = {
            "green": "#28a745",
            "red": "#dc3545",
            "yellow": "#ffc107",
            "blue": "#007bff",
            "black": "#000000"
        }
        
        hex_color = color_map.get(color, "#000000")
        
        # 使用HTML格式添加彩色文本
        html_text = f'<span style="color: {hex_color}; font-weight: bold;">{text}</span>'
        self.log_box.append(html_text)
        
        # 同时在控制台输出
        try:
            print(f"[{color.upper()}] {text}")
        except UnicodeEncodeError:
            print(f"[{color.upper()}] (text with {len(text)} chars)")


    def _trigger_auto_control(self):
        """温度达到后执行自动控制：点击Recipe按钮并置顶质谱窗口"""
        self._update_log_colored("🔥 温度触发条件满足，开始执行自动控制...", "blue")
        
        # 1. 检查Recipe窗口是否存在
        if not self.window_monitor.window or not self.window_monitor.button:
            self._update_log_colored(
                "❌ Recipe窗口或按钮不可用！请确保Recipe软件已打开并确认窗口。",
                "red"
            )
            return
        
        # 2. 点击Start Once按钮
        success, msg = self.window_monitor.click_start_button()
        
        if success:
            self._update_log_colored(f"✅ {msg}", "green")
        else:
            self._update_log_colored(f"❌ {msg}", "red")
            return
        
        # 3. 等待一小段时间
        time.sleep(0.5)
        
        # 4. 将质谱窗口置顶
        mass_keyword = self.mass_window_input.text().strip()
        if mass_keyword:
            success, msg = self.window_monitor.bring_window_to_top(mass_keyword)
            if success:
                self._update_log_colored(f"✅ {msg}", "green")
            else:
                self._update_log_colored(f"⚠️ {msg}", "yellow")
        else:
            self._update_log("[INFO] 未设置质谱窗口关键字，跳过置顶操作")
        
        self._update_log_colored("✅ 自动控制执行完成！", "green")
    
    def _confirm_recipe_window(self):
        """用户确认Recipe窗口已打开"""
        self._update_log("[INFO] 正在检查Recipe窗口和按钮...")
        # 在新线程中检查窗口
        threading.Thread(target=self._check_and_confirm_window, daemon=True).start()
    
    def _check_and_confirm_window(self):
        """检查窗口和按钮是否存在"""
        if self.window_monitor.check_window_exists():
            # 成功 - 绿色显示
            self._update_log_colored(
                "✅ Recipe窗口和'Start Once'按钮已找到！现在可以连接串口并启动监控。",
                "green"
            )
        else:
            # 失败 - 红色显示
            self._update_log_colored(
                "❌ 未找到Recipe窗口或'Start Once'按钮！",
                "red"
            )
            self._update_log("请确保：")
            self._update_log("  1. Recipe软件已打开")
            self._update_log("  2. 'Recipe: Setup Summary'窗口可见")
            self._update_log("  3. 'Start Once'按钮存在")
            self._update_log("然后重新点击确认按钮。")
    
    def _on_window_status_changed(self, exists, message):
        """窗口状态变化回调"""
        if exists:
            self.recipe_window_status.setText(f"状态：🟢 {message}")
            self.confirm_recipe_btn.setEnabled(False)
            self.confirm_recipe_btn.setText("✅ 已确认")
        else:
            self.recipe_window_status.setText(f"状态：🔴 {message}")
            self.confirm_recipe_btn.setEnabled(True)
            self.confirm_recipe_btn.setText("✅ 我已打开Recipe，确认窗口")
        self._update_log(f"[WINDOW] {message}")
    
    def _test_click_button(self):
        """测试点击Start Once按钮"""
        self._update_log("[TEST] 测试点击Start Once按钮...")
        
        if not self.window_monitor.window or not self.window_monitor.button:
            self._update_log_colored(
                "❌ 请先点击'确认窗口'按钮，确保Recipe窗口和按钮已找到！",
                "red"
            )
            return
        
        success, message = self.window_monitor.click_start_button()
        
        if success:
            self._update_log_colored(f"✅ {message}", "green")
            
            # 尝试置顶质谱窗口
            mass_keyword = self.mass_window_input.text().strip()
            if mass_keyword:
                time.sleep(0.5)
                success2, msg2 = self.window_monitor.bring_window_to_top(mass_keyword)
                if success2:
                    self._update_log_colored(f"✅ {msg2}", "green")
                else:
                    self._update_log_colored(f"⚠️ {msg2}", "yellow")
            
            self._update_log_colored("如果按钮被点击，说明自动控制功能正常！", "blue")
        else:
            self._update_log_colored(f"❌ {message}", "red")
    
    def _list_window_controls(self):
        """列出Recipe窗口的所有控件"""
        self._update_log("[INFO] 正在列出窗口控件...")
        
        # 确保窗口已找到
        if not self.window_monitor.window:
            # 先尝试查找窗口
            if not self.window_monitor.check_window_exists():
                self._update_log("[ERROR] 无法找到Recipe窗口")
                QMessageBox.warning(self, "警告", "请先确保Recipe窗口已打开！")
                return
        
        # 获取控件列表
        controls_list = self.window_monitor.get_controls_list()
        controls_text = "\n".join(controls_list)
        
        # 在日志框中显示完整信息
        self._update_log("\n" + "="*80)
        self._update_log("[CONTROLS] 窗口控件列表:")
        self._update_log("="*80)
        for line in controls_list:
            self.log_box.append(line)
        self._update_log("="*80 + "\n")
        
        # 创建自定义对话框用于显示和复制
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("窗口控件列表")
        dialog.resize(700, 600)
        
        layout = QVBoxLayout(dialog)
        
        # 添加文本框显示控件信息
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(controls_text)
        text_edit.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace;")
        layout.addWidget(text_edit)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        copy_button = QPushButton("📋 复制到剪贴板")
        close_button = QPushButton("关闭")
        
        def copy_to_clipboard():
            clipboard = QApplication.clipboard()
            clipboard.setText(controls_text)
            QMessageBox.information(dialog, "复制成功", f"已复制 {len(controls_text)} 个字符到剪贴板！")
        
        copy_button.clicked.connect(copy_to_clipboard)
        close_button.clicked.connect(dialog.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(copy_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def _copy_log(self):
        """复制日志内容到剪贴板"""
        log_text = self.log_box.toPlainText()
        if log_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(log_text)
            self._update_log("[INFO] 📋 日志已复制到剪贴板")
            # 显示提示
            QMessageBox.information(self, "复制成功", f"已复制 {len(log_text)} 个字符到剪贴板")
        else:
            QMessageBox.warning(self, "提示", "日志为空，无内容可复制")
    
    def _clear_log(self):
        """清空日志"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有日志吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.log_box.clear()
            self._update_log("[INFO] 🗑️ 日志已清空")

    def _on_disconnected(self):
        self.status_label.setText("状态：🔘 已断开")
        self._update_log("[CLOSE] 串口关闭。")

    def _set_conditions(self):
        """设置启动条件"""
        try:
            self.temp_threshold = float(self.temp_threshold_input.text())
            self.trigger_times = int(self.trigger_count_input.text())
            self._update_log(f"[INFO] 启动条件已设定：温度≥{self.temp_threshold}℃ 连续 {self.trigger_times} 次触发。")
            try:
                print(f"[DEBUG] 启动条件：temp={self.temp_threshold}, count={self.trigger_times}")
            except UnicodeEncodeError:
                print(f"[DEBUG] Conditions set: temp={self.temp_threshold}, count={self.trigger_times}")
            self._save_config()
        except ValueError:
            self._update_log("[ERROR] 启动条件输入无效，请检查数值。")

    def _clear_conditions(self):
        """清除启动条件"""
        self.temp_threshold_input.setText("50.0")
        self.trigger_count_input.setText("2")
        self.temp_threshold = 50.0
        self.trigger_times = 2
        self._update_log("[INFO] 启动条件已清除为默认值。")
        try:
            print("[DEBUG] 启动条件已重置为默认。")
        except UnicodeEncodeError:
            print("[DEBUG] Conditions reset to default.")

    def _save_config(self):
        """自动保存配置（内部使用）"""
        cfg = {
            "port": self.serial_combo.currentText(),
            "temp_threshold": self.temp_threshold_input.text(),
            "trigger_times": self.trigger_count_input.text(),
            "mass_window_keyword": self.mass_window_input.text(),
        }
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ERROR] 自动保存配置失败: {e}")

    def _load_config(self):
        """启动时自动加载配置（内部使用）"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.serial_combo.setCurrentText(cfg.get("port", ""))
                self.temp_threshold_input.setText(cfg.get("temp_threshold", "50.0"))
                self.trigger_count_input.setText(cfg.get("trigger_times", "2"))
                self.mass_window_input.setText(cfg.get("mass_window_keyword", ""))
                self.mass_window_keyword = cfg.get("mass_window_keyword", "")
                self._update_log("[INFO] 已加载上次配置。")
            else:
                self._update_log("[INFO] 未找到配置文件，使用默认参数。")
        except Exception as e:
            self._update_log(f"[ERROR] 加载配置失败: {e}")
    
    def _save_settings_dialog(self):
        """用户手动保存设置"""
        # 获取当前所有设置
        settings = {
            "串口端口": self.serial_combo.currentText(),
            "启动温度(℃)": self.temp_threshold_input.text(),
            "触发次数": self.trigger_count_input.text(),
            "质谱窗口关键字": self.mass_window_input.text(),
        }
        
        # 弹出文件保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存设置",
            os.path.join(os.path.dirname(self.config_path), "my_settings.json"),
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(settings, f, ensure_ascii=False, indent=2)
                self._update_log_colored(f"✅ 设置已保存到: {file_path}", "green")
            except Exception as e:
                self._update_log_colored(f"❌ 保存设置失败: {e}", "red")
    
    def _load_settings_dialog(self):
        """用户手动载入设置"""
        # 弹出文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "载入设置",
            os.path.dirname(self.config_path),
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                
                # 应用设置
                if "串口端口" in settings:
                    self.serial_combo.setCurrentText(settings["串口端口"])
                if "启动温度(℃)" in settings:
                    self.temp_threshold_input.setText(settings["启动温度(℃)"])
                if "触发次数" in settings:
                    self.trigger_count_input.setText(settings["触发次数"])
                if "质谱窗口关键字" in settings:
                    self.mass_window_input.setText(settings["质谱窗口关键字"])
                
                # 更新内部变量
                try:
                    self.temp_threshold = float(self.temp_threshold_input.text())
                    self.trigger_times = int(self.trigger_count_input.text())
                    self.mass_window_keyword = self.mass_window_input.text()
                except:
                    pass
                
                self._update_log_colored(f"✅ 设置已从文件载入: {file_path}", "green")
                self._save_config()  # 自动保存为默认配置
                
            except Exception as e:
                self._update_log_colored(f"❌ 载入设置失败: {e}", "red")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = TempMonitorUI()
    ui.show()
    sys.exit(app.exec())
