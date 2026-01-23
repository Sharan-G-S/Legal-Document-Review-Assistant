from typing import List
from models.models import DocumentSummary, Clause, KeyTerm
import re

class DocumentSummarizer:
    """Generate comprehensive document summaries"""
    
    def generate_summary(self, text: str, clauses: List[Clause], 
                        key_terms: List[KeyTerm]) -> DocumentSummary:
        """
        Generate document summary
        
        Args:
            text: Full document text
            clauses: Detected clauses
            key_terms: Extracted key terms
            
        Returns:
            DocumentSummary object
        """
        summary = DocumentSummary()
        
        # Detect document type
        summary.document_type = self._detect_document_type(text, clauses)
        
        # Extract parties
        summary.parties = self._extract_parties(key_terms)
        
        # Extract key obligations and rights
        summary.key_obligations = self._extract_obligations(text, clauses)
        summary.key_rights = self._extract_rights(text, clauses)
        
        # Extract important dates
        summary.important_dates = self._extract_important_dates(key_terms)
        
        # Extract monetary values
        summary.monetary_values = self._extract_monetary_values(key_terms)
        
        # Generate purpose
        summary.purpose = self._generate_purpose(summary.document_type, text)
        
        # Generate executive summary
        summary.executive_summary = self._generate_executive_summary(summary, clauses)
        
        return summary
    
    def _detect_document_type(self, text: str, clauses: List[Clause]) -> str:
        """Detect the type of legal document"""
        text_lower = text.lower()
        
        # Common document type indicators
        doc_types = {
            'Non-Disclosure Agreement (NDA)': ['non-disclosure', 'nda', 'confidential information'],
            'Service Agreement': ['service agreement', 'services', 'provider', 'client'],
            'Employment Contract': ['employment', 'employee', 'employer', 'position', 'salary'],
            'License Agreement': ['license', 'licensor', 'licensee', 'intellectual property'],
            'Lease Agreement': ['lease', 'landlord', 'tenant', 'premises', 'rent'],
            'Purchase Agreement': ['purchase', 'buyer', 'seller', 'goods', 'merchandise'],
            'Partnership Agreement': ['partnership', 'partners', 'profit sharing'],
            'Consulting Agreement': ['consulting', 'consultant', 'professional services'],
            'Terms of Service': ['terms of service', 'terms and conditions', 'user agreement'],
            'Privacy Policy': ['privacy policy', 'personal data', 'data protection']
        }
        
        for doc_type, keywords in doc_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return doc_type
        
        return 'Legal Contract'
    
    def _extract_parties(self, key_terms: List[KeyTerm]) -> List[str]:
        """Extract parties involved in the agreement"""
        parties = []
        
        for term in key_terms:
            if term.category in ['ORG', 'PERSON']:
                if term.text not in parties:
                    parties.append(term.text)
        
        return parties[:5]  # Limit to 5 parties
    
    def _extract_obligations(self, text: str, clauses: List[Clause]) -> List[str]:
        """Extract key obligations from the document"""
        obligations = []
        
        # Keywords indicating obligations
        obligation_keywords = [
            'shall', 'must', 'required to', 'obligated to',
            'agrees to', 'undertakes to', 'responsible for'
        ]
        
        # Search in clauses
        for clause in clauses:
            clause_lower = clause.text.lower()
            if any(keyword in clause_lower for keyword in obligation_keywords):
                # Extract the obligation (simplified)
                obligation = clause.text[:150] + '...' if len(clause.text) > 150 else clause.text
                obligations.append(obligation)
                
                if len(obligations) >= 5:
                    break
        
        return obligations
    
    def _extract_rights(self, text: str, clauses: List[Clause]) -> List[str]:
        """Extract key rights from the document"""
        rights = []
        
        # Keywords indicating rights
        rights_keywords = [
            'entitled to', 'right to', 'may', 'permitted to',
            'authorized to', 'privilege'
        ]
        
        # Search in clauses
        for clause in clauses:
            clause_lower = clause.text.lower()
            if any(keyword in clause_lower for keyword in rights_keywords):
                # Extract the right (simplified)
                right = clause.text[:150] + '...' if len(clause.text) > 150 else clause.text
                rights.append(right)
                
                if len(rights) >= 5:
                    break
        
        return rights
    
    def _extract_important_dates(self, key_terms: List[KeyTerm]) -> List[dict]:
        """Extract important dates"""
        dates = []
        
        for term in key_terms:
            if term.category == 'DATE':
                dates.append({
                    'date': term.text,
                    'context': term.context[0] if term.context else ''
                })
        
        return dates[:5]
    
    def _extract_monetary_values(self, key_terms: List[KeyTerm]) -> List[dict]:
        """Extract monetary values"""
        values = []
        
        for term in key_terms:
            if term.category == 'MONEY':
                values.append({
                    'amount': term.text,
                    'context': term.context[0] if term.context else ''
                })
        
        return values[:5]
    
    def _generate_purpose(self, doc_type: str, text: str) -> str:
        """Generate document purpose statement"""
        # Simple purpose generation based on document type
        purposes = {
            'Non-Disclosure Agreement (NDA)': 'To protect confidential information shared between parties',
            'Service Agreement': 'To define terms for provision of services',
            'Employment Contract': 'To establish employment relationship and terms',
            'License Agreement': 'To grant rights to use intellectual property',
            'Lease Agreement': 'To establish rental terms for property',
            'Purchase Agreement': 'To facilitate the purchase and sale of goods',
            'Partnership Agreement': 'To establish partnership terms and profit sharing',
            'Consulting Agreement': 'To engage consulting services',
            'Terms of Service': 'To govern use of services or platform',
            'Privacy Policy': 'To explain data collection and usage practices'
        }
        
        return purposes.get(doc_type, 'To establish legal obligations and rights between parties')
    
    def _generate_executive_summary(self, summary: DocumentSummary, 
                                   clauses: List[Clause]) -> str:
        """Generate executive summary"""
        parts = []
        
        # Document type and purpose
        parts.append(f"This is a {summary.document_type}. {summary.purpose}.")
        
        # Parties
        if summary.parties:
            if len(summary.parties) == 2:
                parts.append(f"The agreement is between {summary.parties[0]} and {summary.parties[1]}.")
            elif len(summary.parties) > 2:
                parts.append(f"The parties involved include {', '.join(summary.parties[:3])}.")
        
        # Key monetary values
        if summary.monetary_values:
            parts.append(f"Key financial terms include {summary.monetary_values[0]['amount']}.")
        
        # Important dates
        if summary.important_dates:
            parts.append(f"Important dates: {summary.important_dates[0]['date']}.")
        
        # Risk overview
        high_risk_clauses = [c for c in clauses if c.risk_level in ['high', 'critical']]
        if high_risk_clauses:
            parts.append(f"The document contains {len(high_risk_clauses)} high-risk clauses requiring careful review.")
        else:
            parts.append("The document appears to have standard terms with no critical risk factors.")
        
        return ' '.join(parts)
