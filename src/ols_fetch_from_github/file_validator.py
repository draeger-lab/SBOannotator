import os
import subprocess
from typing import Tuple, Optional
from .utils import ValidationResult


class FileValidator:
    """Handles file validation operations"""
    
    def validate_roundtrip_conversion(self, original_file: str, reverted_file: str) -> bool:
        """
        Verify whether roundtrip conversion is successful (ignore format differences)
        
        Args:
            original_file: Path to the original OBO file
            reverted_file: Path to the OBO file converted back from JSON
            
        Returns:
            True if semantic content is preserved, False if conversion failed
        """
        print("🔄 Verifying roundtrip conversion...")
        
        # Check if files exist
        if not os.path.exists(original_file):
            print(f"❌ Original file does not exist: {original_file}")
            return False
        
        if not os.path.exists(reverted_file):
            print(f"❌ Converted file does not exist: {reverted_file}")
            return False
        
        # Direct comparison (complete identity is the best case)
        stdout, stderr, code = self._run_git_diff(original_file, reverted_file)
        if stderr:
            print(f"❌ Git diff error: {stderr}")
            return False
        
        if not stdout or not stdout.strip():
            print("✅ Files are completely identical! Roundtrip conversion successful")
            return True
        
        # Comparison ignoring all whitespace differences
        print("📋 Format differences detected, performing whitespace-ignoring comparison...")
        stdout, stderr, code = self._run_git_diff(original_file, reverted_file, 
                                               ['--ignore-all-space', '--ignore-blank-lines'])
        
        if stderr:
            print(f"❌ Git diff error: {stderr}")
            return False
        
        if not stdout or not stdout.strip():
            print("✅ Files are identical after ignoring format differences! Roundtrip conversion successful")
            return True
        
        # Semantic content comparison (most lenient comparison)
        print("📋 Still differences found, performing semantic content comparison...")
        semantic_match = self.validate_semantic_content(original_file, reverted_file)
        
        if semantic_match:
            print("✅ Semantic content is completely consistent! Roundtrip conversion successful (only format differences)")
            return True
        else:
            print("❌ Semantic content is inconsistent! Roundtrip conversion failed")
            return False
    
    def validate_semantic_content(self, file1: str, file2: str) -> bool:
        """
        Verify whether semantic content of two OBO files is consistent (ignore format)
        
        Args:
            file1: Path to the first OBO file
            file2: Path to the second OBO file
            
        Returns:
            True if semantic content is identical, False if differences found
        """
        try:
            content1 = self._extract_semantic_content(file1)
            content2 = self._extract_semantic_content(file2)
            
            # Compare semantic content
            missing_in_file2 = content1 - content2
            extra_in_file2 = content2 - content1
            
            if missing_in_file2:
                print(f"📋 File2 missing content (first 5): {list(missing_in_file2)[:5]}")
            
            if extra_in_file2:
                print(f"📋 File2 extra content (first 5): {list(extra_in_file2)[:5]}")
            
            return len(missing_in_file2) == 0 and len(extra_in_file2) == 0
            
        except Exception as e:
            print(f"❌ Semantic comparison error: {e}")
            return False
    
    def validate_json_structure(self, data: dict) -> ValidationResult:
        """
        Validate JSON structure conforms to SBO format
        
        Args:
            data: Parsed JSON data to validate
            
        Returns:
            ValidationResult object containing validation status and details
        """
        try:
            # Check required top-level fields
            required_fields = ['header', 'terms']
            for field in required_fields:
                if field not in data:
                    return ValidationResult(
                        success=False,
                        message=f"Missing required field: {field}"
                    )
            
            # Check header
            if not isinstance(data['header'], dict):
                return ValidationResult(
                    success=False,
                    message="Header field must be an object"
                )
            
            # Check terms
            if not isinstance(data['terms'], list):
                return ValidationResult(
                    success=False,
                    message="Terms field must be an array"
                )
            
            # Validate each term structure
            for i, term in enumerate(data['terms']):
                if not isinstance(term, dict):
                    return ValidationResult(
                        success=False,
                        message=f"Term {i+1} is not an object"
                    )
                
                # Check required fields for term
                if 'id' not in term:
                    return ValidationResult(
                        success=False,
                        message=f"Term {i+1} missing id field"
                    )
                
                if 'name' not in term:
                    return ValidationResult(
                        success=False,
                        message=f"Term {i+1} missing name field"
                    )
            
            # Collect statistics
            stats = {
                'header_fields': len(data['header']),
                'total_terms': len(data['terms']),
                'has_typedefs': 'typedefs' in data,
                'typedef_count': len(data.get('typedefs', []))
            }
            
            return ValidationResult(
                success=True,
                message="JSON structure validation passed",
                data=stats
            )
            
        except Exception as e:
            return ValidationResult(
                success=False,
                message=f"Error during validation: {e}"
            )
    
    def _run_git_diff(self, file1: str, file2: str, options: Optional[list] = None) -> Tuple[str, str, int]:
        """
        Run git diff and return results
        
        Args:
            file1: Path to the first file for comparison
            file2: Path to the second file for comparison
            options: Additional git diff options
            
        Returns:
            Tuple of (stdout, stderr, returncode) from git diff command
        """
        cmd = ['git', 'diff', '--no-index']
        if options:
            cmd.extend(options)
        cmd.extend([file1, file2])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return None, str(e), 1
    
    def _extract_semantic_content(self, file_path: str) -> set:
        """Extract semantic content from OBO file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract all meaningful lines, ignore empty lines and format
        meaningful_lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('!'):  # Ignore comment lines
                # Normalize whitespace characters
                line = ' '.join(line.split())
                meaningful_lines.append(line)
        
        return set(meaningful_lines)  # Use set to ignore order