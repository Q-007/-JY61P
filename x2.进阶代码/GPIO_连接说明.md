# JY61P 陀螺仪 GPIO 连接说明

## 树莓派5 GPIO引脚定义

```
树莓派5 GPIO引脚布局 (40针)
  3.3V [ 1]  [ 2] 5V          ← JY61P VCC连接这里
       [ 3]  [ 4] 5V
       [ 5]  [ 6] GND         ← JY61P GND连接这里
       [ 7]  [ 8] GPIO 14     (UART0_TXD，用于GPS)
   GND [ 9]  [10] GPIO 15     (UART0_RXD，用于GPS)
       ... 其他引脚 ...
       ... 其他引脚 ...
       ... 其他引脚 ...
       ... 其他引脚 ...
       ... [32] GPIO 12       ← JY61P RX连接这里 (UART4_TXD)
       ... [33] GPIO 13       ← JY61P TX连接这里 (UART4_RXD)
```

## 连接方式

### 标准连接（UART4，推荐）

| JY61P引脚 | 连接到 | 树莓派引脚 | 备注 |
|----------|-------|-----------|------|
| **VCC** (红色) | → | **Pin 2** (5V) | 电源正极 |
| **GND** (黑色) | → | **Pin 6** (GND) | 电源负极/地线 |
| **TX** (蓝色) | → | **Pin 33** (GPIO 13, UART4_RXD) | 陀螺仪发送数据 |
| **RX** (绿色) | → | **Pin 32** (GPIO 12, UART4_TXD) | 陀螺仪接收数据 |

### 关键要点

1. **TX接RX，RX接TX**
   - JY61P的TX（发送）接树莓派的RX（接收，GPIO 13, Pin 33）
   - JY61P的RX（接收）接树莓派的TX（发送，GPIO 12, Pin 32）

2. **使用UART4避免冲突**
   - GPIO 12/13 是 UART4，设备路径为 `/dev/ttyAMA4`
   - GPIO 14/15 是 UART0，通常被GPS模块占用
   - 使用UART4可以避免与GPS模块冲突

2. **电源选择**
   - 推荐使用5V供电（Pin 2或Pin 4）
   - 也可使用3.3V（Pin 1），但某些情况下可能供电不足

3. **GND连接**
   - 必须连接GND，确保共地
   - 可选择Pin 6, 9, 14, 20, 25, 30, 34, 39任一GND引脚

## 串口设备路径

树莓派5上JY61P陀螺仪使用的串口设备：
- **主串口**: `/dev/ttyAMA4` （UART4，GPIO 12/13）
- **说明**: 使用UART4避免与GPS模块占用的UART0（GPIO 14/15）冲突

## 启用串口

在使用前必须先启用树莓派的硬件串口：

### 启用UART4（GPIO 12/13）

```bash
# 编辑config.txt
sudo nano /boot/firmware/config.txt

# 添加以下行以启用UART4：
enable_uart=1
dtoverlay=uart4

# 保存并重启
sudo reboot
```

**重要说明：**
- `enable_uart=1` 启用所有UART接口
- `dtoverlay=uart4` 启用UART4，将GPIO 12/13配置为串口
- 使用UART4可以避免与GPS占用的UART0（GPIO 14/15）冲突

### 验证串口是否启用

```bash
# 检查UART4设备是否存在
ls -l /dev/ttyAMA4

# 查看串口信息
sudo dmesg | grep tty

# 应该看到类似输出：
# Serial: AMBA PL011 UART driver
# 或 uart-pl011 相关信息
```

## 测试连接

### 1. 检查硬件连接

```bash
# 安装minicom（如未安装）
sudo apt-get install minicom

# 测试UART4串口通信
sudo minicom -b 9600 -D /dev/ttyAMA4

# 如果看到乱码或数据流，说明连接正常
# 按 Ctrl+A 然后 X 退出
```

### 2. 运行陀螺仪程序

```bash
cd /path/to/x2.进阶代码
python main.py
```

## 常见问题

### 问题1: 权限错误

```bash
# 将当前用户添加到dialout组
sudo usermod -a -G dialout $USER

# 然后重新登录或重启
```

### 问题2: 无法读取数据

检查：
1. TX/RX是否接反？确认JY61P的TX接GPIO 13，RX接GPIO 12
2. GND是否连接？
3. 供电是否正常？（LED是否亮）
4. UART4是否启用？（`ls -l /dev/ttyAMA4`）
5. `/boot/firmware/config.txt`中是否有 `dtoverlay=uart4`

### 问题3: 串口被占用

```bash
# 查看占用UART4的进程
sudo lsof /dev/ttyAMA4

# 结束占用的进程
sudo kill -9 <进程ID>
```

### 问题4: UART4未启用

如果 `/dev/ttyAMA4` 不存在：

```bash
# 检查配置
cat /boot/firmware/config.txt | grep uart

# 确认有以下配置：
# enable_uart=1
# dtoverlay=uart4

# 如果缺少，添加后重启
sudo reboot
```

## 接线示意图

```
    JY61P 陀螺仪                    树莓派5
   ┌─────────────┐              ┌──────────┐
   │             │              │          │
   │  [VCC]  ────┼──────────────┤ Pin 2    │  5V
   │             │              │ (5V)     │
   │  [GND]  ────┼──────────────┤ Pin 6    │  GND
   │             │              │ (GND)    │
   │  [TX]   ────┼──────────────┤ Pin 33   │  GPIO 13 (UART4_RXD)
   │             │              │          │
   │  [RX]   ────┼──────────────┤ Pin 32   │  GPIO 12 (UART4_TXD)
   │             │              │          │
   └─────────────┘              └──────────┘
   
注意：使用UART4 (GPIO 12/13) 避免与GPS的UART0 (GPIO 14/15) 冲突
```

## 技术参数

- **串口协议**: UART
- **电压**: 3.3V - 5V
- **波特率**: 9600 / 115200 / 230400 / 460800（出厂默认9600）
- **数据位**: 8
- **停止位**: 1
- **校验位**: None

## 相关文档

- [主程序README](./README.md)
- [JY61P数据手册](http://wit-motion.yuque.com/wumwnr/docs/np25sf)

