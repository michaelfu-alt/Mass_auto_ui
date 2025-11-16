import sys
import threading
import time
import serial
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QObject
import json, os


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
        self.setWindowTitle("🔥 炉温监控与启动控制面板")
        self.resize(950, 650)
        self._build_ui()
        self.serial_worker = None
        self._connect_signals()
        self._trigger_counter = 0
        self.trigger_activated = False
        self.temp_threshold = 50.0
        self.trigger_times = 2
        self.config_path = os.path.join(os.path.dirname(__file__), "../config/config.json")
        self._load_config()

    def _build_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("🔥 炉温监控与启动控制面板")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 8px; background-color: #f0f0f0;")
        main_layout.addWidget(title)

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
        log_layout.addWidget(QLabel("📜 串口日志"))
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        log_layout.addWidget(self.log_box)
        left_layout.addWidget(log_frame)
        top_layout.addWidget(left_frame, 2)

        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        mass_frame = QFrame()
        mass_layout = QVBoxLayout(mass_frame)
        mass_layout.addWidget(QLabel("⚙️ 质谱设置"))
        self.mass_path_input = QLineEdit("/Applications/MassSpecApp.app")
        self.mass_test_btn = QPushButton("测试启动")
        row = QHBoxLayout()
        row.addWidget(QLabel("软件路径:"))
        row.addWidget(self.mass_path_input)
        row.addWidget(self.mass_test_btn)
        mass_layout.addLayout(row)
        right_layout.addWidget(mass_frame)

        # 添加启动条件设置区域
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
        # 绑定质谱软件启动按钮
        self.mass_test_btn.clicked.connect(self.start_mass_spectrometer)
        # 绑定启动条件设置按钮
        self.set_condition_btn.clicked.connect(self._set_conditions)
        self.clear_condition_btn.clicked.connect(self._clear_conditions)

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
        print(f"[DEBUG] 收到日志信号: {text}")

        match = re.search(r"TEMP[=\s]*([0-9]+(?:\.[0-9]+)?)", text)
        if match:
            temp_value = float(match.group(1))
            print(f"[DEBUG] 提取温度值: {temp_value}")
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
                    print(debug_msg)
                    self.log_box.append(debug_msg)
                    if self._trigger_counter >= self.trigger_times:
                        info_msg = "[INFO] 启动条件满足，准备启动质谱软件..."
                        print(info_msg)
                        self.log_box.append(info_msg)
                        self.start_mass_spectrometer()
                        self.trigger_activated = True

                        # 启动保护逻辑：10秒后允许重新触发
                        def reset_trigger():
                            self.trigger_activated = False
                            self._trigger_counter = 0
                            self._update_log("[INFO] 启动保护解除，可再次检测触发条件。")
                        threading.Timer(10.0, reset_trigger).start()
                else:
                    if self._trigger_counter != 0:
                        print("[DEBUG] 温度下降，重置计数器。")
                    self._trigger_counter = 0
        else:
            print("[DEBUG] 未匹配到温度数据。")

        # 将日志追加到文本框
        self.log_box.append(text)


    def start_mass_spectrometer(self):
        """启动质谱软件（debug版）"""
        import subprocess
        import os
        path = self.mass_path_input.text().strip()
        if not path:
            self._update_log("[WARN] 未设置质谱软件路径。")
            return

        # 判断路径是否存在
        if not os.path.exists(path):
            self._update_log(f"[ERROR] 软件路径不存在: {path}")
            return

        # Debug输出
        self._update_log(f"[DEBUG] 尝试启动质谱软件: {path}")

        try:
            subprocess.Popen([path], shell=False)
            self._update_log("[DEBUG] 质谱软件已启动 (subprocess.Popen 调用成功)")
            self._save_config()
        except Exception as e:
            self._update_log(f"[ERROR] 启动质谱软件失败: {e}")

    def _on_disconnected(self):
        self.status_label.setText("状态：🔘 已断开")
        self._update_log("[CLOSE] 串口关闭。")

    def _set_conditions(self):
        """设置启动条件"""
        try:
            self.temp_threshold = float(self.temp_threshold_input.text())
            self.trigger_times = int(self.trigger_count_input.text())
            self._update_log(f"[INFO] 启动条件已设定：温度≥{self.temp_threshold}℃ 连续 {self.trigger_times} 次触发。")
            print(f"[DEBUG] 启动条件：temp={self.temp_threshold}, count={self.trigger_times}")
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
        print("[DEBUG] 启动条件已重置为默认。")

    def _save_config(self):
        cfg = {
            "port": self.serial_combo.currentText(),
            "temp_threshold": self.temp_threshold_input.text(),
            "trigger_times": self.trigger_count_input.text(),
            "mass_path": self.mass_path_input.text(),
        }
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            self._update_log("[INFO] 已保存配置至 config/config.json")
        except Exception as e:
            self._update_log(f"[ERROR] 保存配置失败: {e}")

    def _load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.serial_combo.setCurrentText(cfg.get("port", ""))
                self.temp_threshold_input.setText(cfg.get("temp_threshold", "50.0"))
                self.trigger_count_input.setText(cfg.get("trigger_times", "2"))
                self.mass_path_input.setText(cfg.get("mass_path", ""))
                self._update_log("[INFO] 已加载上次配置。")
            else:
                self._update_log("[INFO] 未找到配置文件，使用默认参数。")
        except Exception as e:
            self._update_log(f"[ERROR] 加载配置失败: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = TempMonitorUI()
    ui.show()
    sys.exit(app.exec())
