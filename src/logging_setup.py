import logging
import os


def setup_logging(default_level: str = "INFO") -> None:
    """
    标准日志体系：
    - 时间、等级、模块名
    - 通过环境变量 VERSAIOS_LOG_LEVEL 覆盖等级
    """
    level_name = (os.environ.get("VERSAIOS_LOG_LEVEL") or default_level).upper().strip()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    if root.handlers:
        # 避免重复配置（例如被多次 import）
        root.setLevel(level)
        return

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

