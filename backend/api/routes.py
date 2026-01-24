from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
from config import Config
from services.document_processor import DocumentProcessor
from services.version_manager import VersionManager
from services.batch_processor import BatchProcessor
from utils.pdf_generator import PDFReportGenerator
import os
import threading

# Create blueprint
api_bp = Blueprint('api', __name__)

# Initialize document processor
config = Config()
processor = DocumentProcessor(
    upload_folder=config.UPLOAD_FOLDER,
    processed_folder=config.PROCESSED_FOLDER
)

# Initialize version manager
version_manager = VersionManager(config.VERSIONS_FOLDER)

# Initialize batch processor
batch_processor = BatchProcessor(
    upload_folder=config.UPLOAD_FOLDER,
    processed_folder=config.PROCESSED_FOLDER,
    batch_folder=config.BATCH_FOLDER,
    max_workers=config.CONCURRENT_WORKERS
)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@api_bp.route('/upload', methods=['POST'])
def upload_document():
    """Upload and process a legal document"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'Invalid file type. Allowed types: {", ".join(Config.ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Save file
        filename = secure_filename(file.filename)
        file_path = processor.save_uploaded_file(file, filename)
        
        # Process document
        document = processor.process_document(file_path, filename)
        
        return jsonify({
            'success': True,
            'message': 'Document processed successfully',
            'document': document.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Error processing document: {str(e)}'
        }), 500

@api_bp.route('/documents', methods=['GET'])
def list_documents():
    """List all processed documents"""
    try:
        documents = processor.list_documents()
        return jsonify({
            'success': True,
            'documents': documents,
            'count': len(documents)
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Error listing documents: {str(e)}'
        }), 500

@api_bp.route('/document/<document_id>', methods=['GET'])
def get_document(document_id):
    """Get complete document analysis"""
    try:
        document = processor.load_document_data(document_id)
        return jsonify({
            'success': True,
            'document': document
        }), 200
    
    except FileNotFoundError:
        return jsonify({
            'error': 'Document not found'
        }), 404
    
    except Exception as e:
        return jsonify({
            'error': f'Error retrieving document: {str(e)}'
        }), 500

@api_bp.route('/document/<document_id>/clauses', methods=['GET'])
def get_clauses(document_id):
    """Get detected clauses for a document"""
    try:
        document = processor.load_document_data(document_id)
        return jsonify({
            'success': True,
            'clauses': document.get('clauses', []),
            'count': len(document.get('clauses', []))
        }), 200
    
    except FileNotFoundError:
        return jsonify({
            'error': 'Document not found'
        }), 404
    
    except Exception as e:
        return jsonify({
            'error': f'Error retrieving clauses: {str(e)}'
        }), 500

@api_bp.route('/document/<document_id>/risks', methods=['GET'])
def get_risks(document_id):
    """Get risk assessment for a document"""
    try:
        document = processor.load_document_data(document_id)
        return jsonify({
            'success': True,
            'risk_assessment': document.get('risk_assessment', {})
        }), 200
    
    except FileNotFoundError:
        return jsonify({
            'error': 'Document not found'
        }), 404
    
    except Exception as e:
        return jsonify({
            'error': f'Error retrieving risk assessment: {str(e)}'
        }), 500

@api_bp.route('/document/<document_id>/summary', methods=['GET'])
def get_summary(document_id):
    """Get document summary"""
    try:
        document = processor.load_document_data(document_id)
        return jsonify({
            'success': True,
            'summary': document.get('summary', {})
        }), 200
    
    except FileNotFoundError:
        return jsonify({
            'error': 'Document not found'
        }), 404
    
    except Exception as e:
        return jsonify({
            'error': f'Error retrieving summary: {str(e)}'
        }), 500

@api_bp.route('/export/<document_id>', methods=['POST'])
def export_report(document_id):
    """Export document analysis as PDF report"""
    try:
        # Load document data
        document = processor.load_document_data(document_id)
        
        # Generate PDF report
        pdf_generator = PDFReportGenerator()
        pdf_path = pdf_generator.generate_report(document, Config.REPORTS_FOLDER)
        
        # Send file
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"legal_analysis_{document_id}.pdf",
            mimetype='application/pdf'
        )
    
    except FileNotFoundError:
        return jsonify({
            'error': 'Document not found'
        }), 404
    
    except Exception as e:
        return jsonify({
            'error': f'Error generating report: {str(e)}'
        }), 500

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    try:
        documents = processor.list_documents()
        
        # Calculate statistics
        total_docs = len(documents)
        risk_distribution = {
            'low': 0,
            'medium': 0,
            'high': 0,
            'critical': 0
        }
        
        for doc in documents:
            risk_level = doc.get('risk_level', 'unknown')
            if risk_level in risk_distribution:
                risk_distribution[risk_level] += 1
        
        return jsonify({
            'success': True,
            'stats': {
                'total_documents': total_docs,
                'risk_distribution': risk_distribution
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Error calculating statistics: {str(e)}'
        }), 500

@api_bp.route('/docs', methods=['GET'])
def api_documentation():
    """API documentation"""
    docs = {
        'version': '1.0.0',
        'endpoints': [
            {
                'path': '/api/upload',
                'method': 'POST',
                'description': 'Upload and process a legal document',
                'parameters': {
                    'file': 'Document file (PDF or DOCX)'
                }
            },
            {
                'path': '/api/documents',
                'method': 'GET',
                'description': 'List all processed documents'
            },
            {
                'path': '/api/document/<id>',
                'method': 'GET',
                'description': 'Get complete document analysis'
            },
            {
                'path': '/api/document/<id>/clauses',
                'method': 'GET',
                'description': 'Get detected clauses'
            },
            {
                'path': '/api/document/<id>/risks',
                'method': 'GET',
                'description': 'Get risk assessment'
            },
            {
                'path': '/api/document/<id>/summary',
                'method': 'GET',
                'description': 'Get document summary'
            },
            {
                'path': '/api/export/<id>',
                'method': 'POST',
                'description': 'Export analysis as PDF report'
            },
            {
                'path': '/api/stats',
                'method': 'GET',
                'description': 'Get overall statistics'
            },
            {
                'path': '/api/document/<id>/version',
                'method': 'POST',
                'description': 'Upload new version of document'
            },
            {
                'path': '/api/document/<id>/versions',
                'method': 'GET',
                'description': 'Get all versions of document'
            },
            {
                'path': '/api/version/<version_id>',
                'method': 'GET',
                'description': 'Get specific version'
            },
            {
                'path': '/api/compare/<v1_id>/<v2_id>',
                'method': 'GET',
                'description': 'Compare two versions'
            },
            {
                'path': '/api/version/<version_id>/restore',
                'method': 'POST',
                'description': 'Restore previous version'
            }
        ]
    }
    
    return jsonify(docs), 200

# ============= VERSION MANAGEMENT ENDPOINTS =============

@api_bp.route('/document/<document_id>/version', methods=['POST'])
def upload_new_version(document_id):
    """Upload a new version of an existing document"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'Invalid file type. Allowed types: {", ".join(Config.ALLOWED_EXTENSIONS)}'
            }), 400
        
        filename = secure_filename(file.filename)
        file_path = processor.save_uploaded_file(file, filename)
        document = processor.process_document(file_path, filename)
        version_data = version_manager.create_version(document, parent_id=document_id)
        
        return jsonify({
            'success': True,
            'message': 'New version uploaded successfully',
            'version': version_data,
            'document': document.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': f'Error uploading new version: {str(e)}'}), 500

@api_bp.route('/document/<document_id>/versions', methods=['GET'])
def get_document_versions(document_id):
    """Get all versions of a document"""
    try:
        versions = version_manager.get_versions(document_id)
        return jsonify({
            'success': True,
            'document_id': document_id,
            'versions': versions,
            'count': len(versions)
        }), 200
    except Exception as e:
        return jsonify({'error': f'Error retrieving versions: {str(e)}'}), 500

@api_bp.route('/version/<version_id>', methods=['GET'])
def get_version(version_id):
    """Get a specific version"""
    try:
        version = version_manager.get_version_by_id(version_id)
        if not version:
            return jsonify({'error': 'Version not found'}), 404
        document = processor.load_document_data(version_id)
        return jsonify({
            'success': True,
            'version': version,
            'document': document
        }), 200
    except FileNotFoundError:
        return jsonify({'error': 'Version not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Error retrieving version: {str(e)}'}), 500

@api_bp.route('/compare/<version1_id>/<version2_id>', methods=['GET'])
def compare_versions(version1_id, version2_id):
    """Compare two versions of a document"""
    try:
        comparison = version_manager.compare_versions(version1_id, version2_id)
        return jsonify({
            'success': True,
            'comparison': comparison
        }), 200
    except FileNotFoundError:
        return jsonify({'error': 'One or both versions not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Error comparing versions: {str(e)}'}), 500


# ============= BATCH PROCESSING ENDPOINTS =============

@api_bp.route('/batch/upload', methods=['POST'])
def batch_upload():
    """Upload and process multiple documents in a batch"""
    try:
        # Check if files are present
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({'error': 'No files selected'}), 400
        
        # Check batch size limit
        if len(files) > Config.MAX_BATCH_SIZE:
            return jsonify({
                'error': f'Batch size exceeds maximum limit of {Config.MAX_BATCH_SIZE} documents'
            }), 400
        
        # Validate all files
        file_data = []
        for file in files:
            if file.filename == '':
                continue
            
            if not allowed_file(file.filename):
                return jsonify({
                    'error': f'Invalid file type for {file.filename}. Allowed types: {", ".join(Config.ALLOWED_EXTENSIONS)}'
                }), 400
            
            # Save file
            filename = secure_filename(file.filename)
            file_path = processor.save_uploaded_file(file, filename)
            file_data.append((filename, file_path))
        
        if not file_data:
            return jsonify({'error': 'No valid files to process'}), 400
        
        # Create batch
        batch_id = batch_processor.create_batch(file_data)
        
        # Start processing in background thread
        def process_in_background():
            batch_processor.process_batch(batch_id, file_data)
        
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Batch created with {len(file_data)} documents',
            'batch_id': batch_id,
            'total_documents': len(file_data)
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Error creating batch: {str(e)}'
        }), 500

