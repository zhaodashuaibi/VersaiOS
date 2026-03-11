import serial
import time

# ⚠️ 填入你的真实串口号
COM_PORT = "COM3"


def main():
    print(">>> [VersaiOS] 正在连接 ESP32 机械手...")
    try:
        esp32 = serial.Serial(COM_PORT, 115200, timeout=1)
        time.sleep(2)
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return

    print("\n===========================================")
    print("      🎯 欢迎进入 iOS 鼠标极限步数校准系统      ")
    print("===========================================")
    print("玩法：我们会向手机发送一个极限坐标 (比如 X=250)。")
    print("观察你的手机屏幕，看看光标是不是刚好碰到了屏幕的最右侧边缘。")
    print("如果光标没碰到边缘，说明数字太小；如果光标卡在边缘且感觉‘撞墙’了，说明数字太大。")
    print("===========================================\n")

    while True:
        try:
            # 让你手动输入测试的 X 和 Y 步数
            test_x = int(input("请输入测试 X 轴步数 (猜想值 140): "))
            test_y = int(input("请输入测试 Y 轴步数 (猜想值 310): "))

            command = f"CLICK:{test_x},{test_y}\n"
            esp32.write(command.encode('utf-8'))
            print(f">>> 发送指令: 移动到步数 ({test_x}, {test_y}) 并点击...")
            time.sleep(1)

            print("👉 请观察手机屏幕光标位置！\n")

        except ValueError:
            print("退出校准程序。")
            break

    esp32.close()


if __name__ == "__main__":
    main()