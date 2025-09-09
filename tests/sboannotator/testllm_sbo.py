import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/'))
from sboannotator.llm_sbo  import *

import unittest
import json
import tempfile
import os
from unittest.mock import patch, mock_open


# Import your functions here
# from llm_sbo import askuseLLMornot, readdocument




class TestLLMSBO(unittest.TestCase):

    def setUp(self):
        """创建测试用的JSON数据"""
        self.test_json_data = {
            "model_file": "test_model.xml",
            "target_sbo_terms": ["SBO:0000178", "SBO:0000200"],
            "total_target_reactions": 3,
            "reactions": {
                "R_ACALD": {
                    "sbo": "SBO:0000200",
                    "ec_numbers": [],
                    "annotation_source": "reaction_type_checks"
                },
                "R_ACONTa": {
                    "sbo": "SBO:0000178",
                    "ec_numbers": ["4.2.1.3"],
                    "annotation_source": "callForECAnnotRxnUnified"
                },
                "R_CS": {
                    "sbo": "SBO:0000402",
                    "ec_numbers": ["2.3.3.1", "2.3.3.3", "2.3.3.16"],
                    "annotation_source": "callForECAnnotRxnUnified"
                }
            }
        }

        # 创建临时文件
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump(self.test_json_data, self.temp_file, indent=2)
        self.temp_file.close()

    def tearDown(self):
        """清理临时文件"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_readdocument_basic_functionality(self):
        """测试基本的文件读取功能"""
        result = read_document(self.temp_file.name)

        # 检查返回的字典长度
        self.assertEqual(len(result), 3)

        # 检查特定反应的数据结构
        self.assertIn('R_ACALD', result)
        self.assertEqual(result['R_ACALD']['reaction_id'], 'R_ACALD')
        self.assertEqual(result['R_ACALD']['original_sbo'], 'SBO:0000200')
        self.assertEqual(result['R_ACALD']['ec_numbers'], [])

        # 检查有多个EC号的反应
        self.assertIn('R_CS', result)
        self.assertEqual(result['R_CS']['ec_numbers'], ["2.3.3.1", "2.3.3.3", "2.3.3.16"])

        # 检查有单个EC号的反应
        self.assertIn('R_ACONTa', result)
        self.assertEqual(result['R_ACONTa']['ec_numbers'], ["4.2.1.3"])

    def test_readdocument_empty_reactions(self):
        """测试空反应列表的情况"""
        empty_data = {
            "model_file": "test_model.xml",
            "total_target_reactions": 0,
            "reactions": {}
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp:
            json.dump(empty_data, temp, indent=2)
            temp_path = temp.name

        try:
            result = read_document(temp_path)
            self.assertEqual(len(result), 0)
        finally:
            os.unlink(temp_path)

    def test_readdocument_missing_fields(self):
        """测试缺少字段的情况"""
        incomplete_data = {
            "reactions": {
                "R_TEST": {
                    "sbo": "SBO:0000200"
                    # 缺少ec_numbers字段
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp:
            json.dump(incomplete_data, temp, indent=2)
            temp_path = temp.name

        try:
            result = read_document(temp_path)
            self.assertEqual(len(result), 1)
            self.assertEqual(result['R_TEST']['ec_numbers'], [])  # 应该默认为空列表
        finally:
            os.unlink(temp_path)

    def test_readdocument_file_not_found(self):
        """测试文件不存在的情况"""
        with self.assertRaises(FileNotFoundError):
            read_document("nonexistent_file.json")

    def test_readdocument_invalid_json(self):
        """测试无效JSON的情况"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp:
            temp.write("invalid json content {")
            temp_path = temp.name

        try:
            with self.assertRaises(json.JSONDecodeError):
                read_document(temp_path)
        finally:
            os.unlink(temp_path)


    @patch('builtins.input')
    def test_askuseLLMornot_no_responses(self, mock_input):
        """测试否定回答"""
        # 测试各种否定回答
        negative_responses = ['n', 'N', 'no', 'NO', 'nope', '否', ' n ', 'random']

        for response in negative_responses:
            with self.subTest(response=response):
                mock_input.return_value = response
                self.assertFalse(askuseLLMornot())

    @patch('builtins.input')
    def test_askuseLLMornot_empty_input(self, mock_input):
        """测试空输入"""
        mock_input.return_value = ""
        self.assertFalse(askuseLLMornot())


