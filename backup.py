"""每日个人数据备份 — 只读复制，失败只产生 warning，不触碰主数据。

备份对象（PERSONAL_DATA_DIR 下的个人数据）：
- portfolio.json        必须恢复：持仓事实 / 现金 / 操作日志 / 待执行计划
- portfolio_history/    必须恢复：持仓净值历史（不可再生）
- predictions/          必须恢复：历史预测与验证记录（判断依据）
- reviews/              必须恢复：月度复盘报告
- history/              建议恢复：每日板块快照（验证基准；理论可重拉但成本高、会失真）
- position_snapshots/   可再生成：仓位模型快照（缓存类）

备份路径：默认 <PERSONAL_DATA_DIR>_backups/YYYY-MM-DD/；
可用环境变量 PERSONAL_BACKUP_DIR 覆盖备份根目录。
不引入数据库 / 第三方基础设施。
"""

import json
import os
import shutil
from datetime import date, datetime


BACKUP_FILE = "portfolio.json"
BACKUP_DIRS = [
    "portfolio_history",
    "predictions",
    "reviews",
    "history",
    "position_snapshots",
]


def _default_backup_root(data_dir):
    env = os.environ.get("PERSONAL_BACKUP_DIR")
    if env:
        return env
    return data_dir.rstrip("/") + "_backups"


def backup_personal_data(data_dir=None, backup_root=None):
    """执行一次备份。

    Args:
        data_dir: 个人数据目录（默认取 config.DATA_DIR）。
        backup_root: 备份根目录（默认 <data_dir>_backups 或 PERSONAL_BACKUP_DIR）。

    Returns:
        dict：{"status": "ok"|"warning", "target": ..., "copied": n, "error": ...}
        失败时仅返回 warning，绝不影响主数据。
    """
    from config import DATA_DIR

    data_dir = data_dir or DATA_DIR
    if not data_dir or not os.path.isdir(data_dir):
        return {"status": "warning", "error": f"数据目录不存在: {data_dir}"}

    root = backup_root or _default_backup_root(data_dir)
    today = date.today().strftime("%Y-%m-%d")
    target = os.path.join(root, today)

    try:
        os.makedirs(target, exist_ok=True)
        copied = 0

        src_file = os.path.join(data_dir, BACKUP_FILE)
        if os.path.exists(src_file):
            shutil.copy2(src_file, os.path.join(target, BACKUP_FILE))
            copied += 1

        for name in BACKUP_DIRS:
            src_dir = os.path.join(data_dir, name)
            if not os.path.isdir(src_dir):
                continue
            dst_dir = os.path.join(target, name)
            if os.path.exists(dst_dir):
                shutil.rmtree(dst_dir)
            shutil.copytree(
                src_dir,
                dst_dir,
                ignore=shutil.ignore_patterns("*.lock", "*.tmp"),
            )
            copied += 1

        meta = {
            "status": "ok",
            "backed_up_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data_dir": data_dir,
            "target": target,
            "copied": copied,
        }
        meta_path = os.path.join(root, "last_backup.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        return meta
    except Exception as e:
        return {"status": "warning", "error": f"备份失败（主数据未受影响）: {e}"}


def last_backup_info(backup_root=None):
    """读取最近一次备份记录；无记录时返回 None。"""
    from config import DATA_DIR

    root = backup_root or _default_backup_root(DATA_DIR)
    path = os.path.join(root, "last_backup.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


if __name__ == "__main__":
    result = backup_personal_data()
    if result.get("status") == "ok":
        print(f"🗄 备份完成 → {result['target']}（{result['copied']} 项）")
    else:
        print(f"⚠ 备份警告: {result.get('error')}")
