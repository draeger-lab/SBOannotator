# src/sboannotator/test_configuration.py
#!/usr/bin/env python3
"""
Simple unit test for configuration system
简化的配置系统测试
"""

import unittest
from sboannotator.config_manager import get_database_order  # 相对导入 (relative import)


class TestConfiguration(unittest.TestCase):
    """配置系统简化测试"""

    def test_get_database_order(self):
        """测试获取数据库顺序"""
        order = get_database_order()
        self.assertIsInstance(order, list)
        self.assertGreater(len(order), 0)

    def test_valid_database_names(self):
        """测试数据库名称有效"""
        order = get_database_order()
        valid_dbs = ['bigg', 'kegg', 'reactome', 'seed']
        for db in order:
            self.assertIn(db, valid_dbs)


if __name__ == '__main__':  # 仅本文件单独运行时用，pytest(测试框架 pytest) 不需要
    unittest.main()
