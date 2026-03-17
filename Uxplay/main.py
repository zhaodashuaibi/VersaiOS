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

    # 默认不清理 registry：否则每次启动都会重新扫描并加载所有插件 DLL（启动慢、也不利于做最小化裁剪分析）。
    # 如需强制重建缓存（例如你删除/新增了插件 DLL），设置环境变量 VERSAIOS_UXPLAY_CLEAN_GST_REGISTRY=1
    clean_registry = (os.environ.get("VERSAIOS_UXPLAY_CLEAN_GST_REGISTRY", "").strip() == "1")
    if clean_registry and os.path.exists(env["GST_REGISTRY"]):
        try:
            os.remove(env["GST_REGISTRY"])
            print("已清理旧的解码器缓存。path={}".format(env["GST_REGISTRY"]))
        except Exception:
            print("清理解码器缓存失败。path={}".format(env["GST_REGISTRY"]))

    print("正在挂载独立的 GStreamer 解码矩阵...")

    uxplay_exe = os.path.join(current_dir, "uxplay.exe")

    try:
        process = subprocess.Popen(
            [uxplay_exe, "-p", "-n", "VersaiOS_Screen"],
            env=env
        )
        print("视觉引擎已就绪，请使用 iPhone 发起屏幕镜像。")
        process.wait()
    except FileNotFoundError:
        print("未找到 uxplay.exe，请确认提取步骤。path={}".format(uxplay_exe))
    except KeyboardInterrupt:
        print("收到 KeyboardInterrupt，安全关闭视觉引擎...")
        try:
            process.terminate()
        except Exception:
            print("终止 uxplay 进程失败。")


if __name__ == "__main__":
    start_versaios_receiver()