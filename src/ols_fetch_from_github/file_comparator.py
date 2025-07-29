import json
from typing import Dict, Any, List, Optional


class FileComparator:
    """Handles comparison between different file versions"""
    
    def compare_json_files(self, old_json_file: str, new_json_file: str) -> Optional[Dict[str, Any]]:
        """
        Compare differences between two JSON files
        
        Args:
            old_json_file: Path to the old version JSON file
            new_json_file: Path to the new version JSON file
            
        Returns:
            Comprehensive change report containing header_changes, term_changes,
            typedef_changes, statistics, and has_changes boolean
        """
        try:
            # Read JSON files
            with open(old_json_file, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            
            with open(new_json_file, 'r', encoding='utf-8') as f:
                new_data = json.load(f)
            
            # Compare header
            header_changes = self._compare_headers(old_data.get('header', {}), new_data.get('header', {}))
            
            # Compare terms
            term_changes = self._compare_terms(old_data.get('terms', []), new_data.get('terms', []))
            
            # Compare typedefs
            typedef_changes = self._compare_typedefs(old_data.get('typedefs', []), new_data.get('typedefs', []))
            
            # Count changes
            stats = {
                'terms_added': len(term_changes['added']),
                'terms_deleted': len(term_changes['deleted']),
                'terms_updated': len(term_changes['updated']),
                'typedefs_added': len(typedef_changes['added']),
                'typedefs_deleted': len(typedef_changes['deleted']),
                'typedefs_updated': len(typedef_changes['updated']),
                'header_updated': bool(header_changes)
            }
            
            return {
                'header_changes': header_changes,
                'term_changes': term_changes,
                'typedef_changes': typedef_changes,
                'stats': stats,
                'has_changes': any([
                    header_changes,
                    term_changes['added'],
                    term_changes['deleted'], 
                    term_changes['updated'],
                    typedef_changes['added'],
                    typedef_changes['deleted'],
                    typedef_changes['updated']
                ])
            }
            
        except Exception as e:
            print(f"❌ JSON file comparison error: {e}")
            return None
    
    def _compare_headers(self, old_header: Dict[str, str], new_header: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """
        Compare changes in header section
        
        Args:
            old_header: Header fields from old version
            new_header: Header fields from new version
            
        Returns:
            Changes dictionary with field names as keys and change details as values
        """
        changes = {}
        
        # Check for added fields
        for key, value in new_header.items():
            if key not in old_header:
                changes[key] = {'action': 'added', 'new_value': value}
            elif old_header[key] != value:
                changes[key] = {'action': 'updated', 'old_value': old_header[key], 'new_value': value}
        
        # Check for deleted fields
        for key, value in old_header.items():
            if key not in new_header:
                changes[key] = {'action': 'deleted', 'old_value': value}
        
        return changes
    
    def _compare_terms(self, old_terms: List[Dict[str, Any]], new_terms: List[Dict[str, Any]]) -> Dict[str, List]:
        """
        Compare changes in terms section
        
        Args:
            old_terms: List of term dictionaries from old version
            new_terms: List of term dictionaries from new version
            
        Returns:
            Changes organized into 'added', 'deleted', and 'updated' lists
        """
        # Build mapping from ID to term
        old_terms_dict = {term.get('id'): term for term in old_terms if 'id' in term}
        new_terms_dict = {term.get('id'): term for term in new_terms if 'id' in term}
        
        added = []
        deleted = []
        updated = []
        
        # Check for added terms
        for term_id, term in new_terms_dict.items():
            if term_id not in old_terms_dict:
                added.append(term)
        
        # Check for deleted terms
        for term_id, term in old_terms_dict.items():
            if term_id not in new_terms_dict:
                deleted.append(term)
        
        # Check for updated terms
        for term_id in set(old_terms_dict.keys()) & set(new_terms_dict.keys()):
            old_term = old_terms_dict[term_id]
            new_term = new_terms_dict[term_id]
            
            if old_term != new_term:
                # Detailed comparison of field changes
                field_changes = self._compare_term_fields(old_term, new_term)
                if field_changes:
                    updated.append({
                        'id': term_id,
                        'old_term': old_term,
                        'new_term': new_term,
                        'field_changes': field_changes
                    })
        
        return {
            'added': added,
            'deleted': deleted,
            'updated': updated
        }
    
    def _compare_typedefs(self, old_typedefs: List[Dict[str, Any]], new_typedefs: List[Dict[str, Any]]) -> Dict[str, List]:
        """
        Compare changes in typedefs section
        
        Args:
            old_typedefs: List of typedef dictionaries from old version
            new_typedefs: List of typedef dictionaries from new version
            
        Returns:
            Changes organized into 'added', 'deleted', and 'updated' lists
        """
        # Build mapping from ID to typedef
        old_typedefs_dict = {typedef.get('id'): typedef for typedef in old_typedefs if 'id' in typedef}
        new_typedefs_dict = {typedef.get('id'): typedef for typedef in new_typedefs if 'id' in typedef}
        
        added = []
        deleted = []
        updated = []
        
        # Check for added typedefs
        for typedef_id, typedef in new_typedefs_dict.items():
            if typedef_id not in old_typedefs_dict:
                added.append(typedef)
        
        # Check for deleted typedefs
        for typedef_id, typedef in old_typedefs_dict.items():
            if typedef_id not in new_typedefs_dict:
                deleted.append(typedef)
        
        # Check for updated typedefs
        for typedef_id in set(old_typedefs_dict.keys()) & set(new_typedefs_dict.keys()):
            old_typedef = old_typedefs_dict[typedef_id]
            new_typedef = new_typedefs_dict[typedef_id]
            
            if old_typedef != new_typedef:
                field_changes = self._compare_term_fields(old_typedef, new_typedef)
                if field_changes:
                    updated.append({
                        'id': typedef_id,
                        'old_typedef': old_typedef,
                        'new_typedef': new_typedef,
                        'field_changes': field_changes
                    })
        
        return {
            'added': added,
            'deleted': deleted,
            'updated': updated
        }
    
    def _compare_term_fields(self, old_term: Dict[str, Any], new_term: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Compare field changes of a single term or typedef
        
        Args:
            old_term: Term/typedef dictionary from old version
            new_term: Term/typedef dictionary from new version
            
        Returns:
            Field changes with field names as keys and change details as values
        """
        changes = {}
        
        # Get all fields
        all_fields = set(old_term.keys()) | set(new_term.keys())
        
        for field in all_fields:
            old_value = old_term.get(field)
            new_value = new_term.get(field)
            
            if old_value != new_value:
                if field not in old_term:
                    changes[field] = {'action': 'added', 'new_value': new_value}
                elif field not in new_term:
                    changes[field] = {'action': 'deleted', 'old_value': old_value}
                else:
                    changes[field] = {'action': 'updated', 'old_value': old_value, 'new_value': new_value}
        
        return changes