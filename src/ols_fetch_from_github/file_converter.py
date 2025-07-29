import json
from typing import Dict, Any, List
from .config import Config


class FileConverter:
    """Handles conversion between different file formats (JSON to OBO)"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def convert_json_to_obo(self, json_file: str, obo_file: str) -> None:
        """
        Convert JSON file back to OBO format
        
        Args:
            json_file: Path to the JSON file to convert
            obo_file: Path where the output OBO file will be saved
        """
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        obo_lines = []
        
        # Write header
        self._write_header(data.get('header', {}), obo_lines)
        
        # Write terms
        self._write_terms(data.get('terms', []), obo_lines)
        
        # Write typedefs
        self._write_typedefs(data.get('typedefs', []), obo_lines)
        
        # Write to file
        self._write_to_file(obo_lines, obo_file)
    
    def _write_header(self, header: Dict[str, str], obo_lines: List[str]) -> None:
        """Write header section to OBO lines"""
        for key, value in header.items():
            obo_lines.append(f"{key}: {value}")
        if header:  # Only add empty line if header had content
            obo_lines.append("")  # Empty line after header
    
    def _write_terms(self, terms: List[Dict[str, Any]], obo_lines: List[str]) -> None:
        """Write terms section to OBO lines"""
        for term in terms:
            obo_lines.append("[Term]")
            self._write_fields_in_order(term, self.config.obo_field_order, obo_lines)
            obo_lines.append("")  # Empty line after each term
    
    def _write_typedefs(self, typedefs: List[Dict[str, Any]], obo_lines: List[str]) -> None:
        """Write typedefs section to OBO lines"""
        for typedef in typedefs:
            obo_lines.append("[Typedef]")
            self._write_fields_in_order(typedef, self.config.typedef_field_order, obo_lines)
            obo_lines.append("")  # Empty line after each typedef
    
    def _write_fields_in_order(self, data: Dict[str, Any], field_order: List[str], obo_lines: List[str]) -> None:
        """Write fields in specified order"""
        # First write ordered fields
        for field in field_order:
            if field in data:
                self._write_field(field, data[field], obo_lines)
        
        # Then write any remaining fields not in the order list
        for key, value in data.items():
            if key not in field_order:
                self._write_field(key, value, obo_lines)
    
    def _write_field(self, field: str, value: Any, obo_lines: List[str]) -> None:
        """Write a single field to OBO lines"""
        if isinstance(value, list):
            for v in value:
                if field == 'is_a' and isinstance(v, dict):
                    # Reconstruct "SBO:0000064 ! mathematical expression" format
                    obo_lines.append(f"{field}: {v['id']} ! {v['name']}")
                else:
                    obo_lines.append(f"{field}: {v}")
        else:
            obo_lines.append(f"{field}: {value}")
    
    def _write_to_file(self, obo_lines: List[str], obo_file: str) -> None:
        """Write OBO lines to file"""
        with open(obo_file, 'w', encoding='utf-8') as f:
            if obo_lines:
                f.write('\n'.join(obo_lines))
                # Ensure file ends with single newline

                if obo_lines[-1] != '':
                    f.write('\n')  # Add newline only if last line is not empty
            else:
                # Write empty line for empty content to ensure file has at least one newline
                f.write('\n')