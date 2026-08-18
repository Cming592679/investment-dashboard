"""Investment Dashboard 单元测试（unittest，零第三方依赖）。

为避免测试依赖个人数据目录，统一在导入项目模块前设置一个临时目录。
（绝不读取/写入真实 PERSONAL_DATA_DIR。）
"""

import os
import tempfile

os.environ.setdefault(
    "PERSONAL_DATA_DIR",
    tempfile.mkdtemp(prefix="investment-dashboard-tests-"),
)