class TestPrefixOfECNumbers(unittest.TestCase):

    def test_four_digit_prefix(self):
        """Test 4-digit common prefix"""
        ec_list = ['2.3.3.1', '2.3.3.3', '2.3.3.16']
        result = prefix_of_ec_numbers(ec_list)
        self.assertEqual(result, '2.3.3')

    def test_three_digit_prefix(self):
        """Test 3-digit common prefix"""
        ec_list = ['1.3.99.1', '1.3.5.1']
        result = prefix_of_ec_numbers(ec_list)
        self.assertEqual(result, '1.3')

    def test_two_digit_prefix(self):
        """Test 2-digit common prefix"""
        ec_list = ['4.2.1.11', '4.2.9.3']
        result = prefix_of_ec_numbers(ec_list)
        self.assertEqual(result, '4.2')

    def test_one_digit_prefix(self):
        """Test 1-digit common prefix"""
        ec_list = ['1.1.1.1', '1.9.9.9']
        result = prefix_of_ec_numbers(ec_list)
        self.assertEqual(result, '1')

    def test_single_ec_number(self):
        """Test single EC number"""
        ec_list = ['4.2.1.3']
        result = prefix_of_ec_numbers(ec_list)
        self.assertEqual(result, '4.2.1.3')

    def test_no_common_prefix(self):
        """Test EC numbers with no common prefix"""
        ec_list = ['1.1.1.1', '2.2.2.2']
        result = prefix_of_ec_numbers(ec_list)
        self.assertIsNone(result)

    def test_empty_list(self):
        """Test empty EC number list"""
        ec_list = []
        result = prefix_of_ec_numbers(ec_list)
        self.assertIsNone(result)

    def test_invalid_format(self):
        """Test invalid EC number format"""
        ec_list = ['invalid_ec', '2.3.3.1']
        result = prefix_of_ec_numbers(ec_list)
        self.assertIsNone(result)

    def test_different_lengths(self):
        """Test EC numbers with different lengths"""
        ec_list = ['1.2.3.4', '1.2.3', '1.2']
        result = prefix_of_ec_numbers(ec_list)
        self.assertEqual(result, '1.2')


