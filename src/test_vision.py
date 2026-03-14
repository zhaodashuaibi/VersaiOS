from vision_engine import VersaiOSVision
from ai_brain import VersaiOSAgent
from config import get_api_key, get_window_title
from PIL import ImageDraw
import time


def main():
    api_key = get_api_key()
    if not api_key:
        print("❌ 未配置 API Key。请设置环境变量 VERSAIOS_API_KEY 或在 src/config.ini 中配置 api_key。")
        return

    vision = VersaiOSVision(window_title=get_window_title())
    agent = VersaiOSAgent(api_key=api_key)

    print("等待投屏画面稳定... (请确保投屏窗口没有被最小化)")
    time.sleep(2)

    frame = vision.grab_frame_for_ai()

    if frame is None:
        print("未抓取到画面，请检查窗口名称或状态。")
        return

    print(f"成功截取当前画面，尺寸: {frame.size}")

    instruction = "请帮我点击屏幕中的 '微信' 图标。"
    plan = agent.analyze_ui_and_plan(frame, instruction)

    if plan and "x_ratio" in plan and "y_ratio" in plan:
        window_width = frame.width
        window_height = frame.height

        target_x = int(window_width * plan["x_ratio"])
        target_y = int(window_height * plan["y_ratio"])

        print(f"\n=====================================")
        print(f"🎯 [执行指令] 坐标点为: X={target_x}, Y={target_y}")
        print(f"   [原 因] {plan.get('reason', '')}")
        print(f"=====================================\n")

        # --- 核心调试模块：画红圈验证 ---
        draw = ImageDraw.Draw(frame)
        r = 15  # 红圈的半径

        # 在目标坐标画一个红色的圆圈，线宽为 5
        draw.ellipse(
            (target_x - r, target_y - r, target_x + r, target_y + r),
            outline="red",
            width=5
        )

        # 保存并自动打开这张带有红圈的图
        frame.save("debug_target_result.png")
        frame.show()


if __name__ == "__main__":
    main()