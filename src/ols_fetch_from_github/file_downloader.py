import requests
import os
from datetime import datetime
from typing import Optional, Dict, Any
from .config import Config
from .utils import FileUtils


class GitHubFileDownloader:
    """Handles downloading files from GitHub repository"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def get_remote_file_info(self) -> Optional[Dict[str, Any]]:
        """
        Get latest commit information for the file from GitHub API
        
        Returns:
            dict or None: Dictionary containing commit info or None if API call fails
        """
        api_url = f"{self.config.github_api_base}/repos/{self.config.github_repo_owner}/{self.config.github_repo_name}/commits"
        
        params = {
            'path': self.config.github_file_path,
            'sha': self.config.github_branch,
            'per_page': self.config.api_per_page
        }
        
        try:
            print(f"Checking remote file updates: {self.config.github_file_path}")
            response = requests.get(api_url, params=params)
            
            if response.status_code == 403:
                print("GitHub API rate limit exceeded, please try again later")
                return None
            elif response.status_code == 404:
                print("File or repository does not exist")
                return None
            
            response.raise_for_status()
            
            commits = response.json()
            if commits:
                latest_commit = commits[0]
                print(f"Remote repository latest update time: {latest_commit['commit']['committer']['date']}")
                return {
                    'sha': latest_commit['sha'],
                    'last_modified': latest_commit['commit']['committer']['date'],
                    'message': latest_commit['commit']['message'],
                    'author': latest_commit['commit']['author']['name'],
                    'url': latest_commit['html_url']
                }
            else:
                print("No commit records found for the file")
                return None
                
        except Exception as e:
            print(f"Failed to get remote file information: {e}")
            return None
    
    def download_file(self, remote_info: Dict[str, Any] = None) -> Optional[str]:
        """
        Download file from GitHub
        
        Args:
            remote_info: Remote file information from get_remote_file_info()
            
        Returns:
            Path to downloaded file or None if download failed
        """
        try:
            # Get remote info if not provided
            if remote_info is None:
                remote_info = self.get_remote_file_info()
                if not remote_info:
                    return None
            
            # Generate timestamped filename
            if remote_info:
                commit_date = datetime.fromisoformat(remote_info['last_modified'].replace('Z', '+00:00'))
                timestamp_str = commit_date.strftime(self.config.timestamp_format)
            else:
                timestamp_str = datetime.now().strftime(self.config.timestamp_format)
            
            base_filename = os.path.basename(self.config.github_file_path)
            file_extension = os.path.splitext(base_filename)[1]
            file_basename = os.path.splitext(base_filename)[0]
            timestamped_filename = f"{file_basename}_{timestamp_str}{file_extension}"
            
            print(f"Downloading file: {timestamped_filename}")
            response = requests.get(self.config.github_url)
            response.raise_for_status()
            
            # Create backup if file already exists
            if os.path.exists(timestamped_filename):
                backup_name = f"{timestamped_filename}.backup"
                os.rename(timestamped_filename, backup_name)
                print(f"Backup file created: {backup_name}")
            
            # Save new file
            with open(timestamped_filename, 'wb') as f:
                f.write(response.content)
            
            print(f"File downloaded successfully: {timestamped_filename}")
            return timestamped_filename
            
        except Exception as e:
            print(f"Failed to download file: {e}")
            return None
    
    def download_to_temp(self, remote_info: Dict[str, Any]) -> Optional[str]:
        """
        Download file to temporary location
        
        Args:
            remote_info: Remote file commit information
            
        Returns:
            Path to downloaded temporary file or None if download failed
        """
        try:
            # Generate temporary filename
            timestamp = datetime.now().strftime(self.config.timestamp_format)
            base_filename = os.path.basename(self.config.github_file_path)
            file_extension = os.path.splitext(base_filename)[1]
            file_basename = os.path.splitext(base_filename)[0]
            temp_filename = f"{file_basename}_temp_{timestamp}{file_extension}"
            
            print(f"🔄 Downloading to temporary location: {temp_filename}")
            response = requests.get(self.config.github_url)
            response.raise_for_status()
            
            with open(temp_filename, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Temporary file downloaded successfully: {temp_filename}")
            return temp_filename
            
        except Exception as e:
            print(f"❌ Failed to download temporary file: {e}")
            return None