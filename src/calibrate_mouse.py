import serial
import time
from config import get_com_port
import logging
from logging_setup import setup_logging


setup_logging()
logger = logging.getLogger(__name__)


def main():
    com_port = get_com_port()
    logger.info("正在连接 ESP32 机械手。com_port=%s", com_port)
    try:
        esp32 = serial.Serial(com_port, 115200, timeout=1)
        time.sleep(2)
    except Exception:
        logger.exception("连接失败。com_port=%s", com_port)
        return

    logger.info("===========================================")
    logger.info("欢迎进入 iOS 鼠标极限步数校准系统")
    logger.info("玩法：发送极限坐标，观察光标是否触边以调整 hid_max_x/hid_max_y。")
    logger.info("测好后请将数值填入 src/config.ini 的 hid_max_x、hid_max_y。")
    logger.info("===========================================")

    while True:
        try:
            # 让你手动输入测试的 X 和 Y 步数
            test_x = int(input("请输入测试 X 轴步数 (猜想值 140): "))
            test_y = int(input("请输入测试 Y 轴步数 (猜想值 310): "))

            command = f"CLICK:{test_x},{test_y}\n"
            try:
                esp32.write(command.encode("utf-8"))
            except Exception:
                logger.exception("串口写入失败，已跳过。command=%r", command)
                continue
            logger.info("已发送指令: 移动到步数 (%s, %s) 并点击。", test_x, test_y)
            time.sleep(1)

            logger.info("请观察手机屏幕光标位置。")

        except ValueError:
            logger.info("退出校准程序。")
            break

    try:
        esp32.close()
    except Exception:
        logger.exception("串口关闭失败。")


if __name__ == "__main__":
    main()