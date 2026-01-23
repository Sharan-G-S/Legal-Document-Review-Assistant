from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import uuid

@dataclass
class Clause:
    """Represents a detected clause in a legal document"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    category: str = ""
    start_position: int = 0
    end_position: int = 0
    risk_level: str = "low"
    risk_score: float = 0.0
    confidence: float = 0.0
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert clause to dictionary"""
        return {
            'id': self.id,
            'text': self.text,
            'category': self.category,
            'start_position': self.start_position,
            'end_position': self.end_position,
            'risk_level': self.risk_level,
            'risk_score': self.risk_score,
            'confidence': self.confidence,
            'issues': self.issues,
            'recommendations': self.recommendations
        }

@dataclass
class KeyTerm:
    """Represents an important term or entity in the document"""
    text: str = ""
    category: str = ""  # DATE, MONEY, ORG, PERSON, etc.
    frequency: int = 0
    importance_score: float = 0.0
    context: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert key term to dictionary"""
        return {
            'text': self.text,
            'category': self.category,
            'frequency': self.frequency,
            'importance_score': self.importance_score,
            'context': self.context
        }

@dataclass
class RiskAssessment:
    """Overall risk assessment for the document"""
    overall_risk_level: str = "low"
    overall_risk_score: float = 0.0
    risk_factors: List[Dict] = field(default_factory=list)
    missing_clauses: List[str] = field(default_factory=list)
    unfavorable_terms: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert risk assessment to dictionary"""
        return {
            'overall_risk_level': self.overall_risk_level,
            'overall_risk_score': self.overall_risk_score,
            'risk_factors': self.risk_factors,
            'missing_clauses': self.missing_clauses,
            'unfavorable_terms': self.unfavorable_terms,
            'recommendations': self.recommendations
        }

@dataclass
class DocumentSummary:
    """Summary of the legal document"""
    document_type: str = "Unknown"
    purpose: str = ""
    parties: List[str] = field(default_factory=list)
    key_obligations: List[str] = field(default_factory=list)
    key_rights: List[str] = field(default_factory=list)
    important_dates: List[Dict] = field(default_factory=list)
    monetary_values: List[Dict] = field(default_factory=list)
    executive_summary: str = ""
    
    def to_dict(self) -> Dict:
        """Convert summary to dictionary"""
        return {
            'document_type': self.document_type,
            'purpose': self.purpose,
            'parties': self.parties,
            'key_obligations': self.key_obligations,
            'key_rights': self.key_rights,
            'important_dates': self.important_dates,
            'monetary_values': self.monetary_values,
            'executive_summary': self.executive_summary
        }

@dataclass
class Document:
    """Represents a legal document and its analysis"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = ""
    file_path: str = ""
    file_type: str = ""
    file_size: int = 0
    upload_date: str = field(default_factory=lambda: datetime.now().isoformat())
    processed: bool = False
    processing_date: Optional[str] = None
    
    # Extracted content
    raw_text: str = ""
    page_count: int = 0
    word_count: int = 0
    
    # Analysis results
    clauses: List[Clause] = field(default_factory=list)
    key_terms: List[KeyTerm] = field(default_factory=list)
    risk_assessment: Optional[RiskAssessment] = None
    summary: Optional[DocumentSummary] = None
    
    def to_dict(self) -> Dict:
        """Convert document to dictionary"""
        return {
            'id': self.id,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'upload_date': self.upload_date,
            'processed': self.processed,
            'processing_date': self.processing_date,
            'page_count': self.page_count,
            'word_count': self.word_count,
            'clauses': [c.to_dict() for c in self.clauses],
            'key_terms': [kt.to_dict() for kt in self.key_terms],
            'risk_assessment': self.risk_assessment.to_dict() if self.risk_assessment else None,
            'summary': self.summary.to_dict() if self.summary else None
        }
