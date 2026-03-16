from vision_engine import VersaiOSVision
from ai_brain import VersaiOSAgent
from config import get_api_key, get_com_port, get_window_title, get_hid_max_x, get_hid_max_y
from logging_setup import setup_logging
import logging
import serial
import time
from typing import Any, Dict, Optional, Tuple


setup_logging()
logger = logging.getLogger(__name__)


def _validate_plan_for_actuation(plan: Any) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not isinstance(plan, dict):
        return None, "plan_not_dict"
    if "x_ratio" not in plan or "y_ratio" not in plan:
        return None, "missing_required_fields"
    try:
        x = float(plan["x_ratio"])
        y = float(plan["y_ratio"])
    except Exception as e:
        return None, f"ratio_not_number: {e}"
    if not (0.0 <= x <= 1.0) or not (0.0 <= y <= 1.0):
        return None, f"ratio_out_of_range x={x} y={y}"
    reason = plan.get("reason", None)
    if reason is not None and not isinstance(reason, str):
        return None, "reason_not_string"
    return {"x_ratio": x, "y_ratio": y, **({"reason": reason} if reason is not None else {})}, None


def main():
    logger.info("==================================================")
    logger.info("        VersaiOS AI Agent 已启动       ")
    logger.info("==================================================")

    api_key = get_api_key()
    if not api_key:
        logger.error("未配置 Gemini API Key。请任选其一：")
        logger.error("1) 设置环境变量: set VERSAIOS_API_KEY=你的Key")
        logger.error("2) 在 src 目录下创建 config.ini，写入 [versaios] 段和 api_key=你的Key")
        return

    com_port = get_com_port()
    window_title = get_window_title()

    # 1. 挂载物理机械手 (在循环外只连接一次，防止单片机反复重启)
    try:
        logger.info("正在接通物理神经链路。com_port=%s", com_port)
        esp32 = serial.Serial(com_port, 115200, timeout=1)  # 外部资源：串口打开
        time.sleep(2)  # 给 ESP32 两秒钟重启和重连蓝牙的时间
        logger.info("机械手已就绪。")
    except Exception:
        logger.exception("机械手连接失败。com_port=%s", com_port)
        return

    # 2. 初始化眼睛和大脑
    vision = VersaiOSVision(window_title=window_title)
    agent = VersaiOSAgent(api_key=api_key)

    # 3. 进入无限循环模式
    try:
        while True:
            logger.info("-" * 50)
            instruction = input("请下达指令 (输入 'q' 退出): ")

            if instruction.lower() in ['q', 'quit', 'exit', '退出']:
                logger.info("收到退出指令，准备关闭系统。")
                break

            if not instruction.strip():
                continue

            logger.info("正在抓取当前画面。window_title=%r", window_title)
            frame = vision.grab_frame_for_ai()
            if frame is None:
                logger.warning("未抓取到画面，请检查投屏窗口状态。")
                continue

            # 4. 大脑进行空间推理
            plan = agent.analyze_ui_and_plan(frame, instruction)

            safe_plan, err = _validate_plan_for_actuation(plan)
            if safe_plan:
                hid_max_x = get_hid_max_x()
                hid_max_y = get_hid_max_y()
                target_x = int(hid_max_x * safe_plan["x_ratio"])
                target_y = int(hid_max_y * safe_plan["y_ratio"])

                logger.info(
                    "AI 决策：x_ratio=%.4f y_ratio=%.4f -> 绝对步数=(%s,%s)",
                    safe_plan["x_ratio"],
                    safe_plan["y_ratio"],
                    target_x,
                    target_y,
                )
                if safe_plan.get("reason"):
                    logger.info("AI 思考：%s", safe_plan.get("reason"))

                # 5. 指挥机械手开火！
                command = f"CLICK:{target_x},{target_y}\n"
                try:
                    esp32.write(command.encode("utf-8"))  # 外部资源：串口写
                except Exception:
                    logger.exception("串口写入失败，已跳过本次动作。command=%r", command)
                    continue

                logger.info("动作已执行，等待画面响应。")
                time.sleep(1.5)  # 给手机一点时间响应（比如App打开的动画时间）
            else:
                logger.warning("AI plan 无效（%s），已阻止串口下发。plan=%r", err, plan)

    except KeyboardInterrupt:
        logger.info("被用户强制中断（KeyboardInterrupt）。")
    finally:
        # 无论如何，退出前优雅地关闭串口
        logger.info("正在断开机械手。")
        try:
            esp32.close()  # 外部资源：串口关闭
        except Exception:
            logger.exception("串口关闭失败。")
        logger.info("VersaiOS 已安全关闭。")


if __name__ == "__main__":
    main()