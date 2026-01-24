from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import json
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from services.document_processor import DocumentProcessor

class BatchProcessor:
    """Process multiple documents concurrently with progress tracking"""
    
    def __init__(self, upload_folder: Path, processed_folder: Path, batch_folder: Path, max_workers: int = 3):
        self.upload_folder = Path(upload_folder)
        self.processed_folder = Path(processed_folder)
        self.batch_folder = Path(batch_folder)
        self.batch_folder.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
        self.processor = DocumentProcessor(upload_folder, processed_folder)
        self._lock = threading.Lock()
    
    def create_batch(self, files: List[tuple]) -> str:
        """
        Create a new batch job
        
        Args:
            files: List of (filename, file_object) tuples
            
        Returns:
            Batch ID
        """
        batch_id = str(uuid.uuid4())
        
        batch_data = {
            'batch_id': batch_id,
            'created_at': datetime.now().isoformat(),
            'status': 'pending',
            'total_documents': len(files),
            'completed_documents': 0,
            'failed_documents': 0,
            'progress_percentage': 0,
            'documents': [
                {
                    'filename': filename,
                    'status': 'pending',
                    'document_id': None,
                    'error': None
                }
                for filename, _ in files
            ]
        }
        
        # Save batch metadata
        self._save_batch_metadata(batch_id, batch_data)
        
        return batch_id
    
    def process_batch(self, batch_id: str, files: List[tuple]) -> Dict:
        """
        Process all documents in a batch concurrently
        
        Args:
            batch_id: Batch identifier
            files: List of (filename, file_path) tuples
            
        Returns:
            Batch results
        """
        # Update status to processing
        self._update_batch_status(batch_id, 'processing')
        
        # Process documents concurrently
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self._process_single_document, filename, file_path, batch_id, idx): (filename, idx)
                for idx, (filename, file_path) in enumerate(files)
            }
            
            # Process results as they complete
            for future in as_completed(future_to_file):
                filename, idx = future_to_file[future]
                try:
                    result = future.result()
                    self._update_document_status(batch_id, idx, result)
                except Exception as e:
                    self._update_document_status(batch_id, idx, {
                        'status': 'failed',
                        'error': str(e)
                    })
        
        # Mark batch as completed
        self._update_batch_status(batch_id, 'completed')
        
        # Return final results
        return self.get_batch_results(batch_id)
    
    def _process_single_document(self, filename: str, file_path: Path, batch_id: str, idx: int) -> Dict:
        """Process a single document"""
        try:
            # Update status to processing
            with self._lock:
                batch_data = self._load_batch_metadata(batch_id)
                batch_data['documents'][idx]['status'] = 'processing'
                self._save_batch_metadata(batch_id, batch_data)
            
            # Process the document
            document = self.processor.process_document(file_path, filename)
            
            return {
                'status': 'completed',
                'document_id': document.id,
                'error': None
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'document_id': None,
                'error': str(e)
            }
    
    def _update_document_status(self, batch_id: str, doc_index: int, result: Dict):
        """Update the status of a specific document in the batch"""
        with self._lock:
            batch_data = self._load_batch_metadata(batch_id)
            
            # Update document status
            batch_data['documents'][doc_index].update(result)
            
            # Update counters
            if result['status'] == 'completed':
                batch_data['completed_documents'] += 1
            elif result['status'] == 'failed':
                batch_data['failed_documents'] += 1
            
            # Update progress
            total = batch_data['total_documents']
            completed = batch_data['completed_documents'] + batch_data['failed_documents']
            batch_data['progress_percentage'] = int((completed / total) * 100)
            
            self._save_batch_metadata(batch_id, batch_data)
    
    def _update_batch_status(self, batch_id: str, status: str):
        """Update the overall batch status"""
        with self._lock:
            batch_data = self._load_batch_metadata(batch_id)
            batch_data['status'] = status
            self._save_batch_metadata(batch_id, batch_data)
    
    def get_batch_status(self, batch_id: str) -> Dict:
        """Get current batch status"""
        return self._load_batch_metadata(batch_id)
    
    def get_batch_results(self, batch_id: str) -> Dict:
        """
        Get comprehensive batch results with statistics
        
        Returns:
            Batch results with aggregated statistics
        """
        batch_data = self._load_batch_metadata(batch_id)
        
        # Calculate statistics
        successful_docs = [doc for doc in batch_data['documents'] if doc['status'] == 'completed']
        
        risk_distribution = {
            'low': 0,
            'medium': 0,
            'high': 0,
            'critical': 0
        }
        
        total_risk_score = 0
        total_clauses = 0
        
        # Load full document data for successful documents
        detailed_results = []
        for doc in successful_docs:
            if doc['document_id']:
                try:
                    doc_data = self.processor.load_document_data(doc['document_id'])
                    detailed_results.append(doc_data)
                    
                    # Aggregate statistics
                    risk_level = doc_data.get('risk_assessment', {}).get('overall_risk_level', 'unknown')
                    if risk_level in risk_distribution:
                        risk_distribution[risk_level] += 1
                    
                    total_risk_score += doc_data.get('risk_assessment', {}).get('overall_risk_score', 0)
                    total_clauses += len(doc_data.get('clauses', []))
                except Exception:
                    continue
        
        avg_risk_score = total_risk_score / len(successful_docs) if successful_docs else 0
        
        return {
            'batch_id': batch_id,
            'status': batch_data['status'],
            'created_at': batch_data['created_at'],
            'total_documents': batch_data['total_documents'],
            'successful': batch_data['completed_documents'],
            'failed': batch_data['failed_documents'],
            'progress_percentage': batch_data['progress_percentage'],
            'risk_distribution': risk_distribution,
            'average_risk_score': round(avg_risk_score, 2),
            'total_clauses_detected': total_clauses,
            'documents': batch_data['documents'],
            'detailed_results': detailed_results
        }
    
    def list_batches(self) -> List[Dict]:
        """List all batch jobs"""
        batches = []
        
        for batch_file in self.batch_folder.glob('*.json'):
            try:
                with open(batch_file, 'r', encoding='utf-8') as f:
                    batch_data = json.load(f)
                    batches.append({
                        'batch_id': batch_data['batch_id'],
                        'created_at': batch_data['created_at'],
                        'status': batch_data['status'],
                        'total_documents': batch_data['total_documents'],
                        'progress_percentage': batch_data['progress_percentage']
                    })
            except Exception:
                continue
        
        # Sort by creation date (newest first)
        batches.sort(key=lambda x: x['created_at'], reverse=True)
        return batches
    
    def _save_batch_metadata(self, batch_id: str, batch_data: Dict):
        """Save batch metadata to file"""
        batch_file = self.batch_folder / f"{batch_id}.json"
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)
    
    def _load_batch_metadata(self, batch_id: str) -> Dict:
        """Load batch metadata from file"""
        batch_file = self.batch_folder / f"{batch_id}.json"
        
        if not batch_file.exists():
            raise FileNotFoundError(f"Batch {batch_id} not found")
        
        with open(batch_file, 'r', encoding='utf-8') as f:
            return json.load(f)
