# 串口通信模块 - 协议扩展版
# 用于连接 CH340 串口并发送 TEMP 采集命令帧与接收响应

# 串口通信模块 - 协议精确版
# 上位机发送 TEMP 采集命令帧并解析下位机响应

import serial
import time
import threading

START_BYTE = 0x73
STOP_BYTE = 0x65

# 命令定义
CMD_TEMP_START = [0x01, 0x01]
CMD_TEMP_STOP = [0x00, 0x01]

def calc_checksum(data_bytes):
    """简单累加校验"""
    checksum = sum(data_bytes) & 0xFFFF
    high = (checksum >> 8) & 0xFF
    low = checksum & 0xFF
    return high, low

def build_command(cmd_bytes):
    """构造完整帧"""
    data_len = len(cmd_bytes)
    check_high, check_low = calc_checksum(cmd_bytes)
    frame = bytes([START_BYTE, data_len]) + bytes(cmd_bytes) + bytes([check_high, check_low, STOP_BYTE])
    return frame

def _parse_protocol_frame(frame: bytes):
    """改进版协议帧解析，自动检测 OK 或数据内容"""
    if len(frame) < 7:
        return "[WARN] 帧长度不足"

    if frame[0] != START_BYTE or frame[-1] != STOP_BYTE:
        return f"[ERROR] 帧格式错误 ({frame.hex(' ')})"

    payload = frame[2:-3]  # 动态识别数据段
    chk_high, chk_low = frame[-3], frame[-2]

    # 自动检测OK字符串
    if b'OK' in payload:
        return "[OK] 收到下位机确认帧"
    elif not payload:
        return "[OK] 收到空响应帧"
    else:
        return f"[DATA] 返回数据: {payload.hex(' ')} 校验:{chk_high:02X}{chk_low:02X}"

def parse_response(data: bytes):
    """解析下位机返回帧，可识别协议帧与文本帧"""
    responses = []
    i = 0
    while i < len(data):
        # 检测协议帧
        if data[i] == START_BYTE and (i + 1) < len(data):
            try:
                end_index = data.index(STOP_BYTE, i)
                frame = data[i:end_index + 1]
                responses.append(_parse_protocol_frame(frame))
                i = end_index + 1
            except ValueError:
                responses.append("[WARN] 未找到帧尾 STOP_BYTE，跳过。")
                break
        # 检测文本帧（如 TEMP=xx.x）
        elif 0x20 <= data[i] <= 0x7E or data[i] in (0x0D, 0x0A):
            text_data = b""
            while i < len(data) and (0x20 <= data[i] <= 0x7E or data[i] in (0x0D, 0x0A)):
                text_data += bytes([data[i]])
                i += 1
            text_str = text_data.decode(errors='ignore').strip()
            if text_str:
                responses.append(f"[TEMP] {text_str}")
        else:
            i += 1
    return "\n".join(responses)

class SerialWorker(threading.Thread):
    """后台线程持续监听串口"""
    def __init__(self, ser):
        super().__init__()
        self.ser = ser
        self.running = True

    def run(self):
        print("[THREAD] 串口监听线程已启动。")
        while self.running:
            try:
                if self.ser.in_waiting:
                    data = self.ser.read_all()
                    result = parse_response(data)
                    if result:
                        print(result)
                time.sleep(0.2)
            except Exception as e:
                print(f"[ERROR] 串口监听异常: {e}")
                break
        print("[THREAD] 串口监听线程已结束。")

    def stop(self):
        self.running = False

def send_command(ser, cmd_bytes, wait_response=True):
    """发送命令，可选择是否等待响应"""
    cmd_frame = build_command(cmd_bytes)
    print(f"[SEND] {cmd_frame.hex(' ').upper()}")
    ser.write(cmd_frame)
    if not wait_response:
        return
    time.sleep(0.3)
    if ser.in_waiting:
        resp = ser.read_all()
        print(f"[RECV] {resp.hex(' ').upper()}")
        print(parse_response(resp))
    else:
        print("[WARN] 未收到下位机响应")

def test_serial(port="/dev/cu.usbserial-1130", baud=9600):
    """测试通信流程"""
    try:
        ser = serial.Serial(port, baud, timeout=1)
        print(f"[OK] 已连接串口: {port} @ {baud}bps")

        print("\n>>> 发送 TEMP采集开始 <<<")
        send_command(ser, CMD_TEMP_START, wait_response=False)

        # 启动监听线程
        listener = SerialWorker(ser)
        listener.start()

        print("[INFO] 正在持续监听温度数据，按 Ctrl+C 停止...")
        time.sleep(5)  # 模拟监听一段时间

        print("\n>>> 发送 TEMP采集结束 <<<")
        send_command(ser, CMD_TEMP_STOP, wait_response=True)

        listener.stop()
        listener.join()

    except serial.SerialException as e:
        print(f"[ERROR] 串口连接失败: {e}")
    except KeyboardInterrupt:
        print("\n[STOP] 用户中断测试。")
    finally:
        try:
            ser.close()
            print("[CLOSE] 串口已关闭。")
        except Exception:
            pass

if __name__ == "__main__":
    test_serial()
