import os
import json
import shutil
from datetime import datetime
from typing import Optional, Dict, Any

from .config import Config
from .utils import FileUtils, DirectoryManager
from .file_downloader import GitHubFileDownloader
from .obo_parser import OBOFileParser
from .file_converter import FileConverter
from .file_validator import FileValidator
from .file_comparator import FileComparator


class GitHubFileUpdater:
    """
    GitHub file updater following SOLID principles
    
    This class orchestrates the update process by coordinating
    specialized components for downloading, parsing, converting, and validating files.
    """
    
    def __init__(self, config=None):
        """
        Initialize GitHub file updater with dependency injection
        
        Args:
            config: Configuration object. If None, uses default config.
        """
        self.config = config or Config()
        self.directory_manager = DirectoryManager(self.config)
        
        # Injected dependencies
        self.downloader = GitHubFileDownloader(self.config)
        self.parser = OBOFileParser(self.config)
        self.converter = FileConverter(self.config)
        self.validator = FileValidator()
        self.comparator = FileComparator()
        
        self.base_filename = os.path.basename(self.config.github_file_path)
        
        # Initialize directory structure
        self.directory_manager.ensure_all_directories()
        
        # Switch to localfiles directory for file operations
        self.original_cwd = os.getcwd()
        self.localfiles_dir = self.directory_manager.get_localfiles_dir()
        os.chdir(self.localfiles_dir)
        
        # Find latest local file
        self.local_filename = self._find_latest_local_file()
        self.info_file = f"{self.local_filename}.update_info" if self.local_filename else f"{self.base_filename}.update_info"
    
    def get_update_status(self) -> Dict[str, Any]:
        """
        Get file update status information
        
        Returns:
            Status dictionary containing local file existence, remote info availability,
            update necessity, and version timestamps
        """
        remote_info = self.downloader.get_remote_file_info()
        local_info = self.load_local_info()
        
        status = {
            'local_file_exists': self.local_filename is not None and os.path.exists(self.local_filename),
            'has_local_info': local_info is not None,
            'remote_info_available': remote_info is not None,
            'needs_update': False
        }
        
        if remote_info:
            if local_info:
                status['needs_update'] = local_info.get('sha') != remote_info['sha']
                status['local_sha'] = local_info.get('sha', '')
                status['local_update_time'] = local_info.get('local_update_time', '')
            else:
                # No local info means we need to update
                status['needs_update'] = True
                status['local_sha'] = False
                status['local_update_time'] = False
            
            status['remote_sha'] = remote_info['sha']
            status['remote_update_time'] = remote_info['last_modified']
        
        return status
    
    def auto_download_update(self) -> Optional[Dict[str, Any]]:
        """
        Automatically download update to temporary location and compare changes
        
        Returns:
            Update information dictionary containing temp files, changes, and metadata
        """
        # Get remote file information
        remote_info = self.downloader.get_remote_file_info()
        if not remote_info:
            print("❌ Unable to get remote file information")
            return None
        
        # Download to temporary location
        temp_file = self.downloader.download_to_temp(remote_info)
        if not temp_file:
            print("❌ Failed to download temporary file")
            return None
        
        try:
            # Convert and validate temporary file
            temp_json = self._convert_and_validate_temp(temp_file)
            if not temp_json:
                print("❌ Temporary file conversion validation failed")
                FileUtils.cleanup_files([temp_file])
                return None
            
            # Compare changes (if local file exists)
            changes = None
            if self.local_filename and os.path.exists(self.local_filename):
                local_json = self._ensure_local_json()
                if local_json:
                    changes = self.comparator.compare_json_files(local_json, temp_json)
            
            # Return comprehensive update information
            return {
                'temp_obo_file': temp_file,
                'temp_json_file': temp_json,
                'remote_info': remote_info,
                'changes': changes,
                'has_changes': changes.get('has_changes', False) if changes else False
            }
            
        except Exception as e:
            print(f"❌ Auto-download update failed: {e}")
            FileUtils.cleanup_files([temp_file])
            return None
    
    def apply_downloaded_update(self, update_info: Dict[str, Any]) -> bool:
        """
        Apply previously downloaded update
        
        Args:
            update_info: Update information from auto_download_update
            
        Returns:
            True if update applied successfully, False otherwise
        """
        if not update_info:
            print("❌ No update information provided")
            return False
        
        try:
            temp_file = update_info['temp_obo_file']
            temp_json = update_info['temp_json_file']
            remote_info = update_info['remote_info']
            changes = update_info.get('changes')
            
            # Apply the update
            success = self._apply_update(temp_file, temp_json, remote_info, changes)
            return success
            
        except Exception as e:
            print(f"❌ Failed to apply downloaded update: {e}")
            self.cleanup_temp_update(update_info)
            return False
    
    def cleanup_temp_update(self, update_info: Dict[str, Any]) -> None:
        """
        Clean up temporary files from auto-downloaded update
        
        Args:
            update_info: Update information containing temp file paths
        """
        if not update_info:
            return
        
        temp_files = []
        if 'temp_obo_file' in update_info:
            temp_files.append(update_info['temp_obo_file'])
        if 'temp_json_file' in update_info:
            temp_files.append(update_info['temp_json_file'])
        
        FileUtils.cleanup_files(temp_files)
        print("🗑️ Temporary update files cleaned up")
    
    
    def load_local_info(self) -> Optional[Dict[str, Any]]:
        """
        Load locally saved file information
        
        Returns:
            Dictionary containing local file metadata or None if file doesn't exist
        """
        if os.path.exists(self.info_file):
            try:
                with open(self.info_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"Failed to read local info file: {self.info_file}")
                return None
        return None
    
    def save_local_info(self, info: Dict[str, Any]) -> None:
        """
        Save file information locally
        
        Args:
            info: File information dictionary containing commit details
        """
        try:
            info['local_update_time'] = datetime.now().isoformat()
            with open(self.info_file, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Failed to save local info: {e}")
    
    def cleanup(self) -> None:
        """Clean up resources and restore original working directory"""
        if hasattr(self, 'original_cwd'):
            os.chdir(self.original_cwd)
    
    def _find_latest_local_file(self) -> Optional[str]:
        """Find the latest local file with timestamp"""
        pattern = f"{os.path.splitext(self.config.github_file_path)[0]}_*.{os.path.splitext(self.config.github_file_path)[1][1:]}"
        return FileUtils.find_latest_timestamped_file(pattern, self.localfiles_dir)
    
    def _convert_and_validate_temp(self, temp_file: str) -> Optional[str]:
        """
        Convert temporary OBO file to JSON and perform validation
        
        Args:
            temp_file: Path to the temporary OBO file
            
        Returns:
            Path to generated JSON file if validation successful, None if validation failed
        """
        try:
            base_name = os.path.splitext(temp_file)[0]
            temp_json = f"{base_name}.json"
            temp_converted_obo = f"{base_name}_converted.obo"
            
            print("🔄 Starting temporary file conversion validation process...")
            
            # Step 1: OBO → JSON
            print("1️⃣ Temporary file OBO → JSON")
            data = self.parser.parse_obo_file(temp_file)
            with open(temp_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Temporary JSON file generated: {temp_json}")
            
            # Step 2: JSON → OBO
            print("2️⃣ Temporary file JSON → OBO")
            self.converter.convert_json_to_obo(temp_json, temp_converted_obo)
            print(f"✅ Temporary converted OBO file generated: {temp_converted_obo}")
            
            # Step 3: Validate roundtrip conversion
            print("3️⃣ Validate temporary file roundtrip conversion")
            validation_success = self.validator.validate_roundtrip_conversion(temp_file, temp_converted_obo)
            
            # Clean up conversion file
            if os.path.exists(temp_converted_obo):
                os.remove(temp_converted_obo)
                print(f"🗑️ Cleaned up temporary conversion file: {temp_converted_obo}")
            
            if validation_success:
                print("✅ Temporary file conversion validation passed")
                return temp_json
            else:
                print("❌ Temporary file conversion validation failed")
                if os.path.exists(temp_json):
                    os.remove(temp_json)
                return None
                
        except Exception as e:
            print(f"❌ Temporary file conversion validation failed: {e}")
            # Clean up potentially generated files
            temp_files = [
                f"{os.path.splitext(temp_file)[0]}.json",
                f"{os.path.splitext(temp_file)[0]}_converted.obo"
            ]
            FileUtils.cleanup_files(temp_files)
            return None
    
    def _ensure_local_json(self) -> Optional[str]:
        """
        Ensure local JSON file exists for comparison
        
        Returns:
            Path to local JSON file, or None if generation failed
        """
        if not self.local_filename:
            return None
        
        # Check if corresponding JSON file already exists
        base_name = os.path.splitext(self.local_filename)[0]
        local_json = f"{base_name}.json"
        
        if os.path.exists(local_json):
            return local_json
        
        # If not, generate JSON from OBO file
        try:
            print("🔄 Generating JSON for local file for comparison...")
            data = self.parser.parse_obo_file(self.local_filename)
            
            with open(local_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Local JSON file generated: {local_json}")
            return local_json
            
        except Exception as e:
            print(f"❌ Failed to generate local JSON file: {e}")
            return None
    
    def _apply_update(self, temp_file: str, temp_json: str, remote_info: Dict[str, Any], changes: Optional[Dict[str, Any]]) -> bool:
        """
        Apply update by moving temporary files to their official locations
        
        Args:
            temp_file: Path to temporary OBO file
            temp_json: Path to temporary JSON file
            remote_info: Remote file commit information
            changes: Detected changes between versions
            
        Returns:
            True if update applied successfully, False if errors occurred
        """
        try:
            # Generate official filename
            commit_date = datetime.fromisoformat(remote_info['last_modified'].replace('Z', '+00:00'))
            timestamp = commit_date.strftime(self.config.timestamp_format)
            base_filename = os.path.basename(self.config.github_file_path)
            file_extension = os.path.splitext(base_filename)[1]
            file_basename = os.path.splitext(base_filename)[0]
            new_filename = f"{file_basename}_{timestamp}{file_extension}"
            new_json_filename = f"{file_basename}_{timestamp}.json"
            
            # Move temporary files to official location
            shutil.move(temp_file, new_filename)
            shutil.move(temp_json, new_json_filename)
            
            # Update instance attributes
            self.local_filename = new_filename
            self.info_file = f"{new_filename}.update_info"
            
            print(f"✅ File updated: {new_filename}")
            print(f"✅ JSON file updated: {new_json_filename}")
            
            # Record change log
            if changes and changes.get('has_changes'):
                from .change_logger import ChangeLogger
                logger = ChangeLogger()
                logger.log_changes(changes, None, remote_info)
            
            # Save update information
            self.save_local_info(remote_info)
            
            # Clean up old versions (keep policy as is - 2 versions)
            self._cleanup_old_versions()
            
            print("🎉 Update completed!")
            return True
                
        except Exception as e:
            print(f"❌ Failed to apply update: {e}")
            return False
    
    def _cleanup_old_versions(self) -> None:
        """Keep the latest two timestamp versions, delete older ones"""
        import glob
        
        # Construct filename pattern
        base_filename = os.path.basename(self.config.github_file_path)
        file_extension = os.path.splitext(base_filename)[1]
        file_basename = os.path.splitext(base_filename)[0]
        pattern = f"{file_basename}_*{file_extension}"
        
        # Find all matching files, exclude converted files
        all_files = glob.glob(pattern)
        matching_files = [f for f in all_files if not f.endswith(f'_converted{file_extension}')]
        
        # Count timestamps
        timestamps = set()
        for file in matching_files:
            basename = os.path.splitext(file)[0]
            timestamp_part = basename.replace(file_basename + '_', '')
            timestamps.add(timestamp_part)
        
        if len(timestamps) <= 2:
            print(f"📁 Currently have {len(timestamps)} timestamp versions, no cleanup needed")
            return
        
        # Sort by timestamp and keep latest 2
        matching_files.sort(key=lambda f: os.path.splitext(f)[0].replace(file_basename + '_', ''), reverse=True)
        
        # Delete oldest timestamp version
        oldest_file = matching_files[-1]
        oldest_basename = os.path.splitext(oldest_file)[0]
        oldest_timestamp = oldest_basename.replace(file_basename + '_', '')
        
        print(f"🗑️ Will delete timestamp: {oldest_timestamp}")
        
        # Delete complete file set of earliest timestamp
        files_to_delete = [
            oldest_file,
            f"{oldest_file}.update_info",
            f"{oldest_basename}.json",
            f"{oldest_basename}_converted{file_extension}"
        ]
        
        deleted_count = 0
        for file_to_delete in files_to_delete:
            if os.path.exists(file_to_delete):
                try:
                    os.remove(file_to_delete)
                    print(f"🗑️ Deleted file: {file_to_delete}")
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ Failed to delete file {file_to_delete}: {e}")
        
        print(f"✅ Version cleanup completed, deleted {deleted_count} files")

