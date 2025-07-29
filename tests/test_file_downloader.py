import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from datetime import datetime
import sys

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ols_fetch_from_github.file_downloader import GitHubFileDownloader
from src.ols_fetch_from_github.config import Config


class TestGitHubFileDownloader(unittest.TestCase):
    """Test cases for GitHubFileDownloader class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_config = Mock(spec=Config)
        self.mock_config.github_api_base = "https://api.github.com"
        self.mock_config.github_repo_owner = "test_owner"
        self.mock_config.github_repo_name = "test_repo"
        self.mock_config.github_file_path = "test.obo"
        self.mock_config.github_branch = "master"
        self.mock_config.api_per_page = 1
        self.mock_config.github_url = "https://raw.githubusercontent.com/test_owner/test_repo/master/test.obo"
        self.mock_config.timestamp_format = "%Y%m%d_%H%M%S"

        self.downloader = GitHubFileDownloader(self.mock_config)

    @patch('src.ols_fetch_from_github.file_downloader.requests.get')
    def test_get_remote_file_info_success(self, mock_get):
        """Test successful remote file info retrieval"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'sha': 'abc123',
            'commit': {
                'committer': {'date': '2023-01-01T12:00:00Z'},
                'message': 'Test commit',
                'author': {'name': 'Test Author'}
            },
            'html_url': 'https://github.com/test_owner/test_repo/commit/abc123'
        }]
        mock_get.return_value = mock_response

        result = self.downloader.get_remote_file_info()

        # Verify API call
        expected_url = "https://api.github.com/repos/test_owner/test_repo/commits"
        expected_params = {
            'path': 'test.obo',
            'sha': 'master',
            'per_page': 1
        }
        mock_get.assert_called_once_with(expected_url, params=expected_params)

        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result['sha'], 'abc123')
        self.assertEqual(result['last_modified'], '2023-01-01T12:00:00Z')
        self.assertEqual(result['message'], 'Test commit')
        self.assertEqual(result['author'], 'Test Author')
        self.assertEqual(result['url'], 'https://github.com/test_owner/test_repo/commit/abc123')

    @patch('src.ols_fetch_from_github.file_downloader.requests.get')
    def test_get_remote_file_info_rate_limit(self, mock_get):
        """Test handling of GitHub API rate limit"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        result = self.downloader.get_remote_file_info()

        self.assertIsNone(result)

    @patch('src.ols_fetch_from_github.file_downloader.requests.get')
    def test_get_remote_file_info_not_found(self, mock_get):
        """Test handling of file not found"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = self.downloader.get_remote_file_info()

        self.assertIsNone(result)

    @patch('src.ols_fetch_from_github.file_downloader.requests.get')
    def test_get_remote_file_info_request_exception(self, mock_get):
        """Test handling of request exceptions"""
        mock_get.side_effect = Exception("Network error")

        result = self.downloader.get_remote_file_info()

        self.assertIsNone(result)

    @patch('src.ols_fetch_from_github.file_downloader.requests.get')
    @patch('builtins.open', create=True)
    def test_download_file_success(self, mock_open, mock_get):
        """Test successful file download"""
        # Mock remote file info
        remote_info = {
            'last_modified': '2023-01-01T12:00:00Z'
        }

        # Mock successful download response
        mock_response = Mock()
        mock_response.content = b"test file content"
        mock_get.return_value = mock_response

        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        result = self.downloader.download_file(remote_info)

        # Verify download request
        mock_get.assert_called_once_with(self.mock_config.github_url)

        # Verify file was written
        mock_file.write.assert_called_once_with(b"test file content")

        # Verify filename format
        self.assertIsNotNone(result)
        self.assertTrue(result.startswith("test_"))
        self.assertTrue(result.endswith(".obo"))

    @patch('src.ols_fetch_from_github.file_downloader.requests.get')
    def test_download_file_request_exception(self, mock_get):
        """Test handling of download request exceptions"""
        mock_get.side_effect = Exception("Download error")

        result = self.downloader.download_file()

        self.assertIsNone(result)

    @patch('src.ols_fetch_from_github.file_downloader.requests.get')
    @patch('builtins.open', create=True)
    def test_download_to_temp_success(self, mock_open, mock_get):
        """Test successful temporary file download"""
        remote_info = {'test': 'data'}

        # Mock successful download response
        mock_response = Mock()
        mock_response.content = b"temp file content"
        mock_get.return_value = mock_response

        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        result = self.downloader.download_to_temp(remote_info)

        # Verify download request
        mock_get.assert_called_once_with(self.mock_config.github_url)

        # Verify file was written
        mock_file.write.assert_called_once_with(b"temp file content")

        # Verify filename contains "temp"
        self.assertIsNotNone(result)
        self.assertIn("_temp_", result)

    @patch('src.ols_fetch_from_github.file_downloader.requests.get')
    def test_download_to_temp_exception(self, mock_get):
        """Test handling of temporary download exceptions"""
        mock_get.side_effect = Exception("Temp download error")

        result = self.downloader.download_to_temp({})

        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()