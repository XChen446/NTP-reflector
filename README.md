# NTP反射测试工具

## 法律及免责声明

### 重要法律声明

**使用此工具进行未经授权的测试可能违反当地法律和网络使用政策。** NTP反射攻击通常被视为分布式拒绝服务(DDoS)攻击的一种形式，在许多国家和地区属于违法行为。

### 授权要求

在使用本工具之前，您必须：

1. 获得目标系统所有者的明确书面授权
2. 确保测试不会影响任何第三方系统或网络
3. 遵守所有适用的法律法规和政策
4. 仅在您拥有或已获得明确权限的网络环境中使用

### 免责声明

本工具仅用于授权的安全测试和教育目的。作者和贡献者不对以下情况负责：

1. 未经授权使用本工具造成的任何损害
2. 违反当地法律或政策使用本工具导致的后果
3. 使用本工具时可能发生的任何意外或故意损害
4. 因使用本工具而导致的任何法律后果

使用者应自行承担使用本工具的所有风险。作者明确声明不提供任何明示或暗示的担保，包括但不限于对适销性和特定用途适用性的暗示担保。

### 道德使用准则

1. 仅在对您拥有合法权限的系统上使用本工具
2. 在进行测试前获得所有必要的授权和许可
3. 确保测试不会对第三方系统或网络造成影响
4. 测试完成后及时清理和恢复系统
5. 尊重所有适用的法律法规和道德准则

### 建议用途

1. 网络安全评估和渗透测试（在授权范围内）
2. 网络设备防护能力测试
3. 安全意识和教育培训
4. 学术研究和实验

**使用本工具即表示您已阅读、理解并同意上述免责声明和法律条款，并承诺仅在合法和授权的范围内使用本工具。**

## 项目简介

这是一个简单的NTP反射攻击测试工具，支持跨平台运行（Windows/Linux/macOS），用于测试网络设备对NTP反射攻击的防护能力。该工具支持NTP协议的7种工作模式和各种控制命令，能够模拟不同类型的NTP反射攻击。

## 功能特点

- 跨平台支持：Windows、Linux、macOS
- 支持所有NTP模式（1-7）和版本（v1-v4）
- 支持NTP控制消息命令（1-43, 128-141）
- 多线程并发攻击
- 实时性能监控和统计
- 攻击前NTP服务器支持测试
- 详细模式输出（-v参数）
- 原始套接字支持（IP欺骗）

## 环境要求

### 系统要求
- Windows 7/8/10/11 或 Linux 发行版 或 macOS 10.10+
- Python 3.6 或更高版本

### 依赖项
- 标准Python库（无额外依赖）
- 需要`ntp_packets.py`文件（与主脚本同一目录）

### 权限要求
- 原始套接字功能需要管理员/root权限
- Windows: 需要以管理员身份运行
- Linux/macOS: 需要使用sudo运行

## 安装与配置

1. 克隆或下载项目文件：
   ```
   git clone <repository-url>
   cd NTP-reflector
   ```

2. 确保`ntp_packets.py`文件存在于同一目录

3. 准备NTP服务器列表文件（每行一个NTP服务器地址）

4. 根据需要调整脚本参数

## 使用方法

### 基本用法
```bash
# Windows (需要管理员权限)
python ntp_reflector.py --target <目标IP> -f <NTP服务器列表文件>

# Linux/macOS (需要root权限)
sudo python3 ntp_reflector.py --target <目标IP> -f <NTP服务器列表文件>
```

### 常用命令示例

```bash
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
```

### 完整参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--target` | 目标服务器IP地址或域名 | 必需 |
| `-p PORT`, `--port PORT` | 目标端口 | 123 |
| `-f FILE`, `--file FILE` | NTP服务器列表文件 | 必需 |
| `-t THREADS`, `--threads THREADS` | 并发线程数 | 10 |
| `--min-delay MS` | 最小延迟(毫秒) | 0 |
| `--max-delay MS` | 最大延迟(毫秒) | 0 |
| `-d DURATION`, `--duration DURATION` | 攻击持续时间(秒) | 0 (无限) |
| `-m MODE`, `--mode MODE` | NTP模式 (1-7) | 3 |
| `-c COMMAND`, `--command COMMAND` | NTP控制消息命令 (仅模式6有效) | 无 |
| `-v VERSION`, `--version VERSION` | NTP版本 (1-4) | 4 |
| `--test-before-attack TEST` | 攻击前测试NTP服务器支持的模式 | true |
| `--stats-interval SEC` | 统计信息输出间隔(秒) | 5 |
| `--verbose` | 详细输出模式 | false |
| `-h`, `--help` | 显示帮助信息 | 无 |

## NTP模式说明

| 模式 | 名称 | 反射潜力 | 说明 |
|------|------|----------|------|
| 1 | SYMMETRIC_ACTIVE | 中等 | 对称主动模式，用于对等体间时间同步 |
| 2 | SYMMETRIC_PASSIVE | 中等 | 对称被动模式，响应对称主动请求 |
| 3 | CLIENT | 低 | 客户端模式，基本时间请求 |
| 4 | SERVER | 低到中等 | 服务器模式，响应客户端请求 |
| 5 | BROADCAST | 低 | 广播模式，定期广播时间信息 |
| 6 | NTP_CONTROL | 高到非常高 | 控制消息模式，用于监控和管理 |
| 7 | PRIVATE | 可变 | 私有模式，厂商特定扩展 |

## 注意事项

### 技术注意事项
1. 伪造源IP需要原始套接字权限，在Windows上需要管理员权限
2. 如果没有原始套接字权限，脚本将回退到普通UDP套接字，但无法伪造源IP
3. 某些网络设备可能会阻止或过滤伪造源IP的数据包
4. 不同NTP服务器可能支持不同的模式和命令
5. 现代NTP服务器通常禁用或限制MON_GETLIST和MRU_GETLIST功能
6. 建议使用`--test-before-attack`参数先测试服务器支持的模式

### 性能注意事项
1. 高线程数和大延迟范围可能会影响系统性能
2. 长时间运行可能会产生大量网络流量
3. 建议在测试环境中先进行小规模测试

### 网络注意事项
1. 反射攻击可能对网络造成严重影响，请谨慎使用
2. 确保测试不会影响生产网络环境
3. 考虑使用网络隔离环境进行测试


---

**再次强调：请负责任地使用此工具，并确保您已获得所有必要的授权和许可。**
