import json
import os
from datetime import datetime


class ChangeLogger:
    """
    Change Logger - Records SBO file change history
    
    Description:
        Manages logging and display of changes between SBO ontology file versions,
        providing detailed tracking of modifications, additions, and deletions.
    """
    
    def __init__(self, log_dir=None):
        """
        Initialize Change Logger
        
        Description:
            Sets up the change logger with a specified or default log directory,
            ensuring the directory structure exists for storing change logs.
        
        Input:
            log_dir (str, optional): Custom log directory path, defaults to SBO_OBO_Files/logs
        
        Output:
            None (constructor)
        """
        if log_dir is None:
            # Use SBO_OBO_Files/logs under the current script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            sbo_obo_files_dir = os.path.join(script_dir, 'SBO_OBO_Files')
            self.log_dir = os.path.join(sbo_obo_files_dir, "logs")
        else:
            self.log_dir = log_dir
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        """
        Ensure log directory exists
        
        Description:
            Creates the log directory if it doesn't exist, ensuring proper
            directory structure for storing change logs.
        
        Input:
            None
        
        Output:
            None (creates directory if needed)
        """
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            print(f"📁 Creating log directory: {self.log_dir}")
    
    def log_changes(self, changes, old_version_info=None, new_version_info=None):
        """
        Log change history
        
        Description:
            Creates a detailed JSON log file documenting all changes between versions,
            including statistics, version information, and formatted change details.
        
        Input:
            changes (dict): Change information dictionary (from compare_json_files)
            old_version_info (dict, optional): Metadata about the old version
            new_version_info (dict, optional): Metadata about the new version
        
        Output:
            str or None: Path to created log file, or None if logging failed
        """
        if not changes or not changes.get('has_changes'):
            print("📋 No changes to log")
            return None
        
        # Generate log filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"sbo_changes_{timestamp}.json"
        log_filepath = os.path.join(self.log_dir, log_filename)
        
        # Build detailed log
        detailed_log = {
            'timestamp': datetime.now().isoformat(),
            'old_version': old_version_info,
            'new_version': new_version_info,
            'summary': changes['stats'],
            'changes': {
                'header_changes': changes['header_changes'],
                'term_changes': self._format_term_changes(changes['term_changes']),
                'typedef_changes': self._format_typedef_changes(changes['typedef_changes'])
            }
        }
        
        # Save detailed log
        try:
            with open(log_filepath, 'w', encoding='utf-8') as f:
                json.dump(detailed_log, f, indent=2, ensure_ascii=False)
            
            print(f"📝 Change log saved: {log_filepath}")
            return log_filepath
            
        except Exception as e:
            print(f"❌ Failed to save change log: {e}")
            return None
    
    def _format_term_changes(self, term_changes):
        """
        Format term change information
        
        Description:
            Converts raw term change data into a structured format suitable for logging,
            extracting key information like IDs, labels, descriptions, and parent relationships.
        
        Input:
            term_changes (dict): Raw term changes with 'added', 'deleted', and 'updated' lists
        
        Output:
            dict: Formatted term changes with standardized structure for each change type
        """
        formatted = {
            'added': [],
            'deleted': [],
            'updated': []
        }
        
        # Added terms
        for term in term_changes['added']:
            formatted['added'].append({
                'obo_id': term.get('id', 'Unknown'),
                'label': term.get('name', 'Unknown'),
                'description': term.get('comment', 'No description'),
                'parents': self._get_parent_info(term),
                'change_type': 'add'
            })
        
        # Deleted terms
        for term in term_changes['deleted']:
            formatted['deleted'].append({
                'obo_id': term.get('id', 'Unknown'),
                'label': term.get('name', 'Unknown'),
                'description': term.get('comment', 'No description'),
                'parents': self._get_parent_info(term),
                'change_type': 'delete'
            })
        
        # Updated terms
        for term_update in term_changes['updated']:
            old_term = term_update['old_term']
            new_term = term_update['new_term']
            field_changes = term_update['field_changes']
            
            formatted['updated'].append({
                'obo_id': term_update['id'],
                'label': new_term.get('name', old_term.get('name', 'Unknown')),
                'description': new_term.get('comment', old_term.get('comment', 'No description')),
                'parents': self._get_parent_info(new_term),
                'change_type': 'update',
                'field_changes': field_changes,
                'old_values': {
                    'label': old_term.get('name', 'Unknown'),
                    'description': old_term.get('comment', 'No description'),
                    'parents': self._get_parent_info(old_term)
                }
            })
        
        return formatted
    
    def _format_typedef_changes(self, typedef_changes):
        """
        Format typedef change information
        
        Description:
            Converts raw typedef change data into a structured format suitable for logging,
            extracting key information like IDs, labels, and descriptions.
        
        Input:
            typedef_changes (dict): Raw typedef changes with 'added', 'deleted', and 'updated' lists
        
        Output:
            dict: Formatted typedef changes with standardized structure for each change type
        """
        formatted = {
            'added': [],
            'deleted': [],
            'updated': []
        }
        
        # Added typedefs
        for typedef in typedef_changes['added']:
            formatted['added'].append({
                'obo_id': typedef.get('id', 'Unknown'),
                'label': typedef.get('name', 'Unknown'),
                'description': typedef.get('comment', 'No description'),
                'change_type': 'add'
            })
        
        # Deleted typedefs
        for typedef in typedef_changes['deleted']:
            formatted['deleted'].append({
                'obo_id': typedef.get('id', 'Unknown'),
                'label': typedef.get('name', 'Unknown'),
                'description': typedef.get('comment', 'No description'),
                'change_type': 'delete'
            })
        
        # Updated typedefs
        for typedef_update in typedef_changes['updated']:
            old_typedef = typedef_update['old_typedef']
            new_typedef = typedef_update['new_typedef']
            field_changes = typedef_update['field_changes']
            
            formatted['updated'].append({
                'obo_id': typedef_update['id'],
                'label': new_typedef.get('name', old_typedef.get('name', 'Unknown')),
                'description': new_typedef.get('comment', old_typedef.get('comment', 'No description')),
                'change_type': 'update',
                'field_changes': field_changes,
                'old_values': {
                    'label': old_typedef.get('name', 'Unknown'),
                    'description': old_typedef.get('comment', 'No description')
                }
            })
        
        return formatted
    
    def _get_parent_info(self, term):
        """
        Get parent information for a term
        
        Description:
            Extracts and standardizes parent relationship information from a term's 'is_a' field,
            handling various data formats (dict, list, string) consistently.
        
        Input:
            term (dict): Term dictionary containing 'is_a' field
        
        Output:
            list: List of parent dictionaries with 'parent_id' and 'parent_label' keys
        """
        is_a = term.get('is_a', [])
        parents = []
        
        if isinstance(is_a, list):
            for parent in is_a:
                if isinstance(parent, dict):
                    parents.append({
                        'parent_id': parent.get('id', 'Unknown'),
                        'parent_label': parent.get('name', 'Unknown')
                    })
                else:
                    # Simple string format
                    parents.append({
                        'parent_id': str(parent),
                        'parent_label': 'Unknown'
                    })
        elif isinstance(is_a, dict):
            parents.append({
                'parent_id': is_a.get('id', 'Unknown'),
                'parent_label': is_a.get('name', 'Unknown')
            })
        elif isinstance(is_a, str):
            parents.append({
                'parent_id': is_a,
                'parent_label': 'Unknown'
            })
        
        return parents
    
    def display_change_summary(self, changes):
        """
        Display change summary in CLI
        
        Description:
            Presents a concise overview of changes to the user, showing statistics
            for terms, typedefs, and header modifications in a formatted display.
        
        Input:
            changes (dict): Change information dictionary with statistics
        
        Output:
            None (prints summary to console)
        """
        if not changes or not changes.get('has_changes'):
            print("✅ No changes found")
            return
        
        stats = changes['stats']
        
        print("\n" + "="*60)
        print("📊 Change Summary")
        print("="*60)
        
        # Terms change statistics
        if any([stats['terms_added'], stats['terms_deleted'], stats['terms_updated']]):
            print(f"📋 Terms changes:")
            if stats['terms_added'] > 0:
                print(f"  ➕ Added: {stats['terms_added']}")
            if stats['terms_deleted'] > 0:
                print(f"  ➖ Deleted: {stats['terms_deleted']}")
            if stats['terms_updated'] > 0:
                print(f"  🔄 Updated: {stats['terms_updated']}")
        
        # Typedefs change statistics
        if any([stats['typedefs_added'], stats['typedefs_deleted'], stats['typedefs_updated']]):
            print(f"🏷️  Typedefs changes:")
            if stats['typedefs_added'] > 0:
                print(f"  ➕ Added: {stats['typedefs_added']}")
            if stats['typedefs_deleted'] > 0:
                print(f"  ➖ Deleted: {stats['typedefs_deleted']}")
            if stats['typedefs_updated'] > 0:
                print(f"  🔄 Updated: {stats['typedefs_updated']}")
        
        # Header changes
        if stats['header_updated']:
            print(f"📄 Header: Updated")
        
        # Total
        total_changes = (stats['terms_added'] + stats['terms_deleted'] + stats['terms_updated'] +
                        stats['typedefs_added'] + stats['typedefs_deleted'] + stats['typedefs_updated'])
        
        print(f"\n📈 Total changes: {total_changes} items")
        print("="*60)
    
    def display_detailed_changes(self, changes, limit=5):
        """
        Display detailed change information (limited display count)
        
        Description:
            Shows specific details about individual changes, including term/typedef names,
            IDs, and field-level modifications, with a configurable display limit.
        
        Input:
            changes (dict): Change information dictionary with detailed change data
            limit (int, optional): Maximum number of changes to display for each type (default: 5)
        
        Output:
            None (prints detailed information to console)
        """
        if not changes or not changes.get('has_changes'):
            return
        
        term_changes = changes['term_changes']
        
        # Display added terms (first few)
        if term_changes['added']:
            print(f"\n➕ Added Terms (showing first {min(len(term_changes['added']), limit)}):")
            for i, term in enumerate(term_changes['added'][:limit]):
                print(f"  {i+1}. {term.get('id', 'Unknown')} - {term.get('name', 'Unknown')}")
        
        # Display deleted terms (first few)
        if term_changes['deleted']:
            print(f"\n➖ Deleted Terms (showing first {min(len(term_changes['deleted']), limit)}):")
            for i, term in enumerate(term_changes['deleted'][:limit]):
                print(f"  {i+1}. {term.get('id', 'Unknown')} - {term.get('name', 'Unknown')}")
        
        # Display updated terms (first few)
        if term_changes['updated']:
            print(f"\n🔄 Updated Terms (showing first {min(len(term_changes['updated']), limit)}):")
            for i, term_update in enumerate(term_changes['updated'][:limit]):
                print(f"  {i+1}. {term_update['id']} - {term_update['new_term'].get('name', 'Unknown')}")
                # Display specific changed fields
                for field, change in term_update['field_changes'].items():
                    action = change['action']
                    if action == 'updated':
                        print(f"      📝 {field}: Updated")
                    elif action == 'added':
                        print(f"      ➕ {field}: Added")
                    elif action == 'deleted':
                        print(f"      ➖ {field}: Deleted")