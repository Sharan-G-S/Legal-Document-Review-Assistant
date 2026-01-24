from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import json
import difflib
from models.models import Document

class VersionManager:
    """Manage document versions and track changes"""
    
    def __init__(self, versions_folder: Path):
        self.versions_folder = Path(versions_folder)
        self.versions_folder.mkdir(parents=True, exist_ok=True)
    
    def create_version(self, document: Document, parent_id: Optional[str] = None) -> Dict:
        """
        Create a new version entry for a document
        
        Args:
            document: Document object
            parent_id: ID of the parent document (if this is a new version)
            
        Returns:
            Version metadata dictionary
        """
        # Determine version number
        version_number = 1
        if parent_id:
            versions = self.get_versions(parent_id)
            if versions:
                version_number = max(v['version_number'] for v in versions) + 1
        
        version_data = {
            'version_id': document.id,
            'document_id': parent_id or document.id,
            'version_number': version_number,
            'upload_date': document.upload_date,
            'filename': document.filename,
            'file_size': document.file_size,
            'word_count': document.word_count,
            'page_count': document.page_count,
            'is_current': True
        }
        
        # If this is a new version, calculate changes
        if parent_id and version_number > 1:
            previous_version = self.get_latest_version(parent_id)
            if previous_version:
                changes = self._calculate_changes(previous_version, document)
                version_data['changes_summary'] = changes
                
                # Mark previous version as not current
                self._update_version_status(previous_version['version_id'], is_current=False)
        
        # Save version metadata
        self._save_version_metadata(version_data)
        
        return version_data
    
    def get_versions(self, document_id: str) -> List[Dict]:
        """Get all versions of a document"""
        versions = []
        
        for version_file in self.versions_folder.glob(f"{document_id}_v*.json"):
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                    versions.append(version_data)
            except Exception as e:
                print(f"Error loading version {version_file}: {e}")
                continue
        
        # Sort by version number
        versions.sort(key=lambda x: x['version_number'])
        return versions
    
    def get_latest_version(self, document_id: str) -> Optional[Dict]:
        """Get the most recent version of a document"""
        versions = self.get_versions(document_id)
        return versions[-1] if versions else None
    
    def get_version_by_id(self, version_id: str) -> Optional[Dict]:
        """Get a specific version by its ID"""
        version_files = list(self.versions_folder.glob(f"*_v*.json"))
        
        for version_file in version_files:
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                    if version_data['version_id'] == version_id:
                        return version_data
            except Exception:
                continue
        
        return None
    
    def _calculate_changes(self, previous_version: Dict, current_document: Document) -> Dict:
        """Calculate changes between versions"""
        from services.document_processor import DocumentProcessor
        from config import Config
        
        # Load previous document data
        processor = DocumentProcessor(Config.UPLOAD_FOLDER, Config.PROCESSED_FOLDER)
        prev_doc_data = processor.load_document_data(previous_version['version_id'])
        
        changes = {
            'clauses_added': 0,
            'clauses_removed': 0,
            'clauses_modified': 0,
            'risk_delta': 0.0,
            'major_changes': []
        }
        
        # Compare clauses
        prev_clauses = prev_doc_data.get('clauses', [])
        curr_clauses = [c.to_dict() for c in current_document.clauses]
        
        prev_categories = {c['category'] for c in prev_clauses}
        curr_categories = {c['category'] for c in curr_clauses}
        
        # Count changes
        changes['clauses_added'] = len(curr_categories - prev_categories)
        changes['clauses_removed'] = len(prev_categories - curr_categories)
        
        # Count modified clauses (same category but different text)
        for prev_clause in prev_clauses:
            for curr_clause in curr_clauses:
                if prev_clause['category'] == curr_clause['category']:
                    if prev_clause['text'] != curr_clause['text']:
                        changes['clauses_modified'] += 1
                        break
        
        # Calculate risk delta
        prev_risk = prev_doc_data.get('risk_assessment', {}).get('overall_risk_score', 0)
        curr_risk = current_document.risk_assessment.overall_risk_score if current_document.risk_assessment else 0
        changes['risk_delta'] = round(curr_risk - prev_risk, 2)
        
        # Identify major changes
        if changes['clauses_added'] > 0:
            added_cats = curr_categories - prev_categories
            for cat in added_cats:
                changes['major_changes'].append(f"Added new {cat.replace('_', ' ')} clause")
        
        if changes['clauses_removed'] > 0:
            removed_cats = prev_categories - curr_categories
            for cat in removed_cats:
                changes['major_changes'].append(f"Removed {cat.replace('_', ' ')} clause")
        
        if abs(changes['risk_delta']) > 10:
            direction = "increased" if changes['risk_delta'] > 0 else "decreased"
            changes['major_changes'].append(f"Overall risk {direction} by {abs(changes['risk_delta']):.1f} points")
        
        return changes
    
    def _save_version_metadata(self, version_data: Dict):
        """Save version metadata to file"""
        doc_id = version_data['document_id']
        version_num = version_data['version_number']
        filename = self.versions_folder / f"{doc_id}_v{version_num}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, indent=2, ensure_ascii=False)
    
    def _update_version_status(self, version_id: str, is_current: bool):
        """Update the current status of a version"""
        version_files = list(self.versions_folder.glob(f"*_v*.json"))
        
        for version_file in version_files:
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                
                if version_data['version_id'] == version_id:
                    version_data['is_current'] = is_current
                    
                    with open(version_file, 'w', encoding='utf-8') as f:
                        json.dump(version_data, f, indent=2, ensure_ascii=False)
                    break
            except Exception:
                continue
    
    def compare_versions(self, version1_id: str, version2_id: str) -> Dict:
        """
        Compare two versions and return detailed differences
        
        Args:
            version1_id: First version ID
            version2_id: Second version ID
            
        Returns:
            Comparison results dictionary
        """
        from services.document_processor import DocumentProcessor
        from config import Config
        
        processor = DocumentProcessor(Config.UPLOAD_FOLDER, Config.PROCESSED_FOLDER)
        
        # Load both documents
        doc1 = processor.load_document_data(version1_id)
        doc2 = processor.load_document_data(version2_id)
        
        comparison = {
            'version1': {
                'id': version1_id,
                'filename': doc1.get('filename', ''),
                'upload_date': doc1.get('upload_date', '')
            },
            'version2': {
                'id': version2_id,
                'filename': doc2.get('filename', ''),
                'upload_date': doc2.get('upload_date', '')
            },
            'text_diff': self._generate_text_diff(doc1, doc2),
            'clause_changes': self._compare_clauses(doc1.get('clauses', []), doc2.get('clauses', [])),
            'risk_comparison': self._compare_risks(
                doc1.get('risk_assessment', {}),
                doc2.get('risk_assessment', {})
            ),
            'summary_changes': self._compare_summaries(
                doc1.get('summary', {}),
                doc2.get('summary', {})
            )
        }
        
        return comparison
    
    def _generate_text_diff(self, doc1: Dict, doc2: Dict) -> List[Dict]:
        """Generate line-by-line text differences"""
        # This is a simplified version - in production, you'd want more sophisticated diff
        text1_lines = doc1.get('raw_text', '').split('\n')[:100]  # Limit for performance
        text2_lines = doc2.get('raw_text', '').split('\n')[:100]
        
        diff = difflib.unified_diff(text1_lines, text2_lines, lineterm='')
        
        changes = []
        for line in diff:
            if line.startswith('+'):
                changes.append({'type': 'added', 'text': line[1:]})
            elif line.startswith('-'):
                changes.append({'type': 'removed', 'text': line[1:]})
        
        return changes[:50]  # Limit results
    
    def _compare_clauses(self, clauses1: List[Dict], clauses2: List[Dict]) -> Dict:
        """Compare clauses between versions"""
        cats1 = {c['category']: c for c in clauses1}
        cats2 = {c['category']: c for c in clauses2}
        
        return {
            'added': [cats2[cat] for cat in set(cats2.keys()) - set(cats1.keys())],
            'removed': [cats1[cat] for cat in set(cats1.keys()) - set(cats2.keys())],
            'modified': [
                {'category': cat, 'old': cats1[cat], 'new': cats2[cat]}
                for cat in set(cats1.keys()) & set(cats2.keys())
                if cats1[cat]['text'] != cats2[cat]['text']
            ]
        }
    
    def _compare_risks(self, risk1: Dict, risk2: Dict) -> Dict:
        """Compare risk assessments"""
        return {
            'old_score': risk1.get('overall_risk_score', 0),
            'new_score': risk2.get('overall_risk_score', 0),
            'delta': risk2.get('overall_risk_score', 0) - risk1.get('overall_risk_score', 0),
            'old_level': risk1.get('overall_risk_level', 'unknown'),
            'new_level': risk2.get('overall_risk_level', 'unknown')
        }
    
    def _compare_summaries(self, summary1: Dict, summary2: Dict) -> Dict:
        """Compare document summaries"""
        return {
            'parties_changed': summary1.get('parties', []) != summary2.get('parties', []),
            'purpose_changed': summary1.get('purpose', '') != summary2.get('purpose', ''),
            'type_changed': summary1.get('document_type', '') != summary2.get('document_type', '')
        }
