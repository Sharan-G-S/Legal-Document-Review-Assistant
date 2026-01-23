from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
from models.models import Document
from services.text_extractor import TextExtractor
from ai.clause_detector import ClauseDetector
from ai.risk_analyzer import RiskAnalyzer
from ai.key_terms_extractor import KeyTermsExtractor
from ai.summarizer import DocumentSummarizer
import json

class DocumentProcessor:
    """Main document processing pipeline"""
    
    def __init__(self, upload_folder: Path, processed_folder: Path):
        self.upload_folder = Path(upload_folder)
        self.processed_folder = Path(processed_folder)
        
        # Initialize AI components
        self.text_extractor = TextExtractor()
        self.clause_detector = ClauseDetector()
        self.risk_analyzer = RiskAnalyzer()
        self.key_terms_extractor = KeyTermsExtractor()
        self.summarizer = DocumentSummarizer()
    
    def save_uploaded_file(self, file, filename: str) -> str:
        """
        Save uploaded file to disk
        
        Args:
            file: File object from request
            filename: Original filename
            
        Returns:
            Path to saved file
        """
        # Secure the filename
        filename = secure_filename(filename)
        
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = filename.rsplit('.', 1)
        unique_filename = f"{name}_{timestamp}.{ext}"
        
        # Save file
        file_path = self.upload_folder / unique_filename
        file.save(str(file_path))
        
        return str(file_path)
    
    def process_document(self, file_path: str, filename: str) -> Document:
        """
        Process a legal document through the complete analysis pipeline
        
        Args:
            file_path: Path to the uploaded file
            filename: Original filename
            
        Returns:
            Document object with complete analysis
        """
        file_path = Path(file_path)
        
        # Create document object
        document = Document(
            filename=filename,
            file_path=str(file_path),
            file_type=file_path.suffix.lower(),
            file_size=file_path.stat().st_size
        )
        
        # Step 1: Extract text
        print(f"📄 Extracting text from {filename}...")
        raw_text, page_count = self.text_extractor.extract_text(str(file_path))
        document.raw_text = raw_text
        document.page_count = page_count
        document.word_count = len(raw_text.split())
        
        # Step 2: Detect clauses
        print(f"🔍 Detecting clauses...")
        document.clauses = self.clause_detector.detect_clauses(raw_text)
        
        # Step 3: Extract key terms
        print(f"🔑 Extracting key terms...")
        document.key_terms = self.key_terms_extractor.extract_key_terms(raw_text)
        
        # Step 4: Perform risk assessment
        print(f"⚠️  Analyzing risks...")
        document.risk_assessment = self.risk_analyzer.analyze_risks(
            raw_text, 
            document.clauses
        )
        
        # Step 5: Generate summary
        print(f"📝 Generating summary...")
        document.summary = self.summarizer.generate_summary(
            raw_text,
            document.clauses,
            document.key_terms
        )
        
        # Mark as processed
        document.processed = True
        document.processing_date = datetime.now().isoformat()
        
        # Save processed document data
        self._save_document_data(document)
        
        print(f"✅ Document processing complete!")
        return document
    
    def _save_document_data(self, document: Document):
        """Save document analysis data to JSON file"""
        output_file = self.processed_folder / f"{document.id}.json"
        
        # Don't save raw text to keep file size manageable
        doc_dict = document.to_dict()
        doc_dict['raw_text'] = f"[{document.word_count} words - stored separately]"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(doc_dict, f, indent=2, ensure_ascii=False)
    
    def load_document_data(self, document_id: str) -> Document:
        """Load processed document data from JSON file"""
        data_file = self.processed_folder / f"{document_id}.json"
        
        if not data_file.exists():
            raise FileNotFoundError(f"Document {document_id} not found")
        
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Reconstruct document object (simplified version)
        # In production, you'd want proper deserialization
        return data
    
    def list_documents(self):
        """List all processed documents"""
        documents = []
        for file_path in self.processed_folder.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    documents.append({
                        'id': data['id'],
                        'filename': data['filename'],
                        'upload_date': data['upload_date'],
                        'processed': data['processed'],
                        'risk_level': data.get('risk_assessment', {}).get('overall_risk_level', 'unknown')
                    })
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                continue
        
        return sorted(documents, key=lambda x: x['upload_date'], reverse=True)
