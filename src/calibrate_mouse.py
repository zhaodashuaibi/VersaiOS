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

    logger.info("================================================================")
    logger.info(" 🚀 欢迎进入 VersaiOS 相对鼠标极限界限校准系统")
    logger.info("================================================================")
    logger.info("【校准标准流程】:")
    logger.info("  1. 测 X 轴: 一直向左(a)把光标推死在最左边平直边缘 -> 输入 r 归零 -> ")
    logger.info("              一点点向右(d)直到光标死死贴在最右边 -> 记下此时的 X 累计值。")
    logger.info("  2. 测 Y 轴: 一直向上(w)把光标推死在最上面平直边缘 -> 输入 r 归零 -> ")
    logger.info("              一点点向下(s)直到光标死死贴在最下面 -> 记下此时的 Y 累计值。")
    logger.info("  3. 将这两个最终累计值填入 config.ini 的 hid_max_x 和 hid_max_y。")
    logger.info("================================================================")
    logger.info("【操控指令格式】 (方向 + 空格 + 步数):")
    logger.info("  w 100  : 向上移动 100 步")
    logger.info("  s 100  : 向下移动 100 步")
    logger.info("  a 100  : 向左移动 100 步")
    logger.info("  d 100  : 向右移动 100 步")
    logger.info("  r      : 累加器归零 (起点标记)")
    logger.info("  q      : 退出校准")
    logger.info("================================================================")

    # 累计步数追踪器
    acc_x = 0
    acc_y = 0

    while True:
        # input 本身必须用来接收用户终端输入，其余输出均走 logger
        cmd_input = input(f"\n[当前累计位移 X:{acc_x}, Y:{acc_y}] 请输入指令: ").strip().lower()

        if not cmd_input:
            continue

        if cmd_input in ['q', 'quit', 'exit']:
            logger.info("退出校准程序。")
            break

        # 归零指令
        if cmd_input == 'r':
            acc_x = 0
            acc_y = 0
            logger.info("🔁 累计步数已清零！请开始向反方向移动。")
            continue

        # 解析方向和步数
        parts = cmd_input.split()
        if len(parts) != 2:
            logger.warning("格式错误！请输入类似 'd 100' 的指令。")
            continue

        direction = parts[0]
        try:
            step = int(parts[1])
        except ValueError:
            logger.warning("步数必须是整数！")
            continue

        if step < 0:
            logger.warning("步数请提供正数，方向由 w/a/s/d 决定。")
            continue

        # 将指令映射为相对位移量 dx, dy
        dx, dy = 0, 0
        if direction == 'w':
            dy = -step
        elif direction == 's':
            dy = step
        elif direction == 'a':
            dx = -step
        elif direction == 'd':
            dx = step
        else:
            logger.warning("未知方向！只能使用 w (上), a (左), s (下), d (右)。")
            continue

        # 发送底层执行指令
        command = f"REL:{dx},{dy}\n"
        try:
            esp32.write(command.encode("utf-8"))

            # 只有硬件成功执行，才更新 Python 端的累计值
            acc_x += dx
            acc_y += dy
            logger.info("📡 已发送到底层: %s", command.strip())

        except Exception:
            logger.exception("串口写入失败，已跳过。command=%r", command)
            continue

        time.sleep(0.1)  # 稍微给一点缓冲

    try:
        esp32.close()
    except Exception:
        logger.exception("串口关闭失败。")


if __name__ == "__main__":
    main()