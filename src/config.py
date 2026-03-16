"""
VersaiOS 配置：从环境变量或 config.ini 读取，避免将 API Key 等写进代码。
"""
import os
import logging

logger = logging.getLogger(__name__)

# 环境变量名
ENV_API_KEY = "VERSAIOS_API_KEY"
ENV_COM_PORT = "VERSAIOS_COM_PORT"
ENV_WINDOW_TITLE = "VERSAIOS_WINDOW_TITLE"
ENV_HID_MAX_X = "VERSAIOS_HID_MAX_X"
ENV_HID_MAX_Y = "VERSAIOS_HID_MAX_Y"


def _load_ini_if_exists():
    """若存在 config.ini 则解析为字典，否则返回空字典。"""
    config = {}
    try:
        import configparser
        path = os.path.join(os.path.dirname(__file__), "config.ini")
        if os.path.isfile(path):
            parser = configparser.ConfigParser()
            parser.read(path, encoding="utf-8")
            if parser.has_section("versaios"):
                config = dict(parser["versaios"])
    except Exception:
        # 配置读取属于外部资源操作：必须记录详细错误但不中断启动
        logger.exception("读取 config.ini 失败，将回退到环境变量/默认值。")
    return config


_ini = _load_ini_if_exists()


def get_api_key():
    """Gemini API Key：优先环境变量 VERSAIOS_API_KEY，其次 config.ini 中的 api_key。"""
    key = os.environ.get(ENV_API_KEY) or _ini.get("api_key", "").strip()
    return key if key else None


def get_com_port():
    """ESP32 串口：环境变量 VERSAIOS_COM_PORT 或 config.ini，默认 COM3。"""
    return (
        os.environ.get(ENV_COM_PORT)
        or _ini.get("com_port", "").strip()
        or "COM3"
    )


def get_window_title():
    """投屏窗口标题：环境变量或 config.ini，默认 Direct3D12 Renderer。"""
    return (
        os.environ.get(ENV_WINDOW_TITLE)
        or _ini.get("window_title", "").strip()
        or "Direct3D12 Renderer"
    )


def _int_or(s, default):
    try:
        return int(s)
    except (TypeError, ValueError):
        return default


def get_hid_max_x():
    """HID X 轴极限步数（校准后填入 config.ini）。默认 140（参考 iPhone 16）。"""
    raw = os.environ.get(ENV_HID_MAX_X) or _ini.get("hid_max_x", "").strip()
    return _int_or(raw, 140)


def get_hid_max_y():
    """HID Y 轴极限步数（校准后填入 config.ini）。默认 310（参考 iPhone 16）。"""
    raw = os.environ.get(ENV_HID_MAX_Y) or _ini.get("hid_max_y", "").strip()
    return _int_or(raw, 310)


def get_system_prompt():
    """
    返回用于 UI 点击定位的系统 Prompt。
    如需自定义，可在 config.ini 中增加更高级的配置机制（例如指向外部 prompt 文件），
    或直接修改此函数返回内容。
    """
    return """
        # 角色
        你是一个具备像素级高精度视觉推理能力的 iOS UI 自动化点击专家。

        # 任务
        根据用户提供的 iPhone 投屏截图和人类的自然语言指令，找到目标的【绝对精准】的物理点击坐标（x, y 比例）。

        # 核心高精度指令（极其重要，必须严格执行）：

        ## 1. 定义“目标区域”
        一个目标的触摸区域往往比它显示的文字或图标要大。你需要找到整个【可触摸视觉背景】。

        ## 2. 避免“文本基线偏移”误差（核心修复点！）
        AI 常常会输出文字本身的中心坐标，这会导致点击位置偏下。你必须强行向下修正这个习惯：
        - **如果是文字按钮：** 不要点击文字本身的几何中心，也不要点击文字所在的基线。你必须找到包裹这串文字的视觉背景框（通常是一个隐形的矩形触摸块），然后输出这个【背景框】的几何中心。
        - **如果是图标按钮（如返回、设置图标）：** 找到整个图标图案的视觉边界，输出图标本身的几何中心。

        ## 3. 示例校准
        - 指令：“点击 设置”
          - 错误坐标 (AI 常见错误)：在“设置”文字的正中心，或者文字偏下方。
          - 正确坐标 (你需要输出)：在文字周围灰色条状区域的正中心（通常比文字中心偏高一点，使其落在触摸块正中心）。

        - 指令：“点击 微信”图标
          - 错误坐标：在“微信”两个字上。
          - 正确坐标：在那个绿色的、圆角的图标图案正中心。

        # 输出格式
        必须严格输出以下 JSON 格式，不要包含任何多余文字：
        ```json
        {
          "reason": "简述你锁定该目标的几何视觉理由，以及你是如何修正偏差的",
          "x_ratio": 目标背景中心在横轴的 0.00-1.00 比例,
          "y_ratio": 目标背景中心在纵轴的 0.00-1.00 比例
        }
        ```
        """