@api_bp.route('/batch/<batch_id>/status', methods=['GET'])
def get_batch_status(batch_id):
    """Get the current status of a batch job"""
    try:
        status = batch_processor.get_batch_status(batch_id)
        return jsonify({
            'success': True,
            'status': status
        }), 200
    
    except FileNotFoundError:
        return jsonify({
            'error': 'Batch not found'
        }), 404
    
    except Exception as e:
        return jsonify({
            'error': f'Error retrieving batch status: {str(e)}'
        }), 500

@api_bp.route('/batch/<batch_id>/results', methods=['GET'])
def get_batch_results(batch_id):
    """Get comprehensive results for a completed batch"""
    try:
        results = batch_processor.get_batch_results(batch_id)
        return jsonify({
            'success': True,
            'results': results
        }), 200
    
    except FileNotFoundError:
        return jsonify({
            'error': 'Batch not found'
        }), 404
    
    except Exception as e:
        return jsonify({
            'error': f'Error retrieving batch results: {str(e)}'
        }), 500

@api_bp.route('/batches', methods=['GET'])
def list_batches():
    """List all batch jobs"""
    try:
        batches = batch_processor.list_batches()
        return jsonify({
            'success': True,
            'batches': batches,
            'count': len(batches)
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Error listing batches: {str(e)}'
        }), 500
