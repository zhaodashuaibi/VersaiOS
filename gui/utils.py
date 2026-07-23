# gui/utils.py
"""VersaiOS GUI 模块共享工具：路径、配置读写、src 导入路径。"""
import os
import shutil
import sys
import configparser
from typing import Dict, Any


def get_project_root() -> str:
    """返回项目根目录。兼容 PyInstaller 打包后的 exe 场景。"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # 本文件位于 gui/utils.py，项目根目录是再上一级
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


PROJECT_ROOT = get_project_root()
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
UXPLAY_PATH = os.path.join(PROJECT_ROOT, "UxPlay")

CONFIG_INI_PATH = os.path.join(SRC_PATH, "config.ini")
CONFIG_EXAMPLE_PATH = os.path.join(SRC_PATH, "config.example.ini")
MAIN_VERSAIOS_PATH = os.path.join(SRC_PATH, "main_versaios.py")
UXPLAY_MAIN_PATH = os.path.join(UXPLAY_PATH, "main.py")

# 让 gui 模块能够导入 src 目录下的 config / ai_brain / vision_engine 等
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# 默认配置项，与 src/config.example.ini 保持一致
DEFAULT_CONFIG: Dict[str, str] = {
    "llm_provider": "gemini",
    "llm_api_key": "",
    "llm_base_url": "",
    "llm_model": "gemini-3-flash-preview",
    "com_port": "COM3",
    "window_title": "VersaiOS_Screen",
    "hid_max_x": "140",
    "hid_max_y": "310",
}


def create_default_config() -> None:
    """若 config.ini 不存在，从 config.example.ini 复制生成。"""
    if not os.path.exists(CONFIG_EXAMPLE_PATH):
        raise FileNotFoundError(f"未找到配置模板: {CONFIG_EXAMPLE_PATH}")
    os.makedirs(SRC_PATH, exist_ok=True)
    shutil.copy2(CONFIG_EXAMPLE_PATH, CONFIG_INI_PATH)


def load_existing_config() -> Dict[str, str]:
    """读取 config.ini，返回字典。若不存在则自动创建。"""
    if not os.path.exists(CONFIG_INI_PATH):
        create_default_config()

    parser = configparser.ConfigParser()
    parser.read(CONFIG_INI_PATH, encoding="utf-8")
    section = dict(parser["versaios"]) if parser.has_section("versaios") else {}

    return {key: section.get(key, default) for key, default in DEFAULT_CONFIG.items()}


def save_config_values(updates: Dict[str, Any]) -> None:
    """增量更新 config.ini 的 [versaios] 节。"""
    parser = configparser.ConfigParser()
    if os.path.exists(CONFIG_INI_PATH):
        parser.read(CONFIG_INI_PATH, encoding="utf-8")
    if not parser.has_section("versaios"):
        parser.add_section("versaios")

    for key, value in updates.items():
        parser.set("versaios", key, str(value))

    os.makedirs(SRC_PATH, exist_ok=True)
    with open(CONFIG_INI_PATH, "w", encoding="utf-8") as f:
        parser.write(f)
