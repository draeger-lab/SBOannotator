import json
import re
from typing import Dict, Any, List
from .config import Config


class OBOFileParser:
    """Handles parsing of OBO (Open Biomedical Ontologies) files"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def parse_obo_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse OBO file and convert to JSON structure
        
        Args:
            file_path: Path to the OBO file to parse
            
        Returns:
            Structured dictionary containing 'header', 'terms', and optionally 'typedefs'
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into sections by [Term] and [Typedef]
        sections = re.split(r'\[(?:Term|Typedef)\]', content)
        header_part = sections[0].strip()
        
        # Find all section markers
        section_markers = re.findall(r'\[(?:Term|Typedef)\]', content)
        
        # Parse header
        header = self._parse_header(header_part)
        
        # Parse terms and typedefs
        terms = []
        typedefs = []
        
        for i, section_content in enumerate(sections[1:], 0):
            if i >= len(section_markers):
                break
                
            section_type = section_markers[i]
            parsed_section = self._parse_section(section_content)
            
            if parsed_section:  # Only add non-empty sections
                if section_type == '[Term]':
                    terms.append(parsed_section)
                elif section_type == '[Typedef]':
                    typedefs.append(parsed_section)
        
        result = {
            'header': header,
            'terms': terms
        }
        
        if typedefs:
            result['typedefs'] = typedefs
        
        return result
    
    def _parse_header(self, header_part: str) -> Dict[str, str]:
        """Parse header section of OBO file"""
        header = {}
        for line in header_part.split('\n'):
            line = line.rstrip()
            if line.strip() and ':' in line:
                key, value = line.split(':', 1)
                header[key.strip()] = value.lstrip()
        return header
    
    def _parse_section(self, section_content: str) -> Dict[str, Any]:
        """Parse a term or typedef section"""
        lines = section_content.split('\n')
        section_lines = []
        
        # Split content at next section marker to avoid mixing sections
        for line in lines:
            line = line.rstrip('\n')
            if line.strip().startswith('[') and (line.strip() == '[Term]' or line.strip() == '[Typedef]'):
                break
            section_lines.append(line)
        
        parsed_section = {}
        
        # Parse the section
        for line in section_lines:
            line = line.rstrip('\n')
            if line.strip() and ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.lstrip()
                
                # Handle special cases
                if key == 'is_a':
                    self._handle_is_a_field(parsed_section, key, value)
                else:
                    self._handle_regular_field(parsed_section, key, value)
        
        return parsed_section
    
    def _handle_is_a_field(self, parsed_section: Dict[str, Any], key: str, value: str) -> None:
        """Handle is_a field parsing"""
        # Extract ID and name from "SBO:0000064 ! mathematical expression"
        match = re.match(r'(SBO:\d+)\s*!\s*(.*)', value)
        if match:
            if key not in parsed_section:
                parsed_section[key] = []
            parsed_section[key].append({
                'id': match.group(1),
                'name': match.group(2)
            })
        else:
            if key not in parsed_section:
                parsed_section[key] = []
            parsed_section[key].append(value)
    
    
    def _handle_regular_field(self, parsed_section: Dict[str, Any], key: str, value: str) -> None:
        """Handle regular field parsing"""
        if key in parsed_section:
            # Convert to list if multiple values
            if not isinstance(parsed_section[key], list):
                parsed_section[key] = [parsed_section[key]]
            parsed_section[key].append(value)
        else:
            parsed_section[key] = value