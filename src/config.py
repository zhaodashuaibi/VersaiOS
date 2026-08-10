"""
VersaiOS 配置：从环境变量或 config.ini 读取，避免将 API Key 等写进代码。
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 环境变量名
ENV_COM_PORT = "VERSAIOS_COM_PORT"
ENV_WINDOW_TITLE = "VERSAIOS_WINDOW_TITLE"
ENV_HID_MAX_X = "VERSAIOS_HID_MAX_X"
ENV_HID_MAX_Y = "VERSAIOS_HID_MAX_Y"

# 新版：通用 LLM 配置（推荐用这些环境变量/ini 字段）
ENV_LLM_PROVIDER = "VERSAIOS_LLM_PROVIDER"
ENV_LLM_API_KEY = "VERSAIOS_LLM_API_KEY"
ENV_LLM_MODEL = "VERSAIOS_LLM_MODEL"
ENV_LLM_BASE_URL = "VERSAIOS_LLM_BASE_URL"

# 与 UxPlay/main.py 的 -n 参数保持一致
DEFAULT_WINDOW_TITLE = "VersaiOS_Screen"
APP_VERSION = "3.1.0"

# 模型接口固定为 OpenAI 兼容接口，不再提供厂商选择。
# 保留 llm_provider 字段仅为兼容旧配置，实际读取时统一按 openai_compatible 处理。
LLM_PROVIDER_OPTIONS = (
    ("openai_compatible", "兼容 OpenAI 接口（OpenAI/DeepSeek/本地模型/中转代理）"),
)
LLM_PROVIDER_LABELS = dict(LLM_PROVIDER_OPTIONS)
LLM_PROVIDER_IDS_BY_LABEL = {label: provider for provider, label in LLM_PROVIDER_OPTIONS}
OPENAI_STYLE_PROVIDERS = frozenset({"openai_compatible"})

# OpenAI 兼容接口不内置默认端点，必须由用户在 GUI/ini 中填写 llm_base_url。
DEFAULT_LLM_BASE_URLS: dict = {}

DEFAULT_LLM_MODELS = {
    "openai_compatible": "gpt-4.1-mini",
}

# HID 默认步数仅用于未校准场景，属于“不安全默认值”。
# 请在 gui_app.py『阶段一：准备』完成校准后填入 config.ini 的 hid_max_x / hid_max_y。
DEFAULT_HID_MAX_X = 140
DEFAULT_HID_MAX_Y = 310


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


def reload_config() -> None:
    """重新读取 config.ini。

    GUI 会在运行期间创建或保存配置文件；不刷新这里的缓存，随后启动
    主控或更新校准提示时仍会使用导入时的旧配置。
    """
    global _ini
    _ini = _load_ini_if_exists()


def get_llm_provider() -> str:
    """LLM 提供方。固定使用 OpenAI 兼容接口，不再支持厂商选择。"""
    return "openai_compatible"


def get_llm_provider_label(provider: Optional[str] = None) -> str:
    """返回 provider ID 对应的 GUI 展示文案。"""
    provider_id = (provider or get_llm_provider()).strip().lower()
    return LLM_PROVIDER_LABELS.get(provider_id, LLM_PROVIDER_LABELS["openai_compatible"])


def get_llm_provider_id(value: str) -> str:
    """兼容旧配置与展示文案，统一返回固定的 openai_compatible。"""
    return "openai_compatible"


def get_default_llm_model(provider: Optional[str] = None) -> str:
    """返回默认视觉模型名称（OpenAI 兼容接口）。"""
    return DEFAULT_LLM_MODELS["openai_compatible"]


def get_default_llm_base_url(provider: Optional[str] = None) -> Optional[str]:
    """OpenAI 兼容接口不设默认端点，必须由用户填写。"""
    return None


def get_llm_api_key():
    """
    LLM API Key：优先 VERSAIOS_LLM_API_KEY，其次 config.ini 的 llm_api_key。
    """
    key = os.environ.get(ENV_LLM_API_KEY) or _ini.get("llm_api_key", "").strip()
    return key if key else None


def _is_placeholder_llm_api_key(key: str) -> bool:
    """Detect values copied from config.example.ini rather than a real secret."""
    normalized = key.strip().lower()
    placeholder_tokens = (
        "api_key",
        "your_key",
        "your-api-key",
        "your api key",
        "replace_me",
        "changeme",
    )
    return any(token in normalized for token in placeholder_tokens)


def get_llm_model() -> str:
    """LLM 模型名：可在环境变量/ini 中覆盖，否则按 provider 给默认值。"""
    raw = (os.environ.get(ENV_LLM_MODEL) or _ini.get("llm_model", "")).strip()
    if raw:
        return raw
    return get_default_llm_model()


def get_llm_base_url():
    """返回用户配置的 base_url；OpenAI 兼容接口没有内置默认端点，必须填写。"""
    raw = (os.environ.get(ENV_LLM_BASE_URL) or _ini.get("llm_base_url", "")).strip()
    return raw or None


def get_com_port():
    """ESP32 串口：环境变量 VERSAIOS_COM_PORT 或 config.ini，默认 COM3。"""
    return (
        os.environ.get(ENV_COM_PORT)
        or _ini.get("com_port", "").strip()
        or "COM3"
    )


def get_window_title():
    """投屏窗口标题：环境变量或 config.ini，默认 VersaiOS_Screen。"""
    return (
        os.environ.get(ENV_WINDOW_TITLE)
        or _ini.get("window_title", "").strip()
        or DEFAULT_WINDOW_TITLE
    )


def _int_or(s, default):
    try:
        return int(s)
    except (TypeError, ValueError):
        return default


def get_hid_max_x():
    """HID X 轴极限步数（校准后填入 config.ini）。"""
    raw = os.environ.get(ENV_HID_MAX_X) or _ini.get("hid_max_x", "").strip()
    return _int_or(raw, DEFAULT_HID_MAX_X)


def get_hid_max_y():
    """HID Y 轴极限步数（校准后填入 config.ini）。"""
    raw = os.environ.get(ENV_HID_MAX_Y) or _ini.get("hid_max_y", "").strip()
    return _int_or(raw, DEFAULT_HID_MAX_Y)


def is_hid_calibrated() -> bool:
    """
    判断 HID 步数是否已显式配置（环境变量或 config.ini）。
    仅使用默认值视为未校准，GUI/CLI 应给出醒目提示。
    """
    x_raw = os.environ.get(ENV_HID_MAX_X) or _ini.get("hid_max_x", "").strip()
    y_raw = os.environ.get(ENV_HID_MAX_Y) or _ini.get("hid_max_y", "").strip()
    if not x_raw or not y_raw:
        return False
    try:
        x_value = int(x_raw)
        y_value = int(y_raw)
    except (TypeError, ValueError):
        return False
    if x_value <= 0 or y_value <= 0:
        return False

    # config.example.ini 会写入占位默认值，因此“文件中存在该字段”不足以
    # 说明用户已经完成校准。两个值都仍为默认值时保持警告。
    return (x_value, y_value) != (DEFAULT_HID_MAX_X, DEFAULT_HID_MAX_Y)


def validate_llm_config() -> Optional[str]:
    """启动前校验 LLM 配置，返回错误信息或 None。"""
    api_key = get_llm_api_key()
    if not api_key:
        return "未配置 llm_api_key / VERSAIOS_LLM_API_KEY"
    if _is_placeholder_llm_api_key(api_key):
        return "llm_api_key 仍是模板占位值，请填写真实 API Key"
    if not get_llm_base_url():
        return "OpenAI 兼容接口需要配置 llm_base_url / VERSAIOS_LLM_BASE_URL"
    return None


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
          
        - 指令：“返回”
          - 正确坐标：一般在屏幕左上角两个斜杠组成的图形中心。

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
