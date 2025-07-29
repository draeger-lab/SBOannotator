import unittest
import json
import tempfile
import os
from unittest.mock import patch, mock_open
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ols_fetch_from_github.config import Config, ConfigurationError


class TestConfig(unittest.TestCase):
    """Test cases for Config class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_config_data = {
            "github": {
                "url": "https://raw.githubusercontent.com/test/repo/master/file.obo",
                "repo_owner": "test_owner",
                "repo_name": "test_repo",
                "file_path": "test.obo",
                "branch": "main"
            },
            "directories": {
                "sbo_obo_files": "TestFiles",
                "localfiles": "local",
                "customerfile": "customer",
                "logs": "logs"
            },
            "file_patterns": {
                "sbo_obo_json": "TEST_*.json",
                "timestamp_format": "%Y%m%d_%H%M%S",
                "log_filename": "test_log_{timestamp}.json"
            },
            "obo_conversion": {
                "field_order": ["id", "name", "comment", "is_a"],
                "typedef_field_order": ["id", "name", "is_transitive"]
            },
            "api": {
                "github_api_base": "https://api.test.com",
                "per_page": 5
            }
        }
    
    def test_config_load_success(self):
        """Test successful configuration loading"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_config_data, f)
            config_file = f.name
        
        try:
            config = Config(config_file)
            
            # Test GitHub properties
            self.assertEqual(config.github_url, "https://raw.githubusercontent.com/test/repo/master/file.obo")
            self.assertEqual(config.github_repo_owner, "test_owner")
            self.assertEqual(config.github_repo_name, "test_repo")
            self.assertEqual(config.github_file_path, "test.obo")
            self.assertEqual(config.github_branch, "main")
            
            # Test directory properties
            self.assertEqual(config.sbo_obo_files_dir, "TestFiles")
            self.assertEqual(config.localfiles_dir, "local")
            self.assertEqual(config.customerfile_dir, "customer")
            self.assertEqual(config.logs_dir, "logs")
            
            # Test file pattern properties
            self.assertEqual(config.sbo_obo_json_pattern, "TEST_*.json")
            self.assertEqual(config.timestamp_format, "%Y%m%d_%H%M%S")
            self.assertEqual(config.log_filename_pattern, "test_log_{timestamp}.json")
            
            # Test OBO conversion properties
            self.assertEqual(config.obo_field_order, ["id", "name", "comment", "is_a"])
            self.assertEqual(config.typedef_field_order, ["id", "name", "is_transitive"])
            
            # Test API properties
            self.assertEqual(config.github_api_base, "https://api.test.com")
            self.assertEqual(config.api_per_page, 5)
            
        finally:
            os.unlink(config_file)
    
    def test_config_file_not_found(self):
        """Test configuration error when file not found"""
        with self.assertRaises(ConfigurationError) as context:
            Config("nonexistent_file.json")
        
        self.assertIn("Failed to load configuration", str(context.exception))
    
    def test_config_invalid_json(self):
        """Test configuration error with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content {")
            config_file = f.name
        
        try:
            with self.assertRaises(ConfigurationError) as context:
                Config(config_file)
            
            self.assertIn("Failed to load configuration", str(context.exception))
        finally:
            os.unlink(config_file)
    
    @patch('os.path.dirname')
    @patch('builtins.open', new_callable=mock_open)
    def test_default_config_loading(self, mock_file, mock_dirname):
        """Test loading default config file"""
        mock_dirname.return_value = "/test/dir"
        mock_file.return_value.read.return_value = json.dumps(self.test_config_data)
        
        config = Config()
        
        # Verify the default config file path was used
        mock_file.assert_called_with("/test/dir/config.json", 'r', encoding='utf-8')
        self.assertEqual(config.github_repo_owner, "test_owner")


if __name__ == '__main__':
    unittest.main()