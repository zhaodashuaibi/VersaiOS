import serial
import time


def fire_click(com_port):
    print(f">>> [VersaiOS] 正在接管底层通信总线: {com_port} ...")
    try:
        # 建立串口连接，波特率必须和 Arduino 里写的 115200 保持一致
        esp32 = serial.Serial(com_port, 115200, timeout=1)

        # 极其关键：打开串口后，ESP32 会自动重启一次，必须休眠 2 秒等它稳住
        time.sleep(2)

        print(">>> [VersaiOS] 神经链路已就绪，发送物理点击指令！")

        # 发送我们在 C++ 里约定好的暗号 "CLICK\n"
        esp32.write("CLICK\n".encode('utf-8'))

        # 等待一小会儿确保数据发完
        time.sleep(0.5)
        esp32.close()
        print(">>> [VersaiOS] 指令已成功发送。")

    except serial.SerialException:
        print(f"❌ 串口连接失败！请确认 {com_port} 是否正确，且没有被 Arduino 的串口监视器占用。")


if __name__ == "__main__":
    # ⚠️ 请把这里的 'COM3' 换成你刚才烧录代码时用的真实 COM 口！
    fire_click('COM3')