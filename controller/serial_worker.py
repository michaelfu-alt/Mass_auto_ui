"""
串口通信工作类
"""
import threading
import time
import serial
from PySide6.QtCore import Signal, QObject
import sys
import os
# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.serial_utils import build_command, parse_response


class SerialWorker(QObject):
    """串口通信工作类"""
    data_received = Signal(str)
    connection_closed = Signal()

    def __init__(self, port):
        super().__init__()
        self.port = port
        self.baud = 9600
        self.running = False
        self.ser = None

    def connect_serial(self):
        """连接串口"""
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            return True
        except Exception as e:
            self.data_received.emit(f"[ERROR] 串口连接失败: {e}")
            return False

    def start_listening(self):
        """开始监听串口数据"""
        if not self.ser or not self.ser.is_open:
            return
        self.running = True
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def stop_listening(self):
        """停止监听串口数据"""
        self.running = False
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
                self.connection_closed.emit()
            except Exception:
                pass

    def _listen_loop(self):
        """监听循环"""
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
        """发送命令"""
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
