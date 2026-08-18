"""统一日志系统：控制台 + 文件（个人数据目录）+ 错误计数。

- 文件日志写入 <PERSONAL_DATA_DIR>/logs/app.log，滚动 1MB × 5，不入 Git；
- CountingHandler 按天统计 ERROR / WARNING 次数，供 /api/health 展示；
- setup_logging() 幂等，只在运行入口调用；其余模块仅 import get_logger。
"""

import logging
import logging.handlers
import os
from datetime import date


_counters = {}  # {"2026-08-18": {"error": n, "warning": n}}
_setup_done = False


class _CountingHandler(logging.Handler):
    def emit(self, record):
        day = date.today().isoformat()
        bucket = _counters.setdefault(day, {"error": 0, "warning": 0})
        if record.levelno >= logging.ERROR:
            bucket["error"] += 1
        elif record.levelno >= logging.WARNING:
            bucket["warning"] += 1


# 计数始终可用（不依赖 setup_logging 被调用）
logging.getLogger().addHandler(_CountingHandler())


def setup_logging(log_dir=None):
    """配置 root logger（控制台 + 滚动文件 + 计数）。幂等。"""
    global _setup_done
    if _setup_done:
        return

    if log_dir is None:
        try:
            from config import DATA_DIR

            log_dir = os.path.join(DATA_DIR, "logs")
        except Exception:
            log_dir = os.path.join(os.getcwd(), "logs")

    try:
        os.makedirs(log_dir, exist_ok=True)
    except OSError:
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    root.addHandler(stream_handler)
    _setup_done = True


def get_logger(name):
    return logging.getLogger(name)


def error_counts():
    """按天返回 ERROR / WARNING 计数（供健康检查展示）。"""
    return {k: dict(v) for k, v in sorted(_counters.items())}
