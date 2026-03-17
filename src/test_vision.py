from vision_engine import VersaiOSVision
from ai_brain import VersaiOSAgent
from config import get_llm_api_key, get_llm_provider, get_llm_model, get_llm_base_url, get_window_title
from PIL import ImageDraw
import time
import logging
from logging_setup import setup_logging


setup_logging()
logger = logging.getLogger(__name__)


def main():
    api_key = get_llm_api_key()
    if not api_key:
        logger.error(
            "未配置 LLM API Key。请设置环境变量 VERSAIOS_LLM_API_KEY 或在 src/config.ini 中配置 llm_api_key。"
        )
        return

    vision = VersaiOSVision(window_title=get_window_title())
    agent = VersaiOSAgent(
        provider=get_llm_provider(),
        api_key=api_key,
        model_name=get_llm_model(),
        base_url=get_llm_base_url(),
    )

    logger.info("等待投屏画面稳定... (请确保投屏窗口没有被最小化)")
    time.sleep(2)

    frame = vision.grab_frame_for_ai()

    if frame is None:
        logger.warning("未抓取到画面，请检查窗口名称或状态。")
        return

    logger.info("成功截取当前画面，尺寸: %s", frame.size)

    instruction = "请帮我点击屏幕中的 '微信' 图标。"
    plan = agent.analyze_ui_and_plan(frame, instruction)

    if plan and "x_ratio" in plan and "y_ratio" in plan:
        window_width = frame.width
        window_height = frame.height

        target_x = int(window_width * plan["x_ratio"])
        target_y = int(window_height * plan["y_ratio"])

        logger.info("=====================================")
        logger.info("执行指令坐标点: X=%s, Y=%s", target_x, target_y)
        if plan.get("reason"):
            logger.info("原因: %s", plan.get("reason", ""))
        logger.info("=====================================")

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
    else:
        logger.warning("AI plan 无效，无法绘制验证点。plan=%r", plan)


if __name__ == "__main__":
    main()