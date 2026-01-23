import re
from typing import List
from models.models import Clause
from config import Config
import spacy

class ClauseDetector:
    """Detect and classify legal clauses in documents"""
    
    def __init__(self):
        self.clause_patterns = Config.CLAUSE_CATEGORIES
        self.nlp = None
        self._load_nlp_model()
    
    def _load_nlp_model(self):
        """Load spaCy NLP model"""
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except OSError:
            print("⚠️  spaCy model not found. Installing...")
            import subprocess
            subprocess.run(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
            self.nlp = spacy.load('en_core_web_sm')
    
    def detect_clauses(self, text: str) -> List[Clause]:
        """
        Detect and classify clauses in legal text
        
        Args:
            text: Document text
            
        Returns:
            List of detected Clause objects
        """
        clauses = []
        
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Split into sentences
        sentences = list(doc.sents)
        
        for sent_idx, sent in enumerate(sentences):
            sent_text = sent.text.strip()
            
            # Skip very short sentences
            if len(sent_text.split()) < 5:
                continue
            
            # Detect clause category using pattern matching
            category, confidence = self._classify_sentence(sent_text)
            
            if category:
                clause = Clause(
                    text=sent_text,
                    category=category,
                    start_position=sent.start_char,
                    end_position=sent.end_char,
                    confidence=confidence
                )
                
                # Analyze clause for risks
                clause.risk_level, clause.risk_score = self._assess_clause_risk(sent_text, category)
                
                # Add issues and recommendations
                clause.issues = self._identify_issues(sent_text, category)
                clause.recommendations = self._generate_recommendations(clause.issues, category)
                
                clauses.append(clause)
        
        return clauses
    
    def _classify_sentence(self, sentence: str) -> tuple:
        """
        Classify a sentence into a clause category
        
        Returns:
            Tuple of (category, confidence)
        """
        sentence_lower = sentence.lower()
        
        # Check each category
        best_category = None
        best_score = 0
        
        for category, keywords in self.clause_patterns.items():
            score = 0
            for keyword in keywords:
                if keyword in sentence_lower:
                    # Weight by keyword length (longer = more specific)
                    score += len(keyword.split())
            
            if score > best_score:
                best_score = score
                best_category = category
        
        # Calculate confidence based on score
        confidence = min(0.5 + (best_score * 0.1), 1.0) if best_score > 0 else 0.0
        
        return best_category, confidence
    
    def _assess_clause_risk(self, text: str, category: str) -> tuple:
        """
        Assess risk level of a clause
        
        Returns:
            Tuple of (risk_level, risk_score)
        """
        risk_score = 0.0
        text_lower = text.lower()
        
        # High-risk indicators
        high_risk_terms = [
            'unlimited', 'perpetual', 'irrevocable', 'sole discretion',
            'without limitation', 'in no event', 'waive', 'forfeit',
            'exclusive', 'non-refundable', 'no liability'
        ]
        
        # Medium-risk indicators
        medium_risk_terms = [
            'may', 'at our discretion', 'reserve the right',
            'subject to', 'notwithstanding', 'except as'
        ]
        
        # Count risk indicators
        for term in high_risk_terms:
            if term in text_lower:
                risk_score += 25
        
        for term in medium_risk_terms:
            if term in text_lower:
                risk_score += 10
        
        # Category-specific risk adjustments
        if category == 'liability':
            risk_score += 15
        elif category == 'termination':
            risk_score += 10
        elif category == 'intellectual_property':
            risk_score += 10
        
        # Determine risk level
        risk_score = min(risk_score, 100)
        
        if risk_score < 30:
            risk_level = 'low'
        elif risk_score < 60:
            risk_level = 'medium'
        elif risk_score < 85:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        
        return risk_level, risk_score
    
    def _identify_issues(self, text: str, category: str) -> List[str]:
        """Identify potential issues in a clause"""
        issues = []
        text_lower = text.lower()
        
        # Check for vague language
        vague_terms = ['reasonable', 'appropriate', 'sufficient', 'adequate', 'material']
        if any(term in text_lower for term in vague_terms):
            issues.append("Contains vague or ambiguous language")
        
        # Check for one-sided terms
        one_sided = ['sole discretion', 'at our option', 'we may', 'without limitation']
        if any(term in text_lower for term in one_sided):
            issues.append("Contains potentially one-sided terms")
        
        # Check for unlimited obligations
        if 'unlimited' in text_lower or 'without limit' in text_lower:
            issues.append("Contains unlimited obligations or liability")
        
        # Check for perpetual terms
        if 'perpetual' in text_lower or 'indefinite' in text_lower:
            issues.append("Contains perpetual or indefinite terms")
        
        # Category-specific checks
        if category == 'liability' and 'no liability' in text_lower:
            issues.append("Complete liability waiver detected")
        
        if category == 'termination' and 'without notice' in text_lower:
            issues.append("Allows termination without notice")
        
        return issues
    
    def _generate_recommendations(self, issues: List[str], category: str) -> List[str]:
        """Generate recommendations based on identified issues"""
        recommendations = []
        
        for issue in issues:
            if 'vague' in issue.lower():
                recommendations.append("Request clarification or specific definitions for ambiguous terms")
            
            if 'one-sided' in issue.lower():
                recommendations.append("Negotiate for mutual obligations or reciprocal terms")
            
            if 'unlimited' in issue.lower():
                recommendations.append("Propose reasonable caps or limitations")
            
            if 'perpetual' in issue.lower():
                recommendations.append("Suggest a defined term with renewal options")
            
            if 'liability waiver' in issue.lower():
                recommendations.append("Seek to limit the scope of liability waiver")
            
            if 'without notice' in issue.lower():
                recommendations.append("Request minimum notice period for termination")
        
        # Category-specific recommendations
        if category == 'confidentiality' and not recommendations:
            recommendations.append("Ensure mutual confidentiality obligations")
        
        if category == 'intellectual_property' and not recommendations:
            recommendations.append("Clarify ownership and usage rights")
        
        return recommendations
