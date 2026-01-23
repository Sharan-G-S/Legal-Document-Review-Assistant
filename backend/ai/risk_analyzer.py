from typing import List, Dict
from models.models import Clause, RiskAssessment
from config import Config

class RiskAnalyzer:
    """Analyze overall document risk and identify issues"""
    
    def __init__(self):
        self.risk_weights = Config.RISK_WEIGHTS
        self.essential_clauses = [
            'confidentiality',
            'liability',
            'termination',
            'payment',
            'dispute_resolution',
            'governing_law'
        ]
    
    def analyze_risks(self, text: str, clauses: List[Clause]) -> RiskAssessment:
        """
        Perform comprehensive risk assessment
        
        Args:
            text: Full document text
            clauses: List of detected clauses
            
        Returns:
            RiskAssessment object
        """
        assessment = RiskAssessment()
        
        # Calculate individual risk factors
        unfavorable_score = self._assess_unfavorable_terms(clauses)
        missing_score = self._assess_missing_clauses(clauses)
        ambiguity_score = self._assess_ambiguity(text, clauses)
        unusual_score = self._assess_unusual_obligations(clauses)
        
        # Calculate weighted overall score
        overall_score = (
            unfavorable_score * self.risk_weights['unfavorable_terms'] +
            missing_score * self.risk_weights['missing_clauses'] +
            ambiguity_score * self.risk_weights['ambiguous_language'] +
            unusual_score * self.risk_weights['unusual_obligations']
        )
        
        assessment.overall_risk_score = round(overall_score, 2)
        assessment.overall_risk_level = self._get_risk_level(overall_score)
        
        # Populate detailed findings
        assessment.unfavorable_terms = self._get_unfavorable_terms(clauses)
        assessment.missing_clauses = self._get_missing_clauses(clauses)
        assessment.risk_factors = self._compile_risk_factors(
            unfavorable_score, missing_score, ambiguity_score, unusual_score
        )
        assessment.recommendations = self._generate_recommendations(assessment)
        
        return assessment
    
    def _assess_unfavorable_terms(self, clauses: List[Clause]) -> float:
        """Assess risk from unfavorable terms"""
        if not clauses:
            return 0.0
        
        high_risk_count = sum(1 for c in clauses if c.risk_level in ['high', 'critical'])
        total_clauses = len(clauses)
        
        return (high_risk_count / total_clauses) * 100
    
    def _assess_missing_clauses(self, clauses: List[Clause]) -> float:
        """Assess risk from missing essential clauses"""
        detected_categories = set(c.category for c in clauses)
        missing = set(self.essential_clauses) - detected_categories
        
        if not self.essential_clauses:
            return 0.0
        
        return (len(missing) / len(self.essential_clauses)) * 100
    
    def _assess_ambiguity(self, text: str, clauses: List[Clause]) -> float:
        """Assess risk from ambiguous language"""
        ambiguous_count = sum(1 for c in clauses if any('vague' in issue.lower() or 'ambiguous' in issue.lower() for issue in c.issues))
        
        if not clauses:
            return 0.0
        
        return (ambiguous_count / len(clauses)) * 100
    
    def _assess_unusual_obligations(self, clauses: List[Clause]) -> float:
        """Assess risk from unusual obligations"""
        unusual_count = sum(1 for c in clauses if any('unlimited' in issue.lower() or 'perpetual' in issue.lower() for issue in c.issues))
        
        if not clauses:
            return 0.0
        
        return (unusual_count / len(clauses)) * 100
    
    def _get_risk_level(self, score: float) -> str:
        """Convert risk score to risk level"""
        for level, (min_score, max_score) in Config.RISK_LEVELS.items():
            if min_score <= score < max_score:
                return level
        return 'critical'
    
    def _get_unfavorable_terms(self, clauses: List[Clause]) -> List[Dict]:
        """Get list of unfavorable terms"""
        unfavorable = []
        
        for clause in clauses:
            if clause.risk_level in ['high', 'critical']:
                unfavorable.append({
                    'clause_id': clause.id,
                    'category': clause.category,
                    'text': clause.text[:200] + '...' if len(clause.text) > 200 else clause.text,
                    'risk_level': clause.risk_level,
                    'issues': clause.issues
                })
        
        return unfavorable
    
    def _get_missing_clauses(self, clauses: List[Clause]) -> List[str]:
        """Get list of missing essential clauses"""
        detected_categories = set(c.category for c in clauses)
        missing = set(self.essential_clauses) - detected_categories
        
        # Convert to readable names
        readable_names = {
            'confidentiality': 'Confidentiality/Non-Disclosure',
            'liability': 'Limitation of Liability',
            'termination': 'Termination Conditions',
            'payment': 'Payment Terms',
            'dispute_resolution': 'Dispute Resolution/Arbitration',
            'governing_law': 'Governing Law and Jurisdiction'
        }
        
        return [readable_names.get(m, m.replace('_', ' ').title()) for m in missing]
    
    def _compile_risk_factors(self, unfavorable: float, missing: float, 
                              ambiguity: float, unusual: float) -> List[Dict]:
        """Compile all risk factors with scores"""
        factors = []
        
        if unfavorable > 0:
            factors.append({
                'factor': 'Unfavorable Terms',
                'score': round(unfavorable, 2),
                'severity': self._get_risk_level(unfavorable),
                'description': f'{unfavorable:.1f}% of clauses contain potentially unfavorable terms'
            })
        
        if missing > 0:
            factors.append({
                'factor': 'Missing Clauses',
                'score': round(missing, 2),
                'severity': self._get_risk_level(missing),
                'description': f'{missing:.1f}% of essential clauses are missing'
            })
        
        if ambiguity > 0:
            factors.append({
                'factor': 'Ambiguous Language',
                'score': round(ambiguity, 2),
                'severity': self._get_risk_level(ambiguity),
                'description': f'{ambiguity:.1f}% of clauses contain vague or ambiguous language'
            })
        
        if unusual > 0:
            factors.append({
                'factor': 'Unusual Obligations',
                'score': round(unusual, 2),
                'severity': self._get_risk_level(unusual),
                'description': f'{unusual:.1f}% of clauses contain unusual or extreme obligations'
            })
        
        return factors
    
    def _generate_recommendations(self, assessment: RiskAssessment) -> List[str]:
        """Generate overall recommendations"""
        recommendations = []
        
        # Based on overall risk level
        if assessment.overall_risk_level == 'critical':
            recommendations.append("⚠️ CRITICAL: This document contains significant risks. Legal review is strongly recommended before signing.")
        elif assessment.overall_risk_level == 'high':
            recommendations.append("⚠️ HIGH RISK: Multiple concerning clauses detected. Consider negotiating key terms.")
        elif assessment.overall_risk_level == 'medium':
            recommendations.append("⚠️ MODERATE RISK: Some areas of concern. Review highlighted clauses carefully.")
        else:
            recommendations.append("✓ LOW RISK: Document appears relatively balanced. Standard review recommended.")
        
        # Missing clauses
        if assessment.missing_clauses:
            recommendations.append(f"Add missing essential clauses: {', '.join(assessment.missing_clauses[:3])}")
        
        # Unfavorable terms
        if len(assessment.unfavorable_terms) > 3:
            recommendations.append(f"Negotiate or clarify {len(assessment.unfavorable_terms)} high-risk clauses")
        
        # Specific recommendations
        if any('liability' in str(c).lower() for c in assessment.unfavorable_terms):
            recommendations.append("Review liability limitations carefully - consider adding caps or exclusions")
        
        if 'Termination Conditions' in assessment.missing_clauses:
            recommendations.append("Add clear termination clause with notice periods and conditions")
        
        if 'Dispute Resolution/Arbitration' in assessment.missing_clauses:
            recommendations.append("Include dispute resolution mechanism to avoid costly litigation")
        
        return recommendations
