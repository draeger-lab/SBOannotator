import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ols_fetch_from_github.utils import FileUtils, DirectoryManager, ValidationResult
from src.ols_fetch_from_github.config import Config


class TestFileUtils(unittest.TestCase):
    """Test cases for FileUtils class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_ensure_directory_creates_new(self):
        """Test creating a new directory"""
        new_dir = os.path.join(self.test_dir, "new_directory")
        self.assertFalse(os.path.exists(new_dir))
        
        FileUtils.ensure_directory(new_dir)
        
        self.assertTrue(os.path.exists(new_dir))
        self.assertTrue(os.path.isdir(new_dir))
    
    def test_ensure_directory_existing(self):
        """Test with existing directory"""
        existing_dir = os.path.join(self.test_dir, "existing")
        os.makedirs(existing_dir)
        
        # Should not raise error
        FileUtils.ensure_directory(existing_dir)
        self.assertTrue(os.path.exists(existing_dir))
    
    def test_cleanup_files_success(self):
        """Test successful file cleanup"""
        # Create test files
        file1 = os.path.join(self.test_dir, "file1.txt")
        file2 = os.path.join(self.test_dir, "file2.txt")
        
        with open(file1, 'w') as f:
            f.write("test1")
        with open(file2, 'w') as f:
            f.write("test2")
        
        self.assertTrue(os.path.exists(file1))
        self.assertTrue(os.path.exists(file2))
        
        FileUtils.cleanup_files([file1, file2])
        
        self.assertFalse(os.path.exists(file1))
        self.assertFalse(os.path.exists(file2))
    
    def test_cleanup_files_nonexistent(self):
        """Test cleanup with non-existent files"""
        nonexistent_files = [
            os.path.join(self.test_dir, "nonexistent1.txt"),
            os.path.join(self.test_dir, "nonexistent2.txt")
        ]
        
        # Should not raise error
        FileUtils.cleanup_files(nonexistent_files)
    
    def test_cleanup_files_mixed(self):
        """Test cleanup with mix of existing and non-existent files"""
        file1 = os.path.join(self.test_dir, "existing.txt")
        file2 = os.path.join(self.test_dir, "nonexistent.txt")
        
        with open(file1, 'w') as f:
            f.write("test")
        
        FileUtils.cleanup_files([file1, file2, None, ""])
        
        self.assertFalse(os.path.exists(file1))
    
    def test_find_latest_timestamped_file_success(self):
        """Test finding latest timestamped file"""
        # Create test files with timestamps
        files = [
            "SBO_OBO_20230101_120000.obo",
            "SBO_OBO_20230201_120000.obo", 
            "SBO_OBO_20230301_120000.obo"
        ]
        
        for filename in files:
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, 'w') as f:
                f.write("test")
        
        result = FileUtils.find_latest_timestamped_file("SBO_OBO_*.obo", self.test_dir)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.endswith("SBO_OBO_20230301_120000.obo"))
    
    def test_find_latest_timestamped_file_none(self):
        """Test finding file when none exist"""
        result = FileUtils.find_latest_timestamped_file("SBO_OBO_*.obo", self.test_dir)
        
        self.assertIsNone(result)
    
    def test_generate_timestamped_filename(self):
        """Test generating timestamped filename"""
        base_filename = "test.obo"
        test_timestamp = datetime(2023, 1, 15, 14, 30, 45)
        
        with patch('src.ols_fetch_from_github.utils.Config') as mock_config_class:
            mock_config = Mock()
            mock_config.timestamp_format = "%Y%m%d_%H%M%S"
            mock_config_class.return_value = mock_config
            
            result = FileUtils.generate_timestamped_filename(base_filename, test_timestamp)
            
            self.assertEqual(result, "test_20230115_143045.obo")
    
    def test_generate_timestamped_filename_current_time(self):
        """Test generating timestamped filename with current time"""
        base_filename = "test.json"
        
        with patch('src.ols_fetch_from_github.utils.Config') as mock_config_class:
            mock_config = Mock()
            mock_config.timestamp_format = "%Y%m%d_%H%M%S"
            mock_config_class.return_value = mock_config
            
            with patch('src.ols_fetch_from_github.utils.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2023, 5, 10, 10, 15, 30)
                
                result = FileUtils.generate_timestamped_filename(base_filename)
                
                self.assertEqual(result, "test_20230510_101530.json")


class TestDirectoryManager(unittest.TestCase):
    """Test cases for DirectoryManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_config = Mock(spec=Config)
        self.mock_config.sbo_obo_files_dir = "TestSBO"
        self.mock_config.localfiles_dir = "local"
        self.mock_config.customerfile_dir = "customer"
        self.mock_config.logs_dir = "logs"
        
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('src.ols_fetch_from_github.utils.os.path.dirname')
    @patch('src.ols_fetch_from_github.utils.os.path.abspath')
    def test_directory_paths(self, mock_abspath, mock_dirname):
        """Test directory path generation"""
        mock_abspath.return_value = "/fake/path/file.py"
        mock_dirname.return_value = "/fake/path"
        
        manager = DirectoryManager(self.mock_config)
        
        self.assertEqual(manager.get_sbo_obo_files_dir(), "/fake/path/TestSBO")
        self.assertEqual(manager.get_localfiles_dir(), "/fake/path/TestSBO/local")
        self.assertEqual(manager.get_customerfile_dir(), "/fake/path/TestSBO/customer")
        self.assertEqual(manager.get_logs_dir(), "/fake/path/TestSBO/logs")
    
    @patch('src.ols_fetch_from_github.utils.FileUtils.ensure_directory')
    @patch('src.ols_fetch_from_github.utils.os.path.dirname')
    @patch('src.ols_fetch_from_github.utils.os.path.abspath')
    def test_ensure_all_directories(self, mock_abspath, mock_dirname, mock_ensure):
        """Test ensuring all directories exist"""
        mock_abspath.return_value = "/fake/path/file.py"
        mock_dirname.return_value = "/fake/path"
        
        manager = DirectoryManager(self.mock_config)
        manager.ensure_all_directories()
        
        # Should call ensure_directory for each directory
        self.assertEqual(mock_ensure.call_count, 4)
        expected_calls = [
            "/fake/path/TestSBO",
            "/fake/path/TestSBO/local", 
            "/fake/path/TestSBO/customer",
            "/fake/path/TestSBO/logs"
        ]
        
        actual_calls = [call[0][0] for call in mock_ensure.call_args_list]
        for expected in expected_calls:
            self.assertIn(expected, actual_calls)


class TestValidationResult(unittest.TestCase):
    """Test cases for ValidationResult class"""
    
    def test_validation_result_success(self):
        """Test successful validation result"""
        data = {"key": "value", "count": 42}
        result = ValidationResult(True, "Success message", data)
        
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Success message")
        self.assertEqual(result.data, data)
    
    def test_validation_result_failure(self):
        """Test failed validation result"""
        result = ValidationResult(False, "Error message")
        
        self.assertFalse(result.success)
        self.assertEqual(result.message, "Error message")
        self.assertEqual(result.data, {})
    
    def test_to_tuple_success(self):
        """Test tuple conversion for success"""
        data = {"items": [1, 2, 3]}
        result = ValidationResult(True, "All good", data)
        
        success, returned_data, message = result.to_tuple()
        
        self.assertTrue(success)
        self.assertEqual(returned_data, data)
        self.assertEqual(message, "All good")
    
    def test_to_tuple_failure(self):
        """Test tuple conversion for failure"""
        result = ValidationResult(False, "Something went wrong")
        
        success, returned_data, message = result.to_tuple()
        
        self.assertFalse(success)
        self.assertEqual(returned_data, {})
        self.assertEqual(message, "Something went wrong")


if __name__ == '__main__':
    unittest.main()