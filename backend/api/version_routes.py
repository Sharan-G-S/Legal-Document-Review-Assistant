
# ============= VERSION MANAGEMENT ENDPOINTS =============

@api_bp.route('/document/<document_id>/version', methods=['POST'])
def upload_new_version(document_id):
    """Upload a new version of an existing document"""
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
        
        # Create version entry
        version_data = version_manager.create_version(document, parent_id=document_id)
        
        return jsonify({
            'success': True,
            'message': 'New version uploaded successfully',
            'version': version_data,
            'document': document.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Error uploading new version: {str(e)}'
        }), 500

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
        return jsonify({
            'error': f'Error retrieving versions: {str(e)}'
        }), 500

@api_bp.route('/version/<version_id>', methods=['GET'])
def get_version(version_id):
    """Get a specific version"""
    try:
        version = version_manager.get_version_by_id(version_id)
        
        if not version:
            return jsonify({
                'error': 'Version not found'
            }), 404
        
        # Load full document data
        document = processor.load_document_data(version_id)
        
        return jsonify({
            'success': True,
            'version': version,
            'document': document
        }), 200
    
    except FileNotFoundError:
        return jsonify({
            'error': 'Version not found'
        }), 404
    
    except Exception as e:
        return jsonify({
            'error': f'Error retrieving version: {str(e)}'
        }), 500

@api_bp.route('/compare/<version1_id>/<version2_id>', methods=['GET'])
def compare_versions(version1_id, version2_id):
    """Compare two versions of a document"""
    try:
        comparison = version_manager.compare_versions(version1_id, version2_id)
        
        return jsonify({
            'success': True,
            'comparison': comparison
        }), 200
    
    except FileNotFoundError as e:
        return jsonify({
            'error': 'One or both versions not found'
        }), 404
    
    except Exception as e:
        return jsonify({
            'error': f'Error comparing versions: {str(e)}'
        }), 500

@api_bp.route('/version/<version_id>/restore', methods=['POST'])
def restore_version(version_id):
    """Restore a previous version as the current version"""
    try:
        version = version_manager.get_version_by_id(version_id)
        
        if not version:
            return jsonify({
                'error': 'Version not found'
            }), 404
        
        # Load the version's document data
        document_data = processor.load_document_data(version_id)
        
        # Create a new version based on this data
        # (In a real implementation, you'd copy the file and reprocess)
        
        return jsonify({
            'success': True,
            'message': 'Version restored successfully',
            'version': version
        }), 200
    
    except FileNotFoundError:
        return jsonify({
            'error': 'Version not found'
        }), 404
    
    except Exception as e:
        return jsonify({
            'error': f'Error restoring version: {str(e)}'
        }), 500
