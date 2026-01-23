from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
from config import Config
from services.document_processor import DocumentProcessor
from utils.pdf_generator import PDFReportGenerator
import os

# Create blueprint
api_bp = Blueprint('api', __name__)

# Initialize document processor
config = Config()
processor = DocumentProcessor(
    upload_folder=config.UPLOAD_FOLDER,
    processed_folder=config.PROCESSED_FOLDER
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
            }
        ]
    }
    
    return jsonify(docs), 200
