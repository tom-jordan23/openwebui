"""
Prompt Management API
Provides CRUD operations and advanced features for prompt management
"""
from flask import Flask, request, jsonify, Blueprint
from typing import Dict, List, Optional, Any
import json
import time
import uuid
from dataclasses import asdict

from src.database.connection import get_db_connection
from src.database.models import PromptVersion, PromptCategory
from src.database.repositories import PromptRepository
import logging

logger = logging.getLogger(__name__)

# Create Blueprint for prompt management routes
prompt_bp = Blueprint('prompts', __name__, url_prefix='/api/v1/prompts')


class PromptService:
    """Service layer for prompt management operations"""
    
    def __init__(self):
        self.repo = PromptRepository()
    
    def create_prompt_version(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new prompt version"""
        try:
            # Validate required fields
            required_fields = ['prompt_id', 'title', 'content', 'created_by']
            for field in required_fields:
                if field not in prompt_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create PromptVersion object
            prompt_version = PromptVersion(
                prompt_id=prompt_data['prompt_id'],
                version_number=prompt_data.get('version_number', 1),
                title=prompt_data['title'],
                content=prompt_data['content'],
                variables=prompt_data.get('variables', {}),
                created_by=prompt_data['created_by']
            )
            
            # Save to database
            version_id = self.repo.create_version(prompt_version)
            if version_id:
                prompt_version.id = version_id
                return {
                    'success': True,
                    'version_id': version_id,
                    'version': asdict(prompt_version),
                    'message': 'Prompt version created successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create prompt version'
                }
        
        except Exception as e:
            logger.error(f"Error creating prompt version: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_prompt_versions(self, prompt_id: int) -> Dict[str, Any]:
        """Get all versions for a prompt"""
        try:
            versions = self.repo.get_versions_by_prompt_id(prompt_id)
            return {
                'success': True,
                'versions': [asdict(v) for v in versions],
                'count': len(versions)
            }
        except Exception as e:
            logger.error(f"Error getting prompt versions: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_active_version(self, prompt_id: int) -> Dict[str, Any]:
        """Get active version for a prompt"""
        try:
            version = self.repo.get_active_version(prompt_id)
            if version:
                return {
                    'success': True,
                    'version': asdict(version)
                }
            else:
                return {
                    'success': False,
                    'error': 'No active version found'
                }
        except Exception as e:
            logger.error(f"Error getting active version: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def set_active_version(self, prompt_id: int, version_id: int) -> Dict[str, Any]:
        """Set a version as active"""
        try:
            success = self.repo.set_active_version(prompt_id, version_id)
            if success:
                return {
                    'success': True,
                    'message': f'Version {version_id} set as active'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to set active version'
                }
        except Exception as e:
            logger.error(f"Error setting active version: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new prompt category"""
        try:
            # Validate required fields
            required_fields = ['name', 'created_by']
            for field in required_fields:
                if field not in category_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create PromptCategory object
            category = PromptCategory(
                name=category_data['name'],
                description=category_data.get('description'),
                color=category_data.get('color'),
                created_by=category_data['created_by']
            )
            
            # Save to database
            category_id = self.repo.create_category(category)
            if category_id:
                category.id = category_id
                return {
                    'success': True,
                    'category_id': category_id,
                    'category': asdict(category),
                    'message': 'Prompt category created successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create prompt category'
                }
        
        except Exception as e:
            logger.error(f"Error creating prompt category: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_categories(self) -> Dict[str, Any]:
        """Get all prompt categories"""
        try:
            categories = self.repo.get_categories()
            return {
                'success': True,
                'categories': [asdict(c) for c in categories],
                'count': len(categories)
            }
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Initialize service
prompt_service = PromptService()


@prompt_bp.route('/versions', methods=['POST'])
def create_version():
    """Create a new prompt version"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        result = prompt_service.create_prompt_version(data)
        status_code = 201 if result['success'] else 400
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error in create_version endpoint: {e}")
        # Handle Flask JSON parsing errors as 400 Bad Request
        if "Bad Request" in str(e) and "could not understand" in str(e):
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@prompt_bp.route('/<int:prompt_id>/versions', methods=['GET'])
def get_versions(prompt_id: int):
    """Get all versions for a prompt"""
    try:
        result = prompt_service.get_prompt_versions(prompt_id)
        status_code = 200 if result['success'] else 404
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error in get_versions endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@prompt_bp.route('/<int:prompt_id>/versions/active', methods=['GET'])
def get_active_version(prompt_id: int):
    """Get active version for a prompt"""
    try:
        result = prompt_service.get_active_version(prompt_id)
        status_code = 200 if result['success'] else 404
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error in get_active_version endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@prompt_bp.route('/<int:prompt_id>/versions/<int:version_id>/activate', methods=['POST'])
def activate_version(prompt_id: int, version_id: int):
    """Set a version as active"""
    try:
        result = prompt_service.set_active_version(prompt_id, version_id)
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error in activate_version endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@prompt_bp.route('/categories', methods=['POST'])
def create_category():
    """Create a new prompt category"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        result = prompt_service.create_category(data)
        status_code = 201 if result['success'] else 400
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error in create_category endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@prompt_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all prompt categories"""
    try:
        result = prompt_service.get_categories()
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error in get_categories endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


# Template processing functionality
class PromptTemplateProcessor:
    """Process prompt templates with variable substitution"""
    
    @staticmethod
    def process_template(content: str, variables: Dict[str, Any]) -> str:
        """Process a prompt template with variables"""
        try:
            # Simple variable substitution using string formatting
            # Variables in format {variable_name}
            processed_content = content
            
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                processed_content = processed_content.replace(placeholder, str(value))
            
            return processed_content
        
        except Exception as e:
            logger.error(f"Error processing template: {e}")
            raise ValueError(f"Template processing failed: {e}")
    
    @staticmethod
    def extract_variables(content: str) -> List[str]:
        """Extract variable names from template content"""
        import re
        try:
            # Find all variables in {variable_name} format
            pattern = r'\{([^}]+)\}'
            variables = re.findall(pattern, content)
            return list(set(variables))  # Remove duplicates
        
        except Exception as e:
            logger.error(f"Error extracting variables: {e}")
            return []
    
    @staticmethod
    def validate_variables(content: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that all required variables are provided"""
        required_vars = PromptTemplateProcessor.extract_variables(content)
        provided_vars = list(variables.keys())
        
        missing_vars = [var for var in required_vars if var not in provided_vars]
        extra_vars = [var for var in provided_vars if var not in required_vars]
        
        return {
            'valid': len(missing_vars) == 0,
            'required_variables': required_vars,
            'provided_variables': provided_vars,
            'missing_variables': missing_vars,
            'extra_variables': extra_vars
        }


@prompt_bp.route('/template/process', methods=['POST'])
def process_template():
    """Process a prompt template with variables"""
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing content field'
            }), 400
        
        content = data['content']
        variables = data.get('variables', {})
        
        # Validate variables
        validation = PromptTemplateProcessor.validate_variables(content, variables)
        if not validation['valid']:
            return jsonify({
                'success': False,
                'error': 'Missing required variables',
                'validation': validation
            }), 400
        
        # Process template
        processed_content = PromptTemplateProcessor.process_template(content, variables)
        
        return jsonify({
            'success': True,
            'processed_content': processed_content,
            'validation': validation
        }), 200
    
    except Exception as e:
        logger.error(f"Error in process_template endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@prompt_bp.route('/template/variables', methods=['POST'])
def extract_template_variables():
    """Extract variables from template content"""
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing content field'
            }), 400
        
        content = data['content']
        variables = PromptTemplateProcessor.extract_variables(content)
        
        return jsonify({
            'success': True,
            'variables': variables,
            'count': len(variables)
        }), 200
    
    except Exception as e:
        logger.error(f"Error in extract_template_variables endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Export/Import functionality
class PromptExportImport:
    """Handle prompt export and import operations"""
    
    @staticmethod
    def export_prompt_data(prompt_id: int, include_versions: bool = True) -> Dict[str, Any]:
        """Export prompt data including versions"""
        try:
            db = get_db_connection()
            
            # Get base prompt data
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM prompt WHERE id = %s", (prompt_id,))
                prompt_data = cursor.fetchone()
                
                if not prompt_data:
                    raise ValueError(f"Prompt {prompt_id} not found")
            
            export_data = {
                'prompt': dict(prompt_data),
                'export_timestamp': int(time.time() * 1000),
                'export_version': '1.0'
            }
            
            if include_versions:
                repo = PromptRepository()
                versions = repo.get_versions_by_prompt_id(prompt_id)
                export_data['versions'] = [asdict(v) for v in versions]
            
            return {
                'success': True,
                'data': export_data
            }
        
        except Exception as e:
            logger.error(f"Error exporting prompt data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def import_prompt_data(import_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Import prompt data"""
        try:
            if 'prompt' not in import_data:
                raise ValueError("Missing prompt data in import")
            
            prompt_data = import_data['prompt']
            versions_data = import_data.get('versions', [])
            
            db = get_db_connection()
            repo = PromptRepository()
            
            # Create new prompt (basic implementation)
            with db.get_transaction() as cursor:
                cursor.execute("""
                    INSERT INTO prompt (command, user_id, title, content, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    f"imported_{int(time.time())}",
                    user_id,
                    prompt_data.get('title', 'Imported Prompt'),
                    prompt_data.get('content', ''),
                    int(time.time() * 1000)
                ))
                
                new_prompt = cursor.fetchone()
                new_prompt_id = new_prompt['id']
            
            # Import versions
            imported_versions = []
            for version_data in versions_data:
                version = PromptVersion(
                    prompt_id=new_prompt_id,
                    version_number=version_data.get('version_number', 1),
                    title=version_data.get('title', 'Imported Version'),
                    content=version_data.get('content', ''),
                    variables=version_data.get('variables', {}),
                    created_by=user_id
                )
                
                version_id = repo.create_version(version)
                if version_id:
                    imported_versions.append(version_id)
            
            return {
                'success': True,
                'prompt_id': new_prompt_id,
                'imported_versions': imported_versions,
                'message': 'Prompt imported successfully'
            }
        
        except Exception as e:
            logger.error(f"Error importing prompt data: {e}")
            return {
                'success': False,
                'error': str(e)
            }


@prompt_bp.route('/<int:prompt_id>/export', methods=['GET'])
def export_prompt(prompt_id: int):
    """Export prompt data"""
    try:
        include_versions = request.args.get('include_versions', 'true').lower() == 'true'
        result = PromptExportImport.export_prompt_data(prompt_id, include_versions)
        
        status_code = 200 if result['success'] else 404
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error in export_prompt endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@prompt_bp.route('/import', methods=['POST'])
def import_prompt():
    """Import prompt data"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Missing user_id'}), 400
        
        import_data = data.get('data')
        if not import_data:
            return jsonify({'success': False, 'error': 'Missing import data'}), 400
        
        result = PromptExportImport.import_prompt_data(import_data, user_id)
        status_code = 201 if result['success'] else 400
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f"Error in import_prompt endpoint: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


def register_prompt_routes(app: Flask):
    """Register prompt management routes with Flask app"""
    app.register_blueprint(prompt_bp)