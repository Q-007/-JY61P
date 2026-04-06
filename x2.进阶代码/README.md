# JY61P 陀螺仪网页监测系统（树莓派GPIO UART版）

## 简介

这是一个基于Python和Flask的JY61P陀螺仪实时监测系统，专为树莓派5设计，使用GPIO硬件串口（UART）直接连接，提供Web界面显示6轴姿态传感器数据。

## 功能特性

- ✅ **GPIO UART通信** - 直接使用树莓派GPIO引脚连接，无需USB转串口
- ✅ **自动检测波特率** - 自动识别陀螺仪波特率
- ✅ **实时数据显示** - 实时更新所有传感器数据
- ✅ **3D姿态可视化** - 使用Canvas绘制3D立方体显示姿态
- ✅ **角度折线图** - 实时绘制Roll/Pitch/Yaw角度趋势图
- ✅ **多数据监测** - 加速度、角速度、角度、温度
- ✅ **美观界面** - 现代化的Web界面设计
- ✅ **WebSocket通信** - 低延迟实时数据传输

## 系统要求

- 树莓派5（或其他树莓派型号）
- Python 3.7+
- JY61P 陀螺仪设备

## 安装步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启用树莓派串口

需要启用UART4（GPIO 12/13）用于陀螺仪：

```bash
# 编辑配置文件
sudo nano /boot/firmware/config.txt

# 添加以下行以启用UART4
enable_uart=1
dtoverlay=uart4

# 保存并重启
sudo reboot

# 验证UART4是否启用
ls -l /dev/ttyAMA4
# 应该显示串口设备信息
```

**注意：** 使用UART4（GPIO 12/13）可以避免与GPS模块占用的UART0（GPIO 14/15）冲突。

### 3. 连接硬件

将JY61P陀螺仪直接连接到树莓派GPIO引脚：

| JY61P引脚 | 树莓派GPIO引脚 | 说明 |
|----------|--------------|------|
| VCC      | Pin 2 (5V) | 电源（推荐5V） |
| GND      | Pin 6 (GND)  | 地线 |
| TX       | Pin 33 (GPIO 13, UART4_RXD) | 陀螺仪发送 → 树莓派接收 |
| RX       | Pin 32 (GPIO 12, UART4_TXD)  | 陀螺仪接收 ← 树莓派发送 |

**重要提示：**
- JY61P的TX连接到树莓派的RX（GPIO 13, Pin 33）
- JY61P的RX连接到树莓派的TX（GPIO 12, Pin 32）
- 使用UART4（GPIO 12/13），避开了GPS占用的UART0（GPIO 14/15）
- 确保供电电压正确（JY61P支持3.3V-5V，推荐5V）

### 4. 运行程序

```bash
python main.py
```

程序会自动检测JY61P设备的波特率。

### 5. 访问网页

在浏览器中打开：
```
http://localhost:5000
```

## 配置说明

### 自动检测波特率模式（推荐）

在 `main.py` 中保持默认设置：
```python
PORT = '/dev/ttyAMA4'  # 树莓派UART4串口（GPIO 12/13）
BAUDRATE = None        # 自动检测波特率
```

### 手动配置模式

如果自动检测失败，可以手动指定波特率：
```python
PORT = '/dev/ttyAMA4'  # UART4 (GPIO 12/13)
BAUDRATE = 9600        # JY61P默认波特率，或 115200, 230400, 460800
```

### 串口设备说明

树莓派5的串口设备：
- `/dev/ttyAMA0` - UART0（GPIO 14/15）通常被GPS占用
- `/dev/ttyAMA4` - UART4（GPIO 12/13）用于陀螺仪
- `/dev/ttyAMA5` - UART5（GPIO 16/17）未使用
- `/dev/serial0` - 串口别名，通常指向ttyAMA0

## 数据说明

### 角度 (°)
- **Roll (横滚)** - 绕X轴旋转，范围：-180° 到 +180°
- **Pitch (俯仰)** - 绕Y轴旋转，范围：-180° 到 +180°
- **Yaw (偏航)** - 绕Z轴旋转，范围：-180° 到 +180°

### 加速度 (g)
- **X/Y/Z轴** - 三轴加速度，单位：g (重力加速度)
- 静止时Z轴约为1g

### 角速度 (°/s)
- **X/Y/Z轴** - 三轴角速度，单位：度/秒
- 静止时接近0

### 温度 (°C)
- 传感器内部温度

### 角度折线图
- **实时趋势** - 显示最近100个数据点的角度变化
- **三轴同屏** - 蓝色(角度X)、绿色(角度Y)、红色(角度Z)
- **网格参考** - 每25度一条网格线
- **时间轴** - 实时时间标签

## 常见问题

### 1. 无法找到设备

**解决方案：**
- 检查GPIO连线是否正确（TX、RX不要接反）
- 确认UART4已启用：`ls -l /dev/ttyAMA4`
- 检查 `/boot/firmware/config.txt` 中是否有 `dtoverlay=uart4`
- 检查陀螺仪供电是否正常（LED应亮起）
- 尝试手动指定波特率
- 使用 `sudo dmesg | grep tty` 查看串口信息

### 2. 权限错误

如果提示权限不足：
```bash
# 方法1: 添加当前用户到dialout组
sudo usermod -a -G dialout $USER
# 然后重新登录

# 方法2: 临时使用sudo运行
sudo python main.py
```

### 3. 数据不更新

**解决方案：**
- 检查波特率设置是否正确
- 确认陀螺仪供电正常
- 检查TX/RX接线是否正确
- 重启程序

### 4. 3D模型显示不正常

**解决方案：**
- 刷新浏览器页面
- 检查浏览器控制台是否有错误
- 确认WebSocket连接成功

### 5. 串口被占用

如果提示串口被占用：
```bash
# 查看哪个进程占用串口
sudo lsof /dev/ttyAMA4

# 结束占用的进程
sudo kill -9 <进程ID>
```

### 6. 支持的波特率

JY61P支持以下波特率（出厂默认9600）：
- 9600
- 115200
- 230400
- 460800

可通过官方上位机软件修改波特率。

## 文件结构

```
x2.陀螺仪JY61P/
├── jy61p_driver.py      # JY61P驱动程序
├── main.py              # 主程序（Flask + WebSocket）
├── requirements.txt     # Python依赖
├── README.md           # 说明文档
└── templates/
    └── index.html      # Web界面
```

## 技术架构

- **后端：** Flask + Flask-SocketIO
- **前端：** HTML5 + Canvas + Socket.IO
- **串口通信：** PySerial
- **实时通信：** WebSocket

## 数据协议

JY61P使用标准的WitMotion协议：
- 数据包长度：11字节
- 包头：0x55
- 数据类型：
  - 0x51 - 加速度
  - 0x52 - 角速度
  - 0x53 - 角度
  - 0x54 - 磁场
- 校验：简单和校验

## 许可证

MIT License

## 参考资料

- [JY61P官方文档](http://wit-motion.yuque.com/wumwnr/docs/np25sf)
- [WitMotion产品资料](https://wit-motion.com)

## 作者

智能小车项目组

## 更新日志

### v2.0.0 (2025-10-28)
- ✨ 改用树莓派GPIO UART通信，无需USB转串口
- ✨ 优化初始化流程，自动检测波特率
- 📝 更新文档，增加GPIO连接说明
- 📝 增加树莓派串口配置指南

### v1.0.0 (2025-01-28)
- ✨ 初始版本发布
- ✨ 支持自动设备检测
- ✨ 实时3D姿态显示
- ✨ 完整的9轴数据监测

