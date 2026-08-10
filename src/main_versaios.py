from vision_engine import VersaiOSVision
from ai_brain import VersaiOSAgent, validate_plan_dict
from config import (
    get_llm_api_key,
    get_llm_provider,
    get_llm_model,
    get_llm_base_url,
    get_com_port,
    get_window_title,
    get_hid_max_x,
    get_hid_max_y,
    validate_llm_config,
    is_hid_calibrated,
)
from logging_setup import setup_logging
import logging
import serial
import time
logger = logging.getLogger(__name__)

# 具体异常类型：避免 bare except 吞掉错误栈
_SERIAL_ERRORS = (serial.SerialException, PermissionError, OSError)

def main():
    logger.info("==================================================")
    logger.info("        VersaiOS AI Agent 已启动       ")
    logger.info("==================================================")

    api_key = get_llm_api_key()
    config_err = validate_llm_config()
    if config_err:
        logger.error("LLM 配置无效：%s", config_err)
        logger.error(
            "请在 src/config.ini 的 [versaios] 中配置 llm_api_key / llm_base_url，"
            "或在 GUI 阶段一填写后点击“确认并写入 config”。"
        )
        return

    com_port = get_com_port()
    window_title = get_window_title()

    if not is_hid_calibrated():
        logger.warning(
            "HID 步数尚未校准（使用默认值 %s/%s）。"
            "请点击坐标可能不准确，请在 gui_app.py『阶段一』完成校准。",
            get_hid_max_x(),
            get_hid_max_y(),
        )

    # 1. 挂载物理机械手 (在循环外只连接一次，防止单片机反复重启)
    try:
        logger.info("正在接通物理神经链路。com_port=%s", com_port)
        esp32 = serial.Serial(com_port, 115200, timeout=1)  # 外部资源：串口打开
        time.sleep(2)  # 给 ESP32 两秒钟重启和重连蓝牙的时间
        # 同步硬件边界
        init_cmd = f"SET:{get_hid_max_x()},{get_hid_max_y()}\n"
        esp32.write(init_cmd.encode("utf-8"))
        logger.info("已同步硬件边界参数: %s", init_cmd.strip())

        logger.info("机械手已就绪。")
    except _SERIAL_ERRORS as e:
        logger.error("机械手连接失败。com_port=%s error=%s", com_port, e)
        return

    # 2. 初始化眼睛和大脑，并进入无限循环模式。初始化失败时也必须关闭串口。
    try:
        vision = VersaiOSVision(window_title=window_title)
        agent = VersaiOSAgent(
            provider=get_llm_provider(),
            api_key=api_key,
            model_name=get_llm_model(),
            base_url=get_llm_base_url(),
        )

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

            safe_plan, err = validate_plan_dict(plan)
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
                except _SERIAL_ERRORS as e:
                    logger.error("串口写入失败，已跳过本次动作。command=%r error=%s", command, e)
                    continue

                logger.info("动作已执行，等待画面响应。")
                time.sleep(1.5)  # 给手机一点时间响应（比如App打开的动画时间）
            else:
                logger.warning("AI plan 无效（%s），已阻止串口下发。plan=%r", err, plan)

    except KeyboardInterrupt:
        logger.info("被用户强制中断（KeyboardInterrupt）。")
    except Exception:
        logger.exception("VersaiOS 运行失败，正在安全关闭串口。")
    finally:
        # 无论如何，退出前优雅地关闭串口
        logger.info("正在断开机械手。")
        try:
            esp32.close()  # 外部资源：串口关闭
        except _SERIAL_ERRORS as e:
            logger.error("串口关闭失败。error=%s", e)
        logger.info("VersaiOS 已安全关闭。")


if __name__ == "__main__":
    setup_logging()
    main()
