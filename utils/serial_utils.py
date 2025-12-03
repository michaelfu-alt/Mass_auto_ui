"""
串口通信工具函数和常量
"""
# 串口通信协议常量
START_BYTE = 0x73
STOP_BYTE = 0x65
CMD_TEMP_START = [0x01, 0x01]
CMD_TEMP_STOP = [0x00, 0x01]


def calc_checksum(data_bytes):
    """计算校验和"""
    checksum = sum(data_bytes) & 0xFFFF
    high = (checksum >> 8) & 0xFF
    low = checksum & 0xFF
    return high, low


def build_command(cmd_bytes):
    """构建命令帧"""
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

