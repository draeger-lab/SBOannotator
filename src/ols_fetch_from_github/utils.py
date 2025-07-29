import os
import glob
import shutil
from datetime import datetime
from typing import List, Optional, Tuple
from .config import Config


class FileUtils:
    """Utility functions for file operations"""

    @staticmethod
    def ensure_directory(directory_path: str) -> None:
        """
        Ensure directory exists, create if it doesn't

        Args:
            directory_path: Path to directory
        """
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            print(f"📁 Created directory: {directory_path}")

    @staticmethod
    def cleanup_files(file_paths: List[str]) -> None:
        """
        Clean up multiple files

        Args:
            file_paths: List of file paths to remove
        """
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"🗑️ Cleaned up file: {file_path}")
                except Exception as e:
                    print(f"❌ Failed to clean up file {file_path}: {e}")

    @staticmethod
    def find_latest_timestamped_file(pattern: str, directory: str = ".") -> Optional[str]:
        """
        Find the latest timestamped file matching pattern

        Args:
            pattern: Glob pattern to match files
            directory: Directory to search in

        Returns:
            Path to latest file or None if no files found
        """
        search_pattern = os.path.join(directory, pattern)
        matching_files = glob.glob(search_pattern)

        if not matching_files:
            return None

        # Sort by timestamp in filename (assumes timestamp is in filename)
        matching_files.sort(reverse=True)
        return matching_files[0]

    @staticmethod
    def generate_timestamped_filename(base_filename: str, timestamp: datetime = None) -> str:
        """
        Generate timestamped filename

        Args:
            base_filename: Base filename without extension
            timestamp: Datetime object, uses current time if None

        Returns:
            Timestamped filename
        """
        if timestamp is None:
            timestamp = datetime.now()

        config = Config()
        timestamp_str = timestamp.strftime(config.timestamp_format)

        file_extension = os.path.splitext(base_filename)[1]
        file_basename = os.path.splitext(base_filename)[0]

        return f"{file_basename}_{timestamp_str}{file_extension}"


class DirectoryManager:
    """Manages directory structure for the application"""

    def __init__(self, config: Config):
        self.config = config
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

    def get_sbo_obo_files_dir(self) -> str:
        """Get SBO_OBO_Files directory path"""
        return os.path.join(self.script_dir, self.config.sbo_obo_files_dir)

    def get_localfiles_dir(self) -> str:
        """Get localfiles directory path"""
        return os.path.join(self.get_sbo_obo_files_dir(), self.config.localfiles_dir)

    def get_customerfile_dir(self) -> str:
        """Get customerfile directory path"""
        return os.path.join(self.get_sbo_obo_files_dir(), self.config.customerfile_dir)

    def get_logs_dir(self) -> str:
        """Get logs directory path"""
        return os.path.join(self.get_sbo_obo_files_dir(), self.config.logs_dir)

    def ensure_all_directories(self) -> None:
        """Ensure all required directories exist"""
        directories = [
            self.get_sbo_obo_files_dir(),
            self.get_localfiles_dir(),
            self.get_customerfile_dir(),
            self.get_logs_dir()
        ]

        for directory in directories:
            FileUtils.ensure_directory(directory)


class ValidationResult:
    """Represents the result of a validation operation"""

    def __init__(self, success: bool, message: str, data: dict = None):
        self.success = success
        self.message = message
        self.data = data or {}

    def to_tuple(self) -> Tuple[bool, dict, str]:
        """Convert to tuple format for backward compatibility"""
        return self.success, self.data, self.message