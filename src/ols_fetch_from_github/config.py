import json
import os
from typing import Dict, Any


class Config:
    """Configuration management for ols_fetch_from_github module"""
    
    def __init__(self, config_file: str = None):
        """
        Initialize configuration
        
        Args:
            config_file: Path to configuration file. If None, uses default config.json
        """
        if config_file is None:
            # Use absolute path to config.json in the same directory as this file
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        
        self._config = self._load_config(config_file)
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ConfigurationError(f"Failed to load configuration from {config_file}: {e}")
    
    @property
    def github_url(self) -> str:
        return self._config['github']['url']
    
    @property
    def github_repo_owner(self) -> str:
        return self._config['github']['repo_owner']
    
    @property
    def github_repo_name(self) -> str:
        return self._config['github']['repo_name']
    
    @property
    def github_file_path(self) -> str:
        return self._config['github']['file_path']
    
    @property
    def github_branch(self) -> str:
        return self._config['github']['branch']
    
    @property
    def sbo_obo_files_dir(self) -> str:
        return self._config['directories']['sbo_obo_files']
    
    @property
    def localfiles_dir(self) -> str:
        return self._config['directories']['localfiles']
    
    @property
    def customerfile_dir(self) -> str:
        return self._config['directories']['customerfile']
    
    @property
    def logs_dir(self) -> str:
        return self._config['directories']['logs']
    
    @property
    def sbo_obo_json_pattern(self) -> str:
        return self._config['file_patterns']['sbo_obo_json']
    
    @property
    def timestamp_format(self) -> str:
        return self._config['file_patterns']['timestamp_format']
    
    @property
    def log_filename_pattern(self) -> str:
        return self._config['file_patterns']['log_filename']
    
    @property
    def obo_field_order(self) -> list:
        return self._config['obo_conversion']['field_order']
    
    @property
    def typedef_field_order(self) -> list:
        return self._config['obo_conversion']['typedef_field_order']
    
    @property
    def github_api_base(self) -> str:
        return self._config['api']['github_api_base']
    
    @property
    def api_per_page(self) -> int:
        return self._config['api']['per_page']


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors"""
    pass