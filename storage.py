"""JSON storage 可靠性层：单写者（文件锁）+ 原子写入。

所有个人数据 / 配置 JSON 的写入统一走 write_json()：
- 原子写入：先写同目录临时文件，再 os.replace()，写失败不会破坏原文件；
- 进程/线程间互斥：fcntl.flock 锁 <path>.lock，保证单写者；
- 保持现有 JSON 语义：encoding=utf-8, ensure_ascii=False, indent=2。

读取接口不做改动，保持各模块现有读取方式。
"""

import fcntl
import json
import os
import tempfile


def write_json(path, data):
    """原子写入 JSON 数据。写失败时原文件保持不变。

    Args:
        path: 目标文件路径（父目录不存在时会自动创建）。
        data: 可 JSON 序列化的对象。
    """
    directory = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(directory, exist_ok=True)

    lock_path = path + ".lock"
    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        fd, tmp_path = tempfile.mkstemp(
            dir=directory,
            prefix=os.path.basename(path) + ".",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.chmod(tmp_path, 0o644)
            os.replace(tmp_path, path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)
