import os
import json
import shutil
import glob
from datetime import datetime
from .config import Config
from .obo_parser import OBOFileParser
from .file_converter import FileConverter
from .file_validator import FileValidator


class UserFileProcessor:
    """
    User File Processor - Process user uploaded JSON and OBO files
    
    Description:
        Handles validation, conversion, and processing of user-uploaded SBO ontology files,
        supporting both JSON and OBO formats with comprehensive validation and error handling.
    """
    
    def __init__(self, config):
        """
        Initialize User File Processor
        
        Description:
            Sets up the processor with customer file directory, ensures directory structure,
            and cleans up any old files to maintain a clean working environment.
        
        Input:
            config: Configuration object
        
        Output:
            None (constructor)
        """
        self.processed_files = []
        
        # Initialize components
        self.config = config
        self.obo_parser = OBOFileParser(self.config)
        self.file_converter = FileConverter(self.config)
        self.file_validator = FileValidator()
        
        # Use SBO_OBO_Files/customerfile under the current script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sbo_obo_files_dir = os.path.join(script_dir, 'SBO_OBO_Files')
        self.customer_file_dir = os.path.join(sbo_obo_files_dir, "customerfile")
        self._ensure_customer_dir()
        self._cleanup_old_files()
        
    def process_user_file(self, file_path):
        """
        Process user uploaded file
        
        Description:
            Main entry point for processing user files. Handles both JSON and OBO formats,
            performs validation, and returns the processed JSON file path.
        
        Input:
            file_path (str): Path to user uploaded file (.json or .obo)
            
        Output:
            tuple: (success, json_file_path, message)
                   - success (bool): True if processing succeeded
                   - json_file_path (str or None): Path to processed JSON file
                   - message (str): Descriptive message about the result
        """
        if not os.path.exists(file_path):
            return False, None, f"File does not exist: {file_path}"
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        print(f"📁 Processing user file: {file_path}")
        print(f"📋 File type: {file_extension}")
        
        # First copy the file to customerfile directory
        copied_file = self._copy_file_to_customer_dir(file_path)
        if not copied_file:
            return False, None, "Failed to copy file to customerfile directory"
        
        print(f"📋 File copied to customerfile directory: {copied_file}")
        
        if file_extension == '.json':
            return self._process_json_file(copied_file)
        elif file_extension == '.obo':
            return self._process_obo_file(copied_file)
        else:
            return False, None, f"Unsupported file type: {file_extension}, only .json and .obo files are supported"
    
    def _process_json_file(self, json_file):
        """
        Process JSON file - Validate structure and content
        
        Description:
            Validates a JSON file's structure against SBO format requirements,
            ensuring it contains required fields and proper data types.
        
        Input:
            json_file (str): Path to the JSON file to process
        
        Output:
            tuple: (success, json_file_path, message) indicating validation result
        """
        print("🔍 Validating JSON file structure...")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate JSON structure
            validation_result = self._validate_json_structure(data)
            if not validation_result['valid']:
                return False, None, f"JSON structure validation failed: {validation_result['message']}"
            
            print("✅ JSON file structure validation passed")
            print(f"📊 Statistics: {validation_result['stats']}")
            
            # Save processing record
            self.processed_files.append({
                'original_file': json_file,
                'final_file': json_file,
                'type': 'json',
                'status': 'validated'
            })
            
            return True, json_file, "JSON file validation successful"
            
        except json.JSONDecodeError as e:
            return False, None, f"JSON format error: {e}"
        except Exception as e:
            return False, None, f"Error processing JSON file: {e}"
    
    def _process_obo_file(self, obo_file):
        """
        Process OBO file - Convert to JSON and validate roundtrip
        
        Description:
            Converts an OBO file to JSON format, validates the conversion through
            roundtrip testing (OBO->JSON->OBO), and ensures data integrity.
        
        Input:
            obo_file (str): Path to the OBO file to process
        
        Output:
            tuple: (success, json_file_path, message) indicating conversion and validation result
        """
        print("🔄 Converting OBO file to JSON...")
        
        try:
            # Generate filenames
            base_name = os.path.splitext(obo_file)[0]
            json_file = f"{base_name}_user_upload.json"
            converted_obo_file = f"{base_name}_user_upload_converted.obo"
            
            # Step 1: Parse OBO file and convert to JSON
            print("1️⃣ Parsing OBO file...")
            data = self.obo_parser.parse_obo_file(obo_file)
            
            # Save as JSON
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ JSON file saved: {json_file}")
            
            # Step 2: Validate converted JSON structure
            print("2️⃣ Validating converted JSON structure...")
            validation_result = self._validate_json_structure(data)
            if not validation_result['valid']:
                self._cleanup_temp_files([json_file, converted_obo_file])
                return False, None, f"Converted JSON structure validation failed: {validation_result['message']}"
            
            print("✅ Converted JSON structure validation passed")
            print(f"📊 Statistics: {validation_result['stats']}")
            
            # Step 3: JSON -> OBO roundtrip conversion validation
            print("3️⃣ Performing roundtrip conversion validation...")
            self.file_converter.convert_json_to_obo(json_file, converted_obo_file)
            print(f"✅ Converted OBO file saved: {converted_obo_file}")
            
            # Step 4: Validate roundtrip conversion
            print("4️⃣ Validating roundtrip conversion result...")
            roundtrip_success = self.file_validator.validate_roundtrip_conversion(obo_file, converted_obo_file)
            
            if not roundtrip_success:
                self._cleanup_temp_files([json_file, converted_obo_file])
                return False, None, "Roundtrip conversion validation failed, OBO file may have format issues"
            
            print("🎉 Roundtrip conversion validation successful!")
            
            # Step 5: Clean up files - keep only JSON
            print("5️⃣ Cleaning up files...")
            if os.path.exists(obo_file):
                os.remove(obo_file)
                print(f"🗑️  Deleted original OBO file: {obo_file}")
            
            if os.path.exists(converted_obo_file):
                os.remove(converted_obo_file)
                print(f"🗑️  Deleted temporary conversion file: {converted_obo_file}")
            
            # Save processing record
            self.processed_files.append({
                'original_file': obo_file,
                'final_file': json_file,
                'type': 'obo',
                'status': 'converted_and_validated'
            })
            
            return True, json_file, "OBO file converted to JSON and validation successful"
            
        except Exception as e:
            # Clean up potentially generated files
            temp_files = [
                f"{os.path.splitext(obo_file)[0]}_user_upload.json",
                f"{os.path.splitext(obo_file)[0]}_user_upload_converted.obo"
            ]
            self._cleanup_temp_files(temp_files)
            return False, None, f"Error processing OBO file: {e}"
    
    def _cleanup_temp_files(self, file_list):
        """
        Clean up temporary files
        
        Description:
            Removes temporary files created during processing to avoid
            cluttering the file system and maintain clean working directory.
        
        Input:
            file_list (list): List of file paths to remove
        
        Output:
            None (files are deleted from filesystem)
        """
        for file_path in file_list:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"🗑️  Cleaned up temporary file: {file_path}")
                except Exception as e:
                    print(f"❌ Failed to clean up file {file_path}: {e}")
    
    def _validate_json_structure(self, data):
        """
        Validate JSON structure conforms to SBO format
        
        Description:
            Performs comprehensive validation of JSON data structure, checking for
            required fields, data types, and SBO-specific format requirements.
        
        Input:
            data (dict): Parsed JSON data to validate
        
        Output:
            dict: Validation result containing 'valid' (bool), 'message' (str), and 'stats' (dict)
        """
        try:
            # Check required top-level fields
            required_fields = ['header', 'terms']
            for field in required_fields:
                if field not in data:
                    return {
                        'valid': False,
                        'message': f"Missing required field: {field}",
                        'stats': {}
                    }
            
            # Check header
            if not isinstance(data['header'], dict):
                return {
                    'valid': False,
                    'message': "Header field must be an object",
                    'stats': {}
                }
            
            # Check terms
            if not isinstance(data['terms'], list):
                return {
                    'valid': False,
                    'message': "Terms field must be an array",
                    'stats': {}
                }
            
            # Validate each term structure
            for i, term in enumerate(data['terms']):
                if not isinstance(term, dict):
                    return {
                        'valid': False,
                        'message': f"Term {i+1} is not an object",
                        'stats': {}
                    }
                
                # Check required fields for term
                if 'id' not in term:
                    return {
                        'valid': False,
                        'message': f"Term {i+1} missing id field",
                        'stats': {}
                    }
                
                if 'name' not in term:
                    return {
                        'valid': False,
                        'message': f"Term {i+1} missing name field",
                        'stats': {}
                    }
            
            # Collect statistics
            stats = {
                'header_fields': len(data['header']),
                'total_terms': len(data['terms']),
                'has_typedefs': 'typedefs' in data,
                'typedef_count': len(data.get('typedefs', []))
            }
            
            return {
                'valid': True,
                'message': "JSON structure validation passed",
                'stats': stats
            }
            
        except Exception as e:
            return {
                'valid': False,
                'message': f"Error during validation: {e}",
                'stats': {}
            }
    
    def _ensure_customer_dir(self):
        """
        Ensure customerfile directory exists
        
        Description:
            Creates the customerfile directory if it doesn't exist,
            providing a dedicated space for user-uploaded files.
        
        Input:
            None
        
        Output:
            None (creates directory if needed)
        """
        if not os.path.exists(self.customer_file_dir):
            os.makedirs(self.customer_file_dir)
            print(f"📁 Created customerfile directory: {self.customer_file_dir}")
    
    def _cleanup_old_files(self):
        """
        Clean up old files in customerfile directory
        
        Description:
            Removes all existing files from the customerfile directory
            to ensure a clean slate for new file processing.
        
        Input:
            None
        
        Output:
            None (files are deleted from filesystem)
        """
        try:
            if os.path.exists(self.customer_file_dir):
                files = glob.glob(os.path.join(self.customer_file_dir, "*"))
                if files:
                    for file_path in files:
                        os.remove(file_path)
                        print(f"🗑️ Cleaned up old file: {file_path}")
                    print(f"✅ Cleanup completed, deleted {len(files)} old files")
                else:
                    print("📁 customerfile directory is empty, no cleanup needed")
        except Exception as e:
            print(f"❌ Error cleaning up old files: {e}")
    
    def _copy_file_to_customer_dir(self, file_path):
        """
        Copy user file to customerfile directory, keeping original filename
        
        Description:
            Copies the user's file to the dedicated customerfile directory while
            preserving the original filename and file attributes.
        
        Input:
            file_path (str): Original path of user file
            
        Output:
            str or None: Path of copied file in customerfile directory,
                        or None if copy operation failed
        """
        try:
            # Get original filename
            original_filename = os.path.basename(file_path)
            
            # Target file path (customerfile directory)
            target_path = os.path.join(self.customer_file_dir, original_filename)
            
            # Copy file
            shutil.copy2(file_path, target_path)
            
            print(f"📋 File copied: {file_path} -> {target_path}")
            return target_path
            
        except Exception as e:
            print(f"❌ Failed to copy file: {e}")
            return None
    
    def get_processing_summary(self):
        """
        Get processing summary
        
        Description:
            Returns a summary of all files processed during the session,
            including processing statistics and file details.
        
        Input:
            None
        
        Output:
            dict: Summary containing total_processed count and detailed files list
        """
        return {
            'total_processed': len(self.processed_files),
            'files': self.processed_files
        }


