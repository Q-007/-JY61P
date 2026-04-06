"""
JY61P 陀螺仪驱动程序
支持6轴姿态传感器数据读取
"""

import serial
import serial.tools.list_ports
import struct
import time
import threading


class JY61P:
    """JY61P 陀螺仪驱动类"""
    
    # 数据包头
    HEADER = 0x55
    
    # 数据类型
    TYPE_TIME = 0x50
    TYPE_ACC = 0x51      # 加速度
    TYPE_GYRO = 0x52     # 角速度
    TYPE_ANGLE = 0x53    # 角度
    TYPE_MAG = 0x54      # 磁场
    
    # 支持的波特率
    SUPPORTED_BAUDRATES = [9600, 115200, 230400, 460800]
    
    # 树莓派硬件串口设备
    RPI_UART_DEVICES = ['/dev/ttyAMA0', '/dev/ttyAMA4', '/dev/ttyAMA5', '/dev/serial0']
    
    @staticmethod
    def detect_baudrate(port='/dev/ttyAMA4'):
        """
        检测JY61P设备的波特率（树莓派GPIO UART模式）
        
        Args:
            port: 串口设备路径，默认为树莓派UART4硬件串口
        
        Returns:
            波特率，如果未找到返回 None
        """
        print(f"\n=== 检测JY61P陀螺仪波特率 ===")
        print(f"串口: {port}")
        
        # 尝试不同波特率
        for baudrate in JY61P.SUPPORTED_BAUDRATES:
            ser = None
            try:
                print(f"正在测试波特率: {baudrate}...")
                
                # 尝试连接
                ser = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    timeout=0.5,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS
                )
                time.sleep(0.2)
                ser.reset_input_buffer()
                
                # 读取数据尝试识别JY61P
                data = ser.read(100)
                
                # 检查是否包含JY61P特征数据包（0x55开头）
                if len(data) >= 11:
                    for i in range(len(data) - 10):
                        if data[i] == 0x55 and data[i+1] in [0x51, 0x52, 0x53, 0x54]:
                            print(f"  [OK] 找到JY61P! 波特率: {baudrate}")
                            print(f"    数据包头: 0x{data[i]:02X} 0x{data[i+1]:02X}")
                            
                            ser.close()
                            
                            print(f"\n=== 检测成功 ===")
                            print(f"波特率: {baudrate}")
                            print("=" * 40)
                            
                            return baudrate
                
                ser.close()
                
            except Exception as e:
                # 忽略连接失败，继续尝试
                if ser and ser.is_open:
                    ser.close()
                pass
        
        print("\n⚠ 未找到JY61P设备")
        print("请检查:")
        print("  1. 陀螺仪是否已正确连接到GPIO UART引脚")
        print("  2. 树莓派串口是否已启用 (sudo raspi-config)")
        print("  3. 陀螺仪供电是否正常")
        print("  4. TX/RX引脚是否接反")
        return None
    
    def __init__(self, port='/dev/ttyAMA4', baudrate=None, timeout=1):
        """
        初始化陀螺仪驱动（树莓派GPIO UART模式）
        
        Args:
            port: 串口设备路径，默认为树莓派UART4串口 /dev/ttyAMA4 (GPIO 12/13)
            baudrate: 波特率，None则自动检测
            timeout: 超时时间（秒）
        """
        self.port = port
        
        # 如果未指定波特率，自动检测
        if baudrate is None:
            print(f"未指定波特率，开始自动检测...")
            detected_baudrate = self.detect_baudrate(port)
            if detected_baudrate is None:
                raise Exception(f"无法检测到JY61P设备在 {port}，请检查连接或手动指定波特率")
            self.baudrate = detected_baudrate
        else:
            self.baudrate = baudrate
        
        self.timeout = timeout
        self.serial = None
        self.is_reading = False
        self.data_thread = None
        
        # 数据缓存
        self.data = {
            'acc': {'x': 0, 'y': 0, 'z': 0},           # 加速度 (g)
            'gyro': {'x': 0, 'y': 0, 'z': 0},          # 角速度 (°/s)
            'angle': {'roll': 0, 'pitch': 0, 'yaw': 0}, # 角度 (°)
            'mag': {'x': 0, 'y': 0, 'z': 0},           # 磁场
            'temperature': 0                            # 温度 (°C)
        }
        
        self.data_lock = threading.Lock()
        self.data_callback = None
        
    def connect(self):
        """连接陀螺仪"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            time.sleep(0.5)  # 等待串口稳定
            print(f"成功连接到陀螺仪: {self.port}, 波特率: {self.baudrate}")
            
            # 清空缓冲区
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        self.stop_reading()
        
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("陀螺仪连接已断开")
    
    def start_reading(self, callback=None):
        """
        启动数据读取线程
        
        Args:
            callback: 数据更新回调函数，参数为最新的data字典
        """
        if self.is_reading:
            return
        
        self.data_callback = callback
        self.is_reading = True
        self.data_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.data_thread.start()
        print("开始读取陀螺仪数据...")
    
    def stop_reading(self):
        """停止数据读取"""
        if not self.is_reading:
            return
        
        print("停止读取数据...")
        self.is_reading = False
        
        if self.data_thread and self.data_thread.is_alive():
            self.data_thread.join(timeout=2)
    
    def _read_loop(self):
        """数据读取循环（在独立线程中运行）"""
        buffer = bytearray()
        
        while self.is_reading:
            try:
                # 读取可用数据
                if self.serial.in_waiting > 0:
                    buffer.extend(self.serial.read(self.serial.in_waiting))
                    
                    # 处理缓冲区中的数据包
                    while len(buffer) >= 11:
                        # 查找包头
                        if buffer[0] == self.HEADER:
                            # 验证数据包长度
                            if len(buffer) >= 11:
                                packet = buffer[:11]
                                
                                # 校验和验证
                                if self._verify_checksum(packet):
                                    self._parse_packet(packet)
                                    buffer = buffer[11:]
                                else:
                                    # 校验失败，丢弃第一个字节
                                    buffer = buffer[1:]
                            else:
                                # 数据不够，等待更多数据
                                break
                        else:
                            # 不是包头，丢弃第一个字节
                            buffer = buffer[1:]
                else:
                    time.sleep(0.001)  # 短暂休眠，避免占用过多CPU
                    
            except Exception as e:
                print(f"数据读取错误: {e}")
                time.sleep(0.1)
    
    def _verify_checksum(self, packet):
        """
        验证数据包校验和
        
        Args:
            packet: 11字节数据包
            
        Returns:
            校验是否通过
        """
        if len(packet) != 11:
            return False
        
        # 计算校验和（前10个字节的和）
        checksum = sum(packet[:10]) & 0xFF
        
        return checksum == packet[10]
    
    def _parse_packet(self, packet):
        """
        解析数据包
        
        Args:
            packet: 11字节数据包
        """
        data_type = packet[1]
        
        with self.data_lock:
            if data_type == self.TYPE_ACC:
                # 加速度数据
                acc_x = struct.unpack('<h', packet[2:4])[0] / 32768.0 * 16  # g
                acc_y = struct.unpack('<h', packet[4:6])[0] / 32768.0 * 16
                acc_z = struct.unpack('<h', packet[6:8])[0] / 32768.0 * 16
                temp = struct.unpack('<h', packet[8:10])[0] / 100.0  # °C
                
                self.data['acc'] = {'x': acc_x, 'y': acc_y, 'z': acc_z}
                self.data['temperature'] = temp
                
            elif data_type == self.TYPE_GYRO:
                # 角速度数据
                gyro_x = struct.unpack('<h', packet[2:4])[0] / 32768.0 * 2000  # °/s
                gyro_y = struct.unpack('<h', packet[4:6])[0] / 32768.0 * 2000
                gyro_z = struct.unpack('<h', packet[6:8])[0] / 32768.0 * 2000
                
                self.data['gyro'] = {'x': gyro_x, 'y': gyro_y, 'z': gyro_z}
                
            elif data_type == self.TYPE_ANGLE:
                # 角度数据
                roll = struct.unpack('<h', packet[2:4])[0] / 32768.0 * 180   # °
                pitch = struct.unpack('<h', packet[4:6])[0] / 32768.0 * 180
                yaw = struct.unpack('<h', packet[6:8])[0] / 32768.0 * 180
                
                self.data['angle'] = {'roll': roll, 'pitch': pitch, 'yaw': yaw}
                
            elif data_type == self.TYPE_MAG:
                # 磁场数据
                mag_x = struct.unpack('<h', packet[2:4])[0]
                mag_y = struct.unpack('<h', packet[4:6])[0]
                mag_z = struct.unpack('<h', packet[6:8])[0]
                
                self.data['mag'] = {'x': mag_x, 'y': mag_y, 'z': mag_z}
        
        # 触发回调
        if self.data_callback:
            self.data_callback(self.get_data())
    
    def get_data(self):
        """
        获取当前数据
        
        Returns:
            包含所有传感器数据的字典
        """
        with self.data_lock:
            return self.data.copy()
    
    def __enter__(self):
        """支持with语句"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持with语句"""
        self.disconnect()

