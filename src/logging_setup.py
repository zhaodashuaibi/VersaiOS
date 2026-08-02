import logging
import os

# 每个进程只应初始化一次日志格式；重复调用仅刷新日志级别。
_setup_done = False


def setup_logging(default_level: str = "INFO") -> None:
    """
    标准日志体系：
    - 时间、等级、模块名
    - 通过环境变量 VERSAIOS_LOG_LEVEL 覆盖等级

    注意：这是一个进程级初始化函数。项目入口（src/main_versaios.py、
    src/vision_engine.py 等）在 __main__ 中调用一次即可；作为库被 import
    时不应调用，避免覆盖用户已有的日志 handler 或格式。
    """
    global _setup_done

    level_name = (os.environ.get("VERSAIOS_LOG_LEVEL") or default_level).upper().strip()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    if _setup_done:
        return

    # 如果已有其他 handler（比如被某些库提前写入），先清空以保证格式统一
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

    _setup_done = True
