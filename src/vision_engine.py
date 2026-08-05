import time
import cv2
import numpy as np
from typing import Any
from mss.exception import ScreenShotError
import mss
import pygetwindow as gw
from PIL import Image
import logging
from config import DEFAULT_WINDOW_TITLE, get_window_title


logger = logging.getLogger(__name__)
# 视觉捕获相关的具体异常类型，避免 bare except 吞掉无关错误
_MSS_ERRORS: tuple[Any,...] = (ScreenShotError,)
_WINDOW_ERRORS = (AttributeError, OSError, ValueError)


class VersaiOSVision:
    def __init__(self, window_title=None):
        """
        初始化视觉捕获引擎
        注意：投屏窗口名请在这里修改。
        """
        self.window_title = window_title or DEFAULT_WINDOW_TITLE
        self.sct = mss.MSS()  # 初始化极速截图器

    def _get_window_rect(self):
        """内部方法：获取目标窗口的实时坐标和尺寸"""
        try:
            # 模糊匹配窗口标题
            windows = gw.getWindowsWithTitle(self.window_title)
            if not windows:
                return None

            win = windows[0]
            # 如果窗口被最小化了，无法截图
            if win.isMinimized:
                return None

            # 返回 mss 库需要的字典格式
            # 注意：Windows 窗口有不可见的系统边框阴影，这里可能需要微调
            return {
                "top": win.top,
                "left": win.left,
                "width": win.width,
                "height": win.height
            }
        except _WINDOW_ERRORS as e:
            logger.warning("获取窗口坐标失败。window_title=%r error=%s", self.window_title, e)
            return None
        except Exception as e:
            # pygetwindow 在部分平台/窗口状态下可能抛出未归类的异常，
            # 这里兜底记录并返回 None，避免主控端因窗口枚举偶发错误而崩溃。
            logger.warning("获取窗口坐标遇到未预期异常。window_title=%r error=%s", self.window_title, e)
            return None

    def grab_frame_for_ai(self):
        """
        获取一帧画面，转换为适合发送给大模型的 PIL Image 格式 (RGB)
        """
        rect = self._get_window_rect()
        if not rect:
            return None

        try:
            # 从显存/内存中极速抓取像素
            sct_img = self.sct.grab(rect)
        except _MSS_ERRORS as e:
            logger.warning("mss 截图失败：%s", e)
            return None

        # mss 抓取的是 BGRA 格式，我们需要转为标准的 RGB 供大模型使用
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img

    def grab_frame_for_cv(self):
        """
        获取一帧画面，转换为适合 OpenCV 处理的 Numpy 矩阵 (BGR)
        （用于我们接下来的本地实时预览测试）
        """
        rect = self._get_window_rect()
        if not rect:
            return None

        try:
            sct_img = self.sct.grab(rect)
        except _MSS_ERRORS as e:
            logger.warning("mss 截图失败：%s", e)
            return None

        # 转为 numpy 数组
        img_np = np.array(sct_img)
        # 丢弃 Alpha 通道 (透明度)，保留 BGR
        return img_np[:, :, :3]


# ==========================================
# 单元测试：实时视觉预览流
# ==========================================
if __name__ == "__main__":
    from logging_setup import setup_logging

    setup_logging()
    logger.info("正在启动视觉捕获测试。")

    # 实例化我们的“眼睛”
    vision = VersaiOSVision(window_title=get_window_title())

    # 用于计算 FPS 的变量
    fps_start_time = time.time()
    fps_frame_count = 0

    while True:
        # 获取矩阵格式的画面用于本地显示
        frame = vision.grab_frame_for_cv()

        if frame is not None:
            # 计算帧率 (FPS)
            fps_frame_count += 1
            if time.time() - fps_start_time >= 1.0:
                logger.info("视觉采样率: %s FPS", fps_frame_count)
                fps_frame_count = 0
                fps_start_time = time.time()

            # 使用 OpenCV 实时弹出一个小窗口来监视我们抓取到的画面
            # 对画面进行等比例缩放，防止原图太大占满屏幕
            height, width = frame.shape[:2]
            display_frame = cv2.resize(frame, (int(width * 0.5), int(height * 0.5)))

            cv2.imshow("VersaiOS AI Eye - Live Feed", display_frame)

        # 敲击键盘上的 'q' 键退出测试
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # 稍微休眠，避免榨干 CPU (在实际发给 AI 时，大概 1 秒截 1 帧就够了)
        time.sleep(0.01)

    cv2.destroyAllWindows()
    logger.info("视觉流已关闭。")