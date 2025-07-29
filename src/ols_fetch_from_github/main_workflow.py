
import os
import json
from .github_file_updater import GitHubFileUpdater
from .user_file_processor import UserFileProcessor
from .config import Config


class SBOWorkflowManager:
    """
    SBO File Workflow Manager - Integrates update detection and user file processing
    
    Description:
        Main workflow manager that orchestrates SBO ontology file updates, user file processing,
        and provides a unified interface for managing SBO files in the application.
    """
    
    def __init__(self):
        """
        Initialize SBO Workflow Manager
        
        Description:
            Sets up directory structure, initializes GitHub updater and user file processor,
            and prepares the workflow environment.
        
        Input:
            None
        
        Output:
            None (constructor)
        """
        self.active_file = None
        # Use SBO_OBO_Files directory under current script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.system_files_dir = os.path.join(script_dir, 'SBO_OBO_Files')
        self._ensure_sbo_obo_files_dir()
        
        # Switch to SBO_OBO_Files/localfiles directory for file operations
        self.original_cwd = os.getcwd()
        self.localfiles_dir = os.path.join(self.system_files_dir, "localfiles")
        self._ensure_localfiles_dir()
        os.chdir(self.localfiles_dir)
        
        # Initialize shared config
        self.config = Config()
        
        self.github_updater = GitHubFileUpdater(self.config)
        self.user_processor = UserFileProcessor(self.config)
    
    def run_workflow(self):
        """
        Run the complete workflow process
        
        Description:
            Executes the main workflow: checks for updates, handles user choices,
            and ensures an active SBO file is available for processing.
        
        Input:
            None
        
        Output:
            None (sets self.active_file)
        """
        print("🚀 Starting SBO file workflow")
        print("=" * 80)
        
        # Check for updates and auto-download if found
        print("\n🔍 Checking for remote file updates...")
        update_info = self._check_for_updates()
        
        if update_info:
            self._handle_updates_available(update_info)
        else:
            self._handle_no_updates()
        
        # Display final active file
        self._show_active_file()
    
    def _check_for_updates(self):
        """
        Check if updates are available and auto-download if found
        
        Description:
            Queries the GitHub repository to determine if the SBO ontology file
            has been updated since the last local download. If updates are found,
            automatically downloads them to temporary location for user review.
        
        Input:
            None
        
        Output:
            dict or None: Update information with temp files if updates found, None otherwise
        """
        try:
            status = self.github_updater.get_update_status()
            if status.get('needs_update', False):
                print("📦 Updates found! Downloading to temporary location...")
                update_info = self.github_updater.auto_download_update()
                return update_info
            return None
        except Exception as e:
            print(f"❌ Failed to check for updates: {e}")
            return None
    
    def _handle_updates_available(self, update_info):
        """
        Handle case when updates are available and already downloaded
        
        Description:
            Manages the workflow when remote updates are detected and downloaded.
            Shows changes to user and prompts for confirmation to apply the update.
        
        Input:
            update_info (dict): Information about the downloaded update including temp files and changes
        
        Output:
            None (may update self.active_file)
        """
        print("\n📋 File updates have been downloaded!")
        
        # Display changes if available
        if update_info and update_info.get('changes'):
            print("\n📊 Changes detected:")
            self._display_update_changes(update_info['changes'])
        
        # Ask user if they want to apply the update
        choice = self._get_user_choice("Do you want to apply these updates?", ["Yes", "No"])
        
        if choice == "Yes":
            print("\n🔄 Applying update...")
            success = self.github_updater.apply_downloaded_update(update_info)
            if success:
                # Find the updated JSON file
                self.active_file = self._find_latest_json_file()
                print("✅ Update applied successfully!")
            else:
                print("❌ Failed to apply update")
                self._handle_update_failed()
        else:
            print("\n❌ User chose not to apply update")
            # Clean up temporary files
            self.github_updater.cleanup_temp_update(update_info)
            self._handle_no_update_choice()
    
    def _display_update_changes(self, changes):
        """
        Display update changes to user using change logger
        
        Description:
            Shows a summary of changes detected in the update using the change logger.
        
        Input:
            changes (dict): Changes dictionary from comparison
        
        Output:
            None (prints information to console)
        """
        if not changes:
            print("  No detailed changes available")
            return
        
        # Use change logger to display changes
        from .change_logger import ChangeLogger
        logger = ChangeLogger()
        logger.display_change_summary(changes)
        
        # Show detailed changes with limit
        if changes.get('has_changes'):
            logger.display_detailed_changes(changes, limit=3)
    
    def _handle_no_updates(self):
        """
        Handle case when no updates are available
        
        Description:
            Manages the workflow when no remote updates are found,
            giving user options to upload their own file or use current version.
        
        Input:
            None
        
        Output:
            None (may set self.active_file)
        """
        print("✅ No updates found")
        
        # Check if we have existing files
        existing_file = self._find_latest_json_file()
        if existing_file:
            print(f"📁 Current version available: {existing_file}")
            # Give user choice to upload their own file or use current version
            self._handle_no_update_choice()
        else:
            print("⚠️  No existing JSON file found")
            self._handle_no_existing_file()
    
    def _handle_update_failed(self):
        """
        Handle case when update fails
        
        Description:
            Provides fallback options when the automatic update process fails,
            allowing user to choose alternative actions.
        
        Input:
            None
        
        Output:
            None (delegates to other handlers)
        """
        print("\n❌ Update failed, providing other options:")
        self._handle_no_update_choice()
    
    def _handle_no_update_choice(self):
        """
        Handle case when user chooses not to update
        
        Description:
            Provides alternative options when user declines to update,
            allowing file upload or use of existing files.
        
        Input:
            None
        
        Output:
            None (may set self.active_file)
        """
        choice = self._get_user_choice("Choose operation:", ["Upload your own file", "Use current file"])
        
        if choice == "Upload your own file":
            self._handle_file_upload()
        else:
            print("\n📂 Using current file")
            self.active_file = self._find_latest_json_file()
            if not self.active_file:
                print("⚠️  No existing JSON file found")
                self._handle_no_existing_file()
    
    def _handle_no_existing_file(self):
        """
        Handle case when no existing file is found
        
        Description:
            Manages the situation when no local SBO files exist,
            offering download or upload options to establish an active file.
        
        Input:
            None
        
        Output:
            None (may set self.active_file)
        """
        print("📋 No existing JSON file found")
        choice = self._get_user_choice("Choose operation:", ["Upload your own file", "Try to download latest file"])
        
        if choice == "Upload your own file":
            self._handle_file_upload()
        else:
            print("\n🔄 Trying to download latest file...")
            # Try to download and apply update
            update_info = self.github_updater.auto_download_update()
            if update_info:
                success = self.github_updater.apply_downloaded_update(update_info)
            else:
                success = False
            if success:
                self.active_file = self._find_latest_json_file()
                print("✅ Download completed!")
            else:
                print("❌ Download failed")
                self._handle_file_upload()
    
    def _handle_file_upload(self):
        """
        Handle file upload
        
        Description:
            Manages user file upload process, accepting both .json and .obo files,
            validating them, and processing them into the required format.
        
        Input:
            None (prompts user for file path)
        
        Output:
            None (may set self.active_file)
        """
        print("\n📤 File upload function")
        
        # Prompt user to enter file path
        file_path = input("Please enter file path (supports .json and .obo files): ").strip()
        
        if not file_path:
            print("❌ File path cannot be empty")
            self._handle_file_upload_failed()
            return
        
        if not os.path.exists(file_path):
            print(f"❌ File does not exist: {file_path}")
            self._handle_file_upload_failed()
            return
        
        # Process user file
        print(f"\n🔄 Processing file: {file_path}")
        success, json_file, message = self.user_processor.process_user_file(file_path)
        
        if success:
            self.active_file = json_file
            print(f"✅ File processing successful: {message}")
        else:
            print(f"❌ File processing failed: {message}")
            self._handle_file_upload_failed()
    
    def _handle_file_upload_failed(self):
        """
        Handle case when file upload fails
        
        Description:
            Provides recovery options when file upload or processing fails,
            allowing retry or fallback to existing files.
        
        Input:
            None
        
        Output:
            None (may set self.active_file)
        """
        choice = self._get_user_choice("File upload failed, choose operation:", ["Re-upload", "Use current file"])
        
        if choice == "Re-upload":
            self._handle_file_upload()
        else:
            self.active_file = self._find_latest_json_file()
            if not self.active_file:
                print("⚠️  No available files")
    
    def _find_latest_json_file(self):
        """
        Find the latest JSON file (in SBO_OBO_Files/localfiles directory)
        
        Description:
            Searches for the most recent SBO JSON file in the local files directory,
            using timestamp information in filenames for ordering.
        
        Input:
            None
        
        Output:
            str or None: Path to the latest JSON file, or None if no files found
        """
        import glob
        
        # Find all SBO JSON files in SBO_OBO_Files/localfiles directory
        json_files = glob.glob(os.path.join(self.system_files_dir, "localfiles", "SBO_OBO_*.json"))
        
        if not json_files:
            return None
        
        # Sort by filename, return latest (filename contains timestamp)
        json_files.sort(reverse=True)
        return json_files[0]
    
    def _get_user_choice(self, prompt, choices):
        """
        Get user choice
        
        Description:
            Presents a menu of options to the user and validates their selection,
            ensuring robust input handling with error recovery.
        
        Input:
            prompt (str): Question or instruction to display to user
            choices (list): List of available choice strings
        
        Output:
            str: Selected choice from the choices list
        """
        print(f"\n{prompt}")
        for i, choice in enumerate(choices, 1):
            print(f"{i}. {choice}")
        
        while True:
            try:
                choice_num = int(input("Please enter choice (number): ").strip())
                if 1 <= choice_num <= len(choices):
                    return choices[choice_num - 1]
                else:
                    print(f"Please enter a number between 1-{len(choices)}")
            except ValueError:
                print("Please enter a valid number")
    
    def _show_active_file(self):
        """
        Display current active file
        
        Description:
            Shows detailed information about the currently active SBO file,
            including statistics and file properties for user confirmation.
        
        Input:
            None
        
        Output:
            None (prints information to console)
        """
        print("\n" + "=" * 80)
        if self.active_file:
            print(f"📋 Active file is {self.active_file}")
            
            # Display basic file information
            try:
                with open(self.active_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"📊 File information:")
                print(f"  - Header fields count: {len(data.get('header', {}))}")
                print(f"  - Terms count: {len(data.get('terms', []))}")
                print(f"  - Typedefs count: {len(data.get('typedefs', []))}")
                
                # Display file size
                file_size = os.path.getsize(self.active_file)
                print(f"  - File size: {file_size:,} bytes")
                
            except Exception as e:
                print(f"⚠️  Failed to read file information: {e}")
        else:
            print("❌ No active file")
        print("=" * 80)
    
    def get_active_file(self):
        """
        Get current active file path
        
        Description:
            Returns the path to the currently active SBO JSON file
            for use by other modules or external callers.
        
        Input:
            None
        
        Output:
            str or None: Path to active file, or None if no active file
        """
        return self.active_file


    def _ensure_sbo_obo_files_dir(self):
        """
        Ensure SBO_OBO_Files directory exists
        
        Description:
            Creates the main SBO_OBO_Files directory if it doesn't exist,
            ensuring proper directory structure for file operations.
        
        Input:
            None
        
        Output:
            None (creates directory if needed)
        """
        if not os.path.exists(self.system_files_dir):
            os.makedirs(self.system_files_dir)
            print(f"📁 Created SBO_OBO_Files directory: {self.system_files_dir}")
    
    def _ensure_localfiles_dir(self):
        """
        Ensure SBO_OBO_Files/localfiles directory exists
        
        Description:
            Creates the localfiles subdirectory if it doesn't exist,
            providing a dedicated space for local SBO file storage.
        
        Input:
            None
        
        Output:
            None (creates directory if needed)
        """
        if not os.path.exists(self.localfiles_dir):
            os.makedirs(self.localfiles_dir)
            print(f"📁 Created localfiles directory: {self.localfiles_dir}")
    
    def cleanup(self):
        """
        Clean up resources and restore original working directory
        
        Description:
            Restores the original working directory and performs cleanup
            to ensure the environment is left in a clean state.
        
        Input:
            None
        
        Output:
            None (changes working directory)
        """
        if hasattr(self, 'original_cwd'):
            os.chdir(self.original_cwd)


def main():
    """
    Main function
    
    Description:
        Entry point for the SBO workflow application. Creates workflow manager,
        executes the complete workflow, and handles errors gracefully.
    
    Input:
        None
    
    Output:
        str or None: Path to the active SBO file if workflow completed successfully,
                     None if workflow failed or was interrupted
    """
    workflow = None
    try:
        workflow = SBOWorkflowManager()
        workflow.run_workflow()
        
        # Return active file path for other modules to use
        return workflow.get_active_file()
        
    except KeyboardInterrupt:
        print("\n\n👋 User interrupted program")
        return None
    except Exception as e:
        print(f"\n❌ Program execution error: {e}")
        return None
    finally:
        if workflow:
            workflow.cleanup()


if __name__ == "__main__":
    active_file = main()
    if active_file:
        print(f"\n🎉 Workflow completed, active file: {active_file}")
    else:
        print("\n😞 Workflow not completed")