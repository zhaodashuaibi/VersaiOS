import os
import subprocess


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
        os.remove(env["GST_REGISTRY"])
        print(">>> [VersaiOS] 已清理旧的解码器缓存。")

    print(">>> [VersaiOS] 正在挂载独立的 GStreamer 解码矩阵...")

    uxplay_exe = os.path.join(current_dir, "uxplay.exe")

    try:
        process = subprocess.Popen(
            [uxplay_exe, "-p","-n", "VersaiOS_Screen"],
            env=env
        )
        print(">>> [VersaiOS] 视觉引擎已就绪，请使用 iPhone 发起屏幕镜像。")
        process.wait()
    except FileNotFoundError:
        print("错误：未找到 uxplay.exe，请确认提取步骤。")
    except KeyboardInterrupt:
        print("\n>>> [VersaiOS] 安全关闭视觉引擎...")
        process.terminate()


if __name__ == "__main__":
    start_versaios_receiver()