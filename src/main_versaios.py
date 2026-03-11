from vision_engine import VersaiOSVision
from ai_brain import VersaiOSAgent
import serial
import time
import sys

# ================= 配置区 =================
WINDOW_TITLE = "Direct3D12 Renderer"  # 投屏窗口名
API_KEY = "YOUR_API_KEY_HERE"  # Gemini API Key
COM_PORT = "COM3"  # 你的 ESP32 串口号


# ==========================================

def main():
    print("==================================================")
    print("        🚀 VersaiOS AI Agent 已启动       ")
    print("==================================================")

    # 1. 挂载物理机械手 (在循环外只连接一次，防止单片机反复重启)
    try:
        print(">>> [系统] 正在接通物理神经链路...")
        esp32 = serial.Serial(COM_PORT, 115200, timeout=1)
        time.sleep(2)  # 给 ESP32 两秒钟重启和重连蓝牙的时间
        print(">>> [系统] 机械手已就绪！")
    except Exception as e:
        print(f"❌ 机械手连接失败: {e}")
        return

    # 2. 初始化眼睛和大脑
    vision = VersaiOSVision(window_title=WINDOW_TITLE)
    agent = VersaiOSAgent(api_key=API_KEY)

    # 3. 进入无限循环模式
    try:
        while True:
            print("\n" + "-" * 50)
            instruction = input("请下达指令 (输入 'q' 退出): ")

            if instruction.lower() in ['q', 'quit', 'exit', '退出']:
                print(">>> [系统] 收到退出指令，正在关闭系统...")
                break

            if not instruction.strip():
                continue

            print(">>> [系统] 正在睁开眼睛获取当前手机画面...")
            frame = vision.grab_frame_for_ai()
            if frame is None:
                print("未抓取到画面，请检查投屏窗口状态。")
                continue

            # 4. 大脑进行空间推理
            plan = agent.analyze_ui_and_plan(frame, instruction)

            if plan and "x_ratio" in plan and "y_ratio" in plan:

                # ---  你的专属绝对物理映射 ---
                HID_MAX_X = 140
                HID_MAX_Y = 310

                target_x = int(HID_MAX_X * plan["x_ratio"])
                target_y = int(HID_MAX_Y * plan["y_ratio"])

                print(
                    f"🎯 [AI 决策] X比例:{plan['x_ratio']:.2f}, Y比例:{plan['y_ratio']:.2f} -> 绝对步数:({target_x},{target_y})")
                print(f"💡 [AI 思考] {plan.get('reason', '')}")

                # 5. 指挥机械手开火！
                command = f"CLICK:{target_x},{target_y}\n"
                esp32.write(command.encode('utf-8'))

                print(">>> [系统] 动作已执行，等待画面响应...")
                time.sleep(1.5)  # 给手机一点时间响应（比如App打开的动画时间）
            else:
                print("⚠️ AI 未能找到目标，请尝试换一种说法。")

    except KeyboardInterrupt:
        print("\n>>> [系统] 被用户强制中断。")
    finally:
        # 无论如何，退出前优雅地关闭串口
        print(">>> [系统] 正在断开机械手...")
        esp32.close()
        print(">>> [系统] VersaiOS 已安全关闭。")


if __name__ == "__main__":
    main()