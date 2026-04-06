"""
JY61P 陀螺仪主程序（网页版）
实时显示陀螺仪数据和3D姿态
"""

import threading
import signal
import sys
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from jy61p_driver import JY61P


# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'jy61p_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


class GyroApplication:
    """陀螺仪应用主类（网页版）"""
    
    def __init__(self, port='/dev/ttyAMA4', baudrate=None):
        """
        初始化应用
        
        Args:
            port: 串口设备路径，默认为树莓派UART4串口 (GPIO 12/13)
            baudrate: 波特率，None则自动检测
        """
        self.port = port
        self.baudrate = baudrate
        
        # 创建陀螺仪驱动
        self.gyro = JY61P(port=port, baudrate=baudrate)
        
        # 控制标志
        self.running = False
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """处理Ctrl+C信号"""
        print("\n\n接收到中断信号，正在安全退出...")
        self.stop()
        sys.exit(0)
    
    def _data_callback(self, data):
        """
        数据更新回调
        
        Args:
            data: 陀螺仪数据字典
        """
        try:
            # 通过WebSocket发送数据到前端
            socketio.emit('gyro_data', data, namespace='/')
        except Exception as e:
            print(f"数据广播错误: {e}")
    
    def start(self):
        """启动陀螺仪读取"""
        # 连接陀螺仪
        if not self.gyro.connect():
            print("无法连接陀螺仪，程序退出")
            return False
        
        # 启动数据读取
        self.running = True
        self.gyro.start_reading(callback=self._data_callback)
        
        print("\n陀螺仪数据读取已启动...")
        print("请在浏览器中访问 http://localhost:5000 查看实时数据")
        print("按 Ctrl+C 停止\n")
        
        return True
    
    def stop(self):
        """停止应用"""
        if not self.running:
            return
        
        print("\n正在停止...")
        self.running = False
        
        # 停止陀螺仪
        self.gyro.stop_reading()
        
        # 断开连接
        self.gyro.disconnect()
        
        print("\n陀螺仪已安全停止")


# 全局陀螺仪应用实例
gyro_app = None


@app.route('/')
def index():
    """主页路由"""
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    """客户端连接事件"""
    print(f"客户端已连接")
    
    # 发送当前数据
    if gyro_app and gyro_app.running:
        current_data = gyro_app.gyro.get_data()
        emit('gyro_data', current_data)


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开事件"""
    print(f"客户端已断开")


@socketio.on('request_data')
def handle_data_request():
    """客户端请求数据"""
    if gyro_app and gyro_app.running:
        current_data = gyro_app.gyro.get_data()
        emit('gyro_data', current_data)


def main():
    """主函数"""
    global gyro_app
    
    # 配置参数（树莓派GPIO UART模式）
    # 方式1: 自动检测波特率（推荐）
    PORT = '/dev/ttyAMA4'  # 树莓派UART4串口（GPIO 12/13, Pin 32/33）
    BAUDRATE = None  # 自动检测波特率
    
    # 方式2: 手动指定波特率（如果自动检测失败）
    # PORT = '/dev/ttyAMA4'  # UART4 (GPIO 12/13)
    # BAUDRATE = 9600  # JY61P默认波特率，或 115200, 230400, 460800
    
    print("=" * 60)
    print("JY61P 陀螺仪驱动程序（树莓派GPIO UART版）")
    print("实时显示6轴姿态数据")
    print("=" * 60)
    
    # 创建陀螺仪应用
    try:
        gyro_app = GyroApplication(port=PORT, baudrate=BAUDRATE)
        
        # 启动陀螺仪
        if gyro_app.start():
            # 启动Flask服务器
            print("\n正在启动Web服务器...")
            print("=" * 60)
            socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        else:
            print("陀螺仪启动失败")
            
    except KeyboardInterrupt:
        print("\n程序被中断")
    except Exception as e:
        print(f"\n程序异常: {e}")
        print("\n提示:")
        print("  1. 检查陀螺仪是否正确连接到GPIO UART引脚")
        print("  2. 确认树莓派串口已启用: sudo raspi-config -> Interface Options -> Serial Port")
        print("  3. 如果自动检测失败，可在main.py中手动指定波特率")
        import traceback
        traceback.print_exc()
    finally:
        if gyro_app:
            gyro_app.stop()


if __name__ == "__main__":
    main()

