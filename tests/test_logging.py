"""logging_utils 测试：错误计数 + 文件日志 + setup 幂等。"""

import logging
import os
import tempfile
import unittest
from datetime import date

import logging_utils


class TestLoggingUtils(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="logging_utils_test_")
        self.logger = logging_utils.get_logger("test.logging")

    def test_error_counts_increment(self):
        today = date.today().isoformat()
        before = logging_utils.error_counts().get(today, {}).get("error", 0)
        self.logger.error("boom")
        after = logging_utils.error_counts().get(today, {}).get("error", 0)
        self.assertEqual(after, before + 1)

    def test_warning_counts_separate(self):
        today = date.today().isoformat()
        before = logging_utils.error_counts().get(today, {}).get("warning", 0)
        self.logger.warning("careful")
        after = logging_utils.error_counts().get(today, {}).get("warning", 0)
        self.assertEqual(after, before + 1)

    def test_log_file_written(self):
        logging_utils.setup_logging(log_dir=self.tmp_dir)
        self.logger.warning("hello file")
        log_path = os.path.join(self.tmp_dir, "app.log")
        self.assertTrue(os.path.exists(log_path))
        with open(log_path, encoding="utf-8") as f:
            self.assertIn("hello file", f.read())

    def test_setup_idempotent(self):
        logging_utils.setup_logging(log_dir=self.tmp_dir)
        handler_count = len(logging.getLogger().handlers)
        logging_utils.setup_logging(log_dir=self.tmp_dir)
        self.assertEqual(len(logging.getLogger().handlers), handler_count)


if __name__ == "__main__":
    unittest.main()
