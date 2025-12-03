"""
主UI界面
"""
import sys
import threading
import time
import json
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, QFrame,
    QMessageBox, QFileDialog, QRadioButton, QButtonGroup, QDialog
)
from PySide6.QtCore import Qt

# 修复Windows控制台中文编码问题
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 导入自定义模块
import sys
import os
# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from controller.window_monitor import WindowMonitor
from controller.serial_worker import SerialWorker
from utils.serial_utils import CMD_TEMP_START, CMD_TEMP_STOP


class TempMonitorUI(QMainWindow):
    """温度监控主界面"""
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
        self.trigger_interval = 5.0  # 触发间隔时间（秒）
        self._last_temp_above_threshold = False  # 记录上次温度是否高于阈值
        self._last_trigger_time = None  # 记录上次触发的时间
        self.mass_window_keyword = ""  # 质谱窗口关键字（用于置顶）
        self.config_path = os.path.join(os.path.dirname(__file__), "../config/config.json")
        self._load_config()

    def _build_ui(self):
        """构建UI界面"""
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
        
        # 添加按钮类型选择
        button_type_layout = QHBoxLayout()
        button_type_label = QLabel("选择按钮类型:")
        button_type_label.setStyleSheet("font-weight: bold; color: #856404;")
        button_type_layout.addWidget(button_type_label)
        
        # 创建单选按钮组
        self.button_type_group = QButtonGroup()
        self.start_once_radio = QRadioButton("Start Once")
        self.start_continuous_radio = QRadioButton("Start Continuous")
        self.start_once_radio.setChecked(True)  # 默认选择Start Once
        self.start_continuous_radio.setChecked(False)
        
        self.button_type_group.addButton(self.start_once_radio, 0)
        self.button_type_group.addButton(self.start_continuous_radio, 1)
        
        button_type_layout.addWidget(self.start_once_radio)
        button_type_layout.addWidget(self.start_continuous_radio)
        button_type_layout.addStretch()
        recipe_prepare_layout.addLayout(button_type_layout)
        
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

        interval_row = QHBoxLayout()
        interval_row.addWidget(QLabel("触发间隔时间 (秒)："))
        self.trigger_interval_input = QLineEdit("5")
        interval_row.addWidget(self.trigger_interval_input)
        condition_layout.addLayout(interval_row)

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
        """连接信号和槽"""
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
        # 绑定按钮类型选择信号
        self.start_once_radio.toggled.connect(self._on_button_type_changed)
        self.start_continuous_radio.toggled.connect(self._on_button_type_changed)

    def _connect_serial(self):
        """连接串口"""
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
        """断开串口"""
        if self.serial_worker:
            self.serial_worker.stop_listening()
            self.status_label.setText("状态：🔘 已断开")
            self._update_log("[INFO] 串口已断开。")

    def _start_monitor(self):
        """启动监控"""
        if not self.serial_worker:
            self._update_log("[WARN] 请先连接串口。")
            return
        self.serial_worker.send_command(CMD_TEMP_START, wait_response=False)
        self.serial_worker.start_listening()
        self.status_label.setText("状态：🟡 正在监控")
        self._update_log("[INFO] 已启动温度监控。")

    def _stop_monitor(self):
        """停止监控"""
        if self.serial_worker:
            self.serial_worker.send_command(CMD_TEMP_STOP, wait_response=True)
            self.serial_worker.stop_listening()
            self.status_label.setText("状态：⚪ 已停止")
            self._update_log("[INFO] 已停止监控。")

    def _update_log(self, text):
        """更新日志"""
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
                # 检查当前温度是否高于阈值
                current_above = temp_value >= self.temp_threshold
                
                # 只有在温度从低于阈值变为高于阈值时才累加计数器
                if current_above and not self._last_temp_above_threshold:
                    current_time = time.time()
                    
                    # 检查是否在间隔时间内（如果不是第一次触发）
                    if self._last_trigger_time is not None:
                        time_since_last = current_time - self._last_trigger_time
                        if time_since_last < self.trigger_interval:
                            # 间隔时间太短，不计数，等待下次
                            debug_msg = f"[DEBUG] 触发间隔不足: {time_since_last:.1f}秒 < {self.trigger_interval}秒，等待中..."
                            try:
                                print(debug_msg)
                            except UnicodeEncodeError:
                                print(f"[DEBUG] Interval too short: {time_since_last:.1f}s < {self.trigger_interval}s")
                            self.log_box.append(debug_msg)
                            # 不更新状态，保持_last_temp_above_threshold为False，这样下次温度数据到来时还能再次检查
                            return
                    
                    # 温度从低于阈值变为高于阈值，计数器+1
                    self._trigger_counter += 1
                    self._last_trigger_time = current_time
                    debug_msg = f"[DEBUG] 达到阈值: {self._trigger_counter}/{self.trigger_times} (间隔: {self.trigger_interval}秒)"
                    try:
                        print(debug_msg)
                    except UnicodeEncodeError:
                        print(f"[DEBUG] Threshold reached: {self._trigger_counter}/{self.trigger_times} (interval: {self.trigger_interval}s)")
                    self.log_box.append(debug_msg)
                    
                    # 检查是否达到触发次数
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
                            self._last_temp_above_threshold = False
                            self._last_trigger_time = None
                            self._update_log("[INFO] 启动保护解除，可再次检测触发条件。")
                        threading.Timer(10.0, reset_trigger).start()
                elif not current_above and self._last_temp_above_threshold:
                    # 温度从高于阈值变为低于阈值，重置计数器
                    if self._trigger_counter != 0:
                        try:
                            print("[DEBUG] 温度下降，重置计数器。")
                        except UnicodeEncodeError:
                            print("[DEBUG] Temperature dropped, resetting counter.")
                    self._trigger_counter = 0
                    self._last_trigger_time = None
                
                # 更新状态
                self._last_temp_above_threshold = current_above
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
        
        # 2. 点击按钮
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
    
    def _on_button_type_changed(self):
        """按钮类型选择改变时的回调"""
        if self.start_once_radio.isChecked():
            self.window_monitor.button_type = "Start Once"
            self.window_monitor.button_name = "Start Once"
            self._update_log("[INFO] 已选择按钮类型: Start Once")
        elif self.start_continuous_radio.isChecked():
            self.window_monitor.button_type = "Start Continuous"
            self.window_monitor.button_name = "Start Continuous"
            self._update_log("[INFO] 已选择按钮类型: Start Continuous")
        # 重置按钮对象，需要重新查找
        self.window_monitor.button = None
        self.window_monitor.dropdown_button = None
    
    def _confirm_recipe_window(self):
        """用户确认Recipe窗口已打开"""
        # 先更新按钮类型
        self._on_button_type_changed()
        self._update_log("[INFO] 正在检查Recipe窗口和按钮...")
        # 在新线程中检查窗口
        threading.Thread(target=self._check_and_confirm_window, daemon=True).start()
    
    def _check_and_confirm_window(self):
        """检查窗口和按钮是否存在"""
        button_type_name = self.window_monitor.button_type
        if self.window_monitor.check_window_exists():
            # 成功 - 绿色显示
            self._update_log_colored(
                f"✅ Recipe窗口和'{button_type_name}'按钮已找到！现在可以连接串口并启动监控。",
                "green"
            )
        else:
            # 失败 - 红色显示
            self._update_log_colored(
                f"❌ 未找到Recipe窗口或'{button_type_name}'按钮！",
                "red"
            )
            self._update_log("请确保：")
            self._update_log("  1. Recipe软件已打开")
            self._update_log("  2. 'Recipe: Setup Summary'窗口可见")
            if button_type_name == "Start Continuous":
                self._update_log("  3. 'Start Continuous'按钮及其下拉按钮存在")
            else:
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
        """测试点击按钮"""
        button_type_name = self.window_monitor.button_type
        self._update_log(f"[TEST] 测试点击{button_type_name}按钮...")
        
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
        """串口断开回调"""
        self.status_label.setText("状态：🔘 已断开")
        self._update_log("[CLOSE] 串口关闭。")

    def _set_conditions(self):
        """设置启动条件"""
        try:
            self.temp_threshold = float(self.temp_threshold_input.text())
            self.trigger_times = int(self.trigger_count_input.text())
            self.trigger_interval = float(self.trigger_interval_input.text())
            self._update_log(f"[INFO] 启动条件已设定：温度≥{self.temp_threshold}℃ 连续 {self.trigger_times} 次触发，间隔 {self.trigger_interval} 秒。")
            try:
                print(f"[DEBUG] 启动条件：temp={self.temp_threshold}, count={self.trigger_times}, interval={self.trigger_interval}")
            except UnicodeEncodeError:
                print(f"[DEBUG] Conditions set: temp={self.temp_threshold}, count={self.trigger_times}, interval={self.trigger_interval}")
            self._save_config()
        except ValueError:
            self._update_log("[ERROR] 启动条件输入无效，请检查数值。")

    def _clear_conditions(self):
        """清除启动条件"""
        self.temp_threshold_input.setText("50.0")
        self.trigger_count_input.setText("2")
        self.trigger_interval_input.setText("5")
        self.temp_threshold = 50.0
        self.trigger_times = 2
        self.trigger_interval = 5.0
        self._update_log("[INFO] 启动条件已清除为默认值。")
        try:
            print("[DEBUG] 启动条件已重置为默认。")
        except UnicodeEncodeError:
            print("[DEBUG] Conditions reset to default.")

    def _save_config(self):
        """自动保存配置（内部使用）"""
        # 获取按钮类型
        button_type = "Start Once" if self.start_once_radio.isChecked() else "Start Continuous"
        cfg = {
            "port": self.serial_combo.currentText(),
            "temp_threshold": self.temp_threshold_input.text(),
            "trigger_times": self.trigger_count_input.text(),
            "trigger_interval": self.trigger_interval_input.text(),
            "mass_window_keyword": self.mass_window_input.text(),
            "button_type": button_type,
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
                self.trigger_interval_input.setText(cfg.get("trigger_interval", "5"))
                self.mass_window_input.setText(cfg.get("mass_window_keyword", ""))
                self.mass_window_keyword = cfg.get("mass_window_keyword", "")
                # 更新内部变量
                try:
                    self.temp_threshold = float(self.temp_threshold_input.text())
                    self.trigger_times = int(self.trigger_count_input.text())
                    self.trigger_interval = float(self.trigger_interval_input.text())
                except:
                    self.trigger_interval = 5.0
                # 加载按钮类型
                button_type = cfg.get("button_type", "Start Once")
                if button_type == "Start Continuous":
                    self.start_continuous_radio.setChecked(True)
                    self.start_once_radio.setChecked(False)
                else:
                    self.start_once_radio.setChecked(True)
                    self.start_continuous_radio.setChecked(False)
                # 更新window_monitor的button_type
                self._on_button_type_changed()
                self._update_log("[INFO] 已加载上次配置。")
            else:
                self._update_log("[INFO] 未找到配置文件，使用默认参数。")
        except Exception as e:
            self._update_log(f"[ERROR] 加载配置失败: {e}")
    
    def _save_settings_dialog(self):
        """用户手动保存设置"""
        # 获取当前所有设置
        button_type = "Start Once" if self.start_once_radio.isChecked() else "Start Continuous"
        settings = {
            "串口端口": self.serial_combo.currentText(),
            "启动温度(℃)": self.temp_threshold_input.text(),
            "触发次数": self.trigger_count_input.text(),
            "触发间隔时间(秒)": self.trigger_interval_input.text(),
            "质谱窗口关键字": self.mass_window_input.text(),
            "按钮类型": button_type,
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
                if "触发间隔时间(秒)" in settings:
                    self.trigger_interval_input.setText(settings["触发间隔时间(秒)"])
                if "质谱窗口关键字" in settings:
                    self.mass_window_input.setText(settings["质谱窗口关键字"])
                # 加载按钮类型
                if "按钮类型" in settings:
                    button_type = settings["按钮类型"]
                    if button_type == "Start Continuous":
                        self.start_continuous_radio.setChecked(True)
                        self.start_once_radio.setChecked(False)
                    else:
                        self.start_once_radio.setChecked(True)
                        self.start_continuous_radio.setChecked(False)
                    self._on_button_type_changed()
                
                # 更新内部变量
                try:
                    self.temp_threshold = float(self.temp_threshold_input.text())
                    self.trigger_times = int(self.trigger_count_input.text())
                    self.trigger_interval = float(self.trigger_interval_input.text())
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