class TestAnalyzeReactionsForLLM(unittest.TestCase):

    def setUp(self):
        """Setup test data"""
        self.test_data = {
            'R_NO_EC': {
                'reaction_id': 'R_NO_EC',
                'original_sbo': 'SBO:0000200',
                'ec_numbers': []
            },
            'R_SINGLE_EC': {
                'reaction_id': 'R_SINGLE_EC',
                'original_sbo': 'SBO:0000178',
                'ec_numbers': ['4.2.1.3']
            },
            'R_MULTI_EC_SAME_PREFIX': {
                'reaction_id': 'R_MULTI_EC_SAME_PREFIX',
                'original_sbo': 'SBO:0000402',
                'ec_numbers': ['2.3.3.1', '2.3.3.3', '2.3.3.16']
            },
            'R_MULTI_EC_DIFFERENT_FIRST': {
                'reaction_id': 'R_MULTI_EC_DIFFERENT_FIRST',
                'original_sbo': 'SBO:0000176',
                'ec_numbers': ['1.1.1.1', '2.3.3.1']
            },
            'R_MULTI_EC_PARTIAL_PREFIX': {
                'reaction_id': 'R_MULTI_EC_PARTIAL_PREFIX',
                'original_sbo': 'SBO:0000211',
                'ec_numbers': ['1.3.99.1', '1.3.5.1']
            },
            'R_MULTI_EC_ONE_DIGIT_PREFIX': {
                'reaction_id': 'R_MULTI_EC_ONE_DIGIT_PREFIX',
                'original_sbo': 'SBO:0000208',
                'ec_numbers': ['4.1.2.13', '4.9.8.7']
            }
        }

    def test_filter_no_ec_reactions(self):
        """Test filtering reactions without EC numbers"""
        result = analyze_reactions_for_llm(self.test_data)
        print(result)

    def test_filter_no_ec_reactions(self):
        """Test filtering reactions without EC numbers"""
        result = analyze_reactions_for_llm(self.test_data)
        self.assertNotIn('R_NO_EC', result)

    def test_single_ec_reaction(self):
        """Test single EC number reaction"""
        result = analyze_reactions_for_llm(self.test_data)

        self.assertIn('R_SINGLE_EC', result)
        self.assertEqual(result['R_SINGLE_EC']['ec_to_llm'], '4.2.1.3')
        self.assertEqual(result['R_SINGLE_EC']['original_sbo'], 'SBO:0000178')

    def test_multiple_ec_same_first_digit_with_prefix(self):
        """Test multiple EC numbers with same first digit using prefix"""
        result = analyze_reactions_for_llm(self.test_data)

        # Should be included with common prefix
        self.assertIn('R_MULTI_EC_SAME_PREFIX', result)
        self.assertEqual(result['R_MULTI_EC_SAME_PREFIX']['ec_to_llm'], '2.3.3')

        self.assertIn('R_MULTI_EC_PARTIAL_PREFIX', result)
        self.assertEqual(result['R_MULTI_EC_PARTIAL_PREFIX']['ec_to_llm'], '1.3')

        self.assertIn('R_MULTI_EC_ONE_DIGIT_PREFIX', result)
        self.assertEqual(result['R_MULTI_EC_ONE_DIGIT_PREFIX']['ec_to_llm'], '4')

    def test_multiple_ec_different_first_digit(self):
        """Test multiple EC numbers with different first digits"""
        result = analyze_reactions_for_llm(self.test_data)

        # Should be filtered out
        self.assertNotIn('R_MULTI_EC_DIFFERENT_FIRST', result)

    def test_original_data_unchanged(self):
        """Test that original data is not modified"""
        original_data = {k: v.copy() for k, v in self.test_data.items()}
        result = analyze_reactions_for_llm(self.test_data)

        # Original data should remain unchanged
        self.assertEqual(self.test_data, original_data)

        # Original data should not have ec_to_llm field
        for reaction_data in self.test_data.values():
            self.assertNotIn('ec_to_llm', reaction_data)

    def test_return_count(self):
        """Test correct number of filtered reactions"""
        result = analyze_reactions_for_llm(self.test_data)

        # Should return 4 reactions (1 single + 3 multi with same first digit)
        self.assertEqual(len(result), 4)

    def test_ec_to_llm_field_added(self):
        """Test that ec_to_llm field is properly added"""
        result = analyze_reactions_for_llm(self.test_data)

        for reaction_id, reaction_data in result.items():
            self.assertIn('ec_to_llm', reaction_data)
            self.assertIsNotNone(reaction_data['ec_to_llm'])


import unittest
import tempfile
import os


class TestConcatenateECText(unittest.TestCase):

    def test_basic_functionality(self):
        """Test basic EC text lookup"""

        # Test data
        data_dict = {
            'R_TEST': {
                'reaction_id': 'R_TEST',
                'original_sbo': 'SBO:0000176',
                'ec_numbers': ['2.3.3.4', '2.3.3.1'],
                'ec_to_llm': '2.3.3'
            }
        }

        # EC file data
        ec_data = [
            {"ec_number": "2.3.3", "ec_text": "Acyl-CoA transferases"}
        ]

        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(ec_data, f)
            temp_path = f.name

        try:
            result = concatenate_ec_text(data_dict, temp_path)
            self.assertEqual(result['R_TEST']['ec_text_to_llm'], 'Acyl-CoA transferases')
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)