from typing import List, Dict, Tuple
import difflib
from models.models import Clause

class DiffAnalyzer:
    """AI-powered difference analysis between document versions"""
    
    def __init__(self):
        pass
    
    def analyze_text_changes(self, text1: str, text2: str) -> Dict:
        """
        Analyze changes between two text versions
        
        Args:
            text1: Original text
            text2: Modified text
            
        Returns:
            Analysis of changes
        """
        # Calculate similarity ratio
        similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
        
        # Get detailed diff
        diff = list(difflib.unified_diff(
            text1.split('\n'),
            text2.split('\n'),
            lineterm=''
        ))
        
        # Count changes
        additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
        
        return {
            'similarity_percentage': round(similarity * 100, 2),
            'lines_added': additions,
            'lines_deleted': deletions,
            'total_changes': additions + deletions,
            'change_type': self._classify_change_magnitude(similarity)
        }
    
    def _classify_change_magnitude(self, similarity: float) -> str:
        """Classify the magnitude of changes"""
        if similarity >= 0.95:
            return 'minor'
        elif similarity >= 0.80:
            return 'moderate'
        elif similarity >= 0.50:
            return 'major'
        else:
            return 'substantial'
    
    def analyze_clause_changes(self, old_clauses: List[Clause], new_clauses: List[Clause]) -> Dict:
        """
        Analyze changes in clauses between versions
        
        Args:
            old_clauses: Clauses from previous version
            new_clauses: Clauses from current version
            
        Returns:
            Detailed clause change analysis
        """
        old_by_category = {c.category: c for c in old_clauses}
        new_by_category = {c.category: c for c in new_clauses}
        
        old_categories = set(old_by_category.keys())
        new_categories = set(new_by_category.keys())
        
        analysis = {
            'added_clauses': [],
            'removed_clauses': [],
            'modified_clauses': [],
            'unchanged_clauses': [],
            'risk_changes': []
        }
        
        # Find added clauses
        for category in new_categories - old_categories:
            clause = new_by_category[category]
            analysis['added_clauses'].append({
                'category': category,
                'text': clause.text[:200] + '...' if len(clause.text) > 200 else clause.text,
                'risk_level': clause.risk_level,
                'impact': 'New clause added - review required'
            })
        
        # Find removed clauses
        for category in old_categories - new_categories:
            clause = old_by_category[category]
            analysis['removed_clauses'].append({
                'category': category,
                'text': clause.text[:200] + '...' if len(clause.text) > 200 else clause.text,
                'risk_level': clause.risk_level,
                'impact': 'Clause removed - verify intentional'
            })
        
        # Find modified clauses
        for category in old_categories & new_categories:
            old_clause = old_by_category[category]
            new_clause = new_by_category[category]
            
            if old_clause.text != new_clause.text:
                # Calculate text similarity
                similarity = difflib.SequenceMatcher(
                    None,
                    old_clause.text,
                    new_clause.text
                ).ratio()
                
                analysis['modified_clauses'].append({
                    'category': category,
                    'old_text': old_clause.text[:150] + '...',
                    'new_text': new_clause.text[:150] + '...',
                    'similarity': round(similarity * 100, 2),
                    'old_risk': old_clause.risk_level,
                    'new_risk': new_clause.risk_level,
                    'risk_changed': old_clause.risk_level != new_clause.risk_level
                })
                
                # Track risk changes
                if old_clause.risk_level != new_clause.risk_level:
                    analysis['risk_changes'].append({
                        'category': category,
                        'old_risk': old_clause.risk_level,
                        'new_risk': new_clause.risk_level,
                        'direction': 'increased' if self._risk_level_value(new_clause.risk_level) > self._risk_level_value(old_clause.risk_level) else 'decreased'
                    })
            else:
                analysis['unchanged_clauses'].append(category)
        
        return analysis
    
    def _risk_level_value(self, risk_level: str) -> int:
        """Convert risk level to numeric value for comparison"""
        levels = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        return levels.get(risk_level.lower(), 0)
    
    def generate_change_summary(self, analysis: Dict) -> List[str]:
        """
        Generate human-readable summary of changes
        
        Args:
            analysis: Analysis results from analyze_clause_changes
            
        Returns:
            List of summary statements
        """
        summary = []
        
        # Added clauses
        if analysis['added_clauses']:
            count = len(analysis['added_clauses'])
            summary.append(f"✅ {count} new clause{'s' if count > 1 else ''} added")
            for clause in analysis['added_clauses'][:3]:  # Show top 3
                summary.append(f"  • {clause['category'].replace('_', ' ').title()}")
        
        # Removed clauses
        if analysis['removed_clauses']:
            count = len(analysis['removed_clauses'])
            summary.append(f"❌ {count} clause{'s' if count > 1 else ''} removed")
            for clause in analysis['removed_clauses'][:3]:
                summary.append(f"  • {clause['category'].replace('_', ' ').title()}")
        
        # Modified clauses
        if analysis['modified_clauses']:
            count = len(analysis['modified_clauses'])
            summary.append(f"📝 {count} clause{'s' if count > 1 else ''} modified")
        
        # Risk changes
        if analysis['risk_changes']:
            for change in analysis['risk_changes']:
                direction_icon = '⬆️' if change['direction'] == 'increased' else '⬇️'
                summary.append(
                    f"{direction_icon} {change['category'].replace('_', ' ').title()}: "
                    f"{change['old_risk']} → {change['new_risk']}"
                )
        
        # Unchanged
        if analysis['unchanged_clauses']:
            count = len(analysis['unchanged_clauses'])
            summary.append(f"✓ {count} clause{'s' if count > 1 else ''} unchanged")
        
        return summary
    
    def highlight_differences(self, text1: str, text2: str) -> Tuple[str, str]:
        """
        Generate HTML-highlighted versions of texts showing differences
        
        Args:
            text1: Original text
            text2: Modified text
            
        Returns:
            Tuple of (highlighted_text1, highlighted_text2)
        """
        # Use difflib to get opcodes
        matcher = difflib.SequenceMatcher(None, text1, text2)
        
        highlighted1 = []
        highlighted2 = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                highlighted1.append(text1[i1:i2])
                highlighted2.append(text2[j1:j2])
            elif tag == 'delete':
                highlighted1.append(f'<span class="diff-removed">{text1[i1:i2]}</span>')
            elif tag == 'insert':
                highlighted2.append(f'<span class="diff-added">{text2[j1:j2]}</span>')
            elif tag == 'replace':
                highlighted1.append(f'<span class="diff-modified">{text1[i1:i2]}</span>')
                highlighted2.append(f'<span class="diff-modified">{text2[j1:j2]}</span>')
        
        return ''.join(highlighted1), ''.join(highlighted2)
