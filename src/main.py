import os
import subprocess
import logging
from logging_setup import setup_logging


setup_logging()
logger = logging.getLogger(__name__)


def start_versaios_receiver():
    # 1. 获取当前绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    gst_plugin_path = os.path.join(current_dir, "gst_plugins")

    # 2. 配置纯净的沙盒环境变量
    env = os.environ.copy()

    # 强制 GStreamer 只从我们的文件夹加载插件
    env["GST_PLUGIN_SYSTEM_PATH"] = gst_plugin_path
    env["GST_PLUGIN_PATH"] = gst_plugin_path

    # 强制将 GStreamer 的注册表缓存文件写在当前目录，彻底隔离系统环境！
    env["GST_REGISTRY"] = os.path.join(current_dir, "gst_registry.bin")

    # 强制清理旧的、可能损坏的缓存（如果有）
    if os.path.exists(env["GST_REGISTRY"]):
        try:
            os.remove(env["GST_REGISTRY"])  # 外部资源：文件删除
            logger.info("已清理旧的解码器缓存。path=%s", env["GST_REGISTRY"])
        except Exception:
            logger.exception("清理解码器缓存失败。path=%s", env["GST_REGISTRY"])

    logger.info("正在挂载独立的 GStreamer 解码矩阵...")

    uxplay_exe = os.path.join(current_dir, "uxplay.exe")

    try:
        process = subprocess.Popen(
            [uxplay_exe, "-p","-n", "VersaiOS_Screen"],
            env=env
        )
        logger.info("视觉引擎已就绪，请使用 iPhone 发起屏幕镜像。")
        process.wait()
    except FileNotFoundError:
        logger.error("未找到 uxplay.exe，请确认提取步骤。path=%s", uxplay_exe)
    except KeyboardInterrupt:
        logger.info("收到 KeyboardInterrupt，安全关闭视觉引擎...")
        try:
            process.terminate()
        except Exception:
            logger.exception("终止 uxplay 进程失败。")


if __name__ == "__main__":
    start_versaios_receiver()