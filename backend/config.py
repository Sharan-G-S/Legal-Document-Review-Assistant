import os
from pathlib import Path

class Config:
    """Application configuration"""
    
    # Base directory
    BASE_DIR = Path(__file__).parent
    
    # Upload configuration
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    PROCESSED_FOLDER = BASE_DIR / 'processed'
    REPORTS_FOLDER = BASE_DIR / 'reports'
    VERSIONS_FOLDER = BASE_DIR / 'versions'
    BATCH_FOLDER = BASE_DIR / 'batches'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
    
    # Batch processing configuration
    MAX_BATCH_SIZE = 10  # Maximum documents per batch
    CONCURRENT_WORKERS = 3  # Number of parallel processing workers
    
    # AI Model configuration
    SPACY_MODEL = 'en_core_web_sm'  # Will be downloaded if not present
    USE_GPU = False  # Set to True if GPU is available
    
    # Clause detection patterns
    CLAUSE_CATEGORIES = {
        'confidentiality': ['confidential', 'non-disclosure', 'proprietary', 'secret'],
        'liability': ['liability', 'indemnify', 'indemnification', 'damages', 'liable'],
        'termination': ['termination', 'terminate', 'cancel', 'cancellation', 'end'],
        'payment': ['payment', 'fee', 'compensation', 'remuneration', 'invoice'],
        'intellectual_property': ['intellectual property', 'ip', 'copyright', 'patent', 'trademark'],
        'dispute_resolution': ['arbitration', 'mediation', 'dispute', 'litigation', 'jurisdiction'],
        'force_majeure': ['force majeure', 'act of god', 'unavoidable'],
        'warranty': ['warranty', 'guarantee', 'representation', 'warranted'],
        'assignment': ['assignment', 'transfer', 'assign'],
        'governing_law': ['governing law', 'applicable law', 'jurisdiction']
    }
    
    # Risk scoring weights
    RISK_WEIGHTS = {
        'unfavorable_terms': 0.4,
        'missing_clauses': 0.3,
        'ambiguous_language': 0.2,
        'unusual_obligations': 0.1
    }
    
    # Risk levels
    RISK_LEVELS = {
        'low': (0, 30),
        'medium': (30, 60),
        'high': (60, 85),
        'critical': (85, 100)
    }
    
    # Create necessary directories
    @classmethod
    def init_app(cls):
        """Initialize application directories"""
        for folder in [cls.UPLOAD_FOLDER, cls.PROCESSED_FOLDER, cls.REPORTS_FOLDER, cls.VERSIONS_FOLDER, cls.BATCH_FOLDER]:
            folder.mkdir(parents=True, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
