"""
OLS Fetch from GitHub Module

This module provides functionality to fetch and manage SBO (Systems Biology Ontology) 
files from GitHub repositories with update detection and user file processing capabilities.

Main Components:
- SBOWorkflowManager: Main workflow orchestrator
- GitHubFileUpdater: GitHub file download and update management
- UserFileProcessor: Process user-uploaded files
- FileComparator: Compare files for changes
- OBOFileParser: Parse OBO format files
- FileConverter: Convert between different file formats
- FileValidator: Validate file integrity
- ChangeLogger: Log and display file changes
- Config: Configuration management
- FileUtils: File utilities
"""

from .main_workflow import SBOWorkflowManager
from .github_file_updater import GitHubFileUpdater
from .user_file_processor import UserFileProcessor
from .file_comparator import FileComparator
from .obo_parser import OBOFileParser
from .file_converter import FileConverter
from .file_validator import FileValidator
from .change_logger import ChangeLogger
from .config import Config
from .utils import FileUtils, DirectoryManager, ValidationResult
from .file_downloader import GitHubFileDownloader

__version__ = "1.0.0"
__author__ = "SBOannotator Team"

__all__ = [
    "SBOWorkflowManager",
    "GitHubFileUpdater", 
    "UserFileProcessor",
    "FileComparator",
    "OBOFileParser",
    "FileConverter",
    "FileValidator",
    "ChangeLogger",
    "Config",
    "FileUtils",
    "DirectoryManager",
    "ValidationResult",
    "GitHubFileDownloader",
]