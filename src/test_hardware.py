import serial
import time
import logging
from logging_setup import setup_logging


setup_logging()
logger = logging.getLogger(__name__)


def fire_click(com_port):
    logger.info("正在接管底层通信总线。com_port=%s", com_port)
    esp32 = None
    try:
        # 建立串口连接，波特率必须和 Arduino 里写的 115200 保持一致
        esp32 = serial.Serial(com_port, 115200, timeout=1)
        # 极其关键：打开串口后，ESP32 会自动重启一次，必须休眠 2 秒等它稳住
        time.sleep(2)
    except serial.SerialException:
        logger.exception("串口连接失败。请确认 com_port=%s 是否正确，且未被占用。", com_port)
        return

    logger.info("神经链路已就绪，发送物理点击指令。")
    try:
        esp32.write("CLICK\n".encode("utf-8"))
    except Exception:
        logger.exception("串口写入失败。")
    finally:
        try:
            esp32.close()
        except Exception:
            logger.exception("串口关闭失败。")

    logger.info("指令流程结束。")


if __name__ == "__main__":
    # ⚠️ 请把这里的 'COM3' 换成你刚才烧录代码时用的真实 COM 口！
    fire_click("COM3")