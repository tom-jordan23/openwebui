"""
AI Assistant Management API
Provides CRUD operations and management functionality for the Assistant Framework
"""

import logging
import time
import json
from typing import List, Dict, Optional, Any, Union
from functools import wraps
from flask import Blueprint, request, jsonify, g

from ..database.assistant_repositories import (
    AssistantRepository, 
    AssistantDeploymentRepository, 
    ConversationContextRepository,
    AssistantAnalyticsRepository
)
from ..database.assistant_models import (
    AssistantProfile, AssistantDeployment, ConversationContext,
    AssistantStatus, AssistantType, DeploymentEnvironment
)

logger = logging.getLogger(__name__)

# Create Blueprint
assistant_bp = Blueprint('assistant_management', __name__, url_prefix='/api/v1/assistants')


class AssistantService:
    """Core service for assistant management operations"""
    
    def __init__(self):
        self.assistant_repo = AssistantRepository()
        self.deployment_repo = AssistantDeploymentRepository()
        self.context_repo = ConversationContextRepository()
        self.analytics_repo = AssistantAnalyticsRepository()
    
    def create_assistant(self, assistant_data: Dict[str, Any], user_id: str) -> tuple[bool, Union[AssistantProfile, str]]:
        """Create a new AI assistant"""
        try:
            # Validate required fields
            required_fields = ['name', 'description', 'system_prompt', 'model_id']
            for field in required_fields:
                if field not in assistant_data or not assistant_data[field]:
                    return False, f"Missing required field: {field}"
            
            # Parse assistant type and status
            assistant_type = AssistantType.GENERAL
            if 'assistant_type' in assistant_data:
                try:
                    assistant_type = AssistantType(assistant_data['assistant_type'])
                except ValueError:
                    return False, f"Invalid assistant type: {assistant_data['assistant_type']}"
            
            status = AssistantStatus.DRAFT
            if 'status' in assistant_data:
                try:
                    status = AssistantStatus(assistant_data['status'])
                except ValueError:
                    return False, f"Invalid status: {assistant_data['status']}"
            
            # Create assistant profile
            assistant = AssistantProfile(
                name=assistant_data['name'],
                description=assistant_data['description'],
                system_prompt=assistant_data['system_prompt'],
                model_id=assistant_data['model_id'],
                user_id=user_id,
                assistant_type=assistant_type,
                status=status,
                version=assistant_data.get('version', '1.0.0'),
                primary_prompt_id=assistant_data.get('primary_prompt_id'),
                prompt_version_id=assistant_data.get('prompt_version_id'),
                personality_traits=assistant_data.get('personality_traits', {}),
                response_guidelines=assistant_data.get('response_guidelines', {}),
                context_memory_size=assistant_data.get('context_memory_size', 4000),
                temperature=assistant_data.get('temperature', 0.7),
                max_tokens=assistant_data.get('max_tokens', 2000),
                tags=assistant_data.get('tags', []),
                category_ids=assistant_data.get('category_ids', [])
            )
            
            # Save to database
            if self.assistant_repo.create(assistant):
                return True, assistant
            else:
                return False, "Failed to create assistant in database"
                
        except Exception as e:
            logger.error(f"Error creating assistant: {e}")
            return False, f"Internal error: {str(e)}"
    
    def get_assistant(self, assistant_id: str, user_id: str) -> tuple[bool, Union[AssistantProfile, str]]:
        """Get assistant by ID with permission check"""
        try:
            assistant = self.assistant_repo.get_by_id(assistant_id)
            if not assistant:
                return False, "Assistant not found"
            
            # Check permissions (user can access own assistants or public ones)
            if assistant.user_id != user_id:
                # TODO: Add role-based access control for shared assistants
                return False, "Access denied"
            
            return True, assistant
            
        except Exception as e:
            logger.error(f"Error getting assistant {assistant_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def update_assistant(self, assistant_id: str, user_id: str, update_data: Dict[str, Any]) -> tuple[bool, str]:
        """Update assistant with permission check"""
        try:
            # Get existing assistant
            success, result = self.get_assistant(assistant_id, user_id)
            if not success:
                return False, result
            
            assistant = result
            
            # Update fields
            if 'name' in update_data:
                assistant.name = update_data['name']
            if 'description' in update_data:
                assistant.description = update_data['description']
            if 'system_prompt' in update_data:
                assistant.system_prompt = update_data['system_prompt']
            if 'model_id' in update_data:
                assistant.model_id = update_data['model_id']
            if 'assistant_type' in update_data:
                try:
                    assistant.assistant_type = AssistantType(update_data['assistant_type'])
                except ValueError:
                    return False, f"Invalid assistant type: {update_data['assistant_type']}"
            if 'status' in update_data:
                try:
                    assistant.status = AssistantStatus(update_data['status'])
                except ValueError:
                    return False, f"Invalid status: {update_data['status']}"
            if 'version' in update_data:
                assistant.version = update_data['version']
            if 'primary_prompt_id' in update_data:
                assistant.primary_prompt_id = update_data['primary_prompt_id']
            if 'prompt_version_id' in update_data:
                assistant.prompt_version_id = update_data['prompt_version_id']
            if 'personality_traits' in update_data:
                assistant.personality_traits = update_data['personality_traits']
            if 'response_guidelines' in update_data:
                assistant.response_guidelines = update_data['response_guidelines']
            if 'context_memory_size' in update_data:
                assistant.context_memory_size = update_data['context_memory_size']
            if 'temperature' in update_data:
                assistant.temperature = update_data['temperature']
            if 'max_tokens' in update_data:
                assistant.max_tokens = update_data['max_tokens']
            if 'tags' in update_data:
                assistant.tags = update_data['tags']
            if 'category_ids' in update_data:
                assistant.category_ids = update_data['category_ids']
            
            # Save changes
            if self.assistant_repo.update(assistant):
                return True, "Assistant updated successfully"
            else:
                return False, "Failed to update assistant"
                
        except Exception as e:
            logger.error(f"Error updating assistant {assistant_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def delete_assistant(self, assistant_id: str, user_id: str, soft_delete: bool = True) -> tuple[bool, str]:
        """Delete assistant with permission check"""
        try:
            # Check permissions
            success, result = self.get_assistant(assistant_id, user_id)
            if not success:
                return False, result
            
            # Delete assistant
            if self.assistant_repo.delete(assistant_id, soft_delete):
                return True, "Assistant deleted successfully"
            else:
                return False, "Failed to delete assistant"
                
        except Exception as e:
            logger.error(f"Error deleting assistant {assistant_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def list_user_assistants(self, user_id: str, include_archived: bool = False) -> tuple[bool, Union[List[AssistantProfile], str]]:
        """List assistants for a user"""
        try:
            assistants = self.assistant_repo.get_by_user_id(user_id, include_archived)
            return True, assistants
            
        except Exception as e:
            logger.error(f"Error listing assistants for user {user_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def search_assistants(self, query: str, assistant_type: Optional[str] = None, limit: int = 50) -> tuple[bool, Union[List[AssistantProfile], str]]:
        """Search assistants"""
        try:
            type_enum = None
            if assistant_type:
                try:
                    type_enum = AssistantType(assistant_type)
                except ValueError:
                    return False, f"Invalid assistant type: {assistant_type}"
            
            assistants = self.assistant_repo.search(query, type_enum, limit)
            return True, assistants
            
        except Exception as e:
            logger.error(f"Error searching assistants: {e}")
            return False, f"Internal error: {str(e)}"
    
    def get_popular_assistants(self, limit: int = 20) -> tuple[bool, Union[List[AssistantProfile], str]]:
        """Get popular assistants"""
        try:
            assistants = self.assistant_repo.get_popular(limit)
            return True, assistants
            
        except Exception as e:
            logger.error(f"Error getting popular assistants: {e}")
            return False, f"Internal error: {str(e)}"
    
    def clone_assistant(self, source_id: str, new_name: str, user_id: str) -> tuple[bool, Union[str, str]]:
        """Clone an existing assistant"""
        try:
            # Check if source assistant exists and is accessible
            source_assistant = self.assistant_repo.get_by_id(source_id)
            if not source_assistant:
                return False, "Source assistant not found"
            
            # Clone assistant
            new_assistant_id = self.assistant_repo.clone_assistant(source_id, new_name, user_id)
            if new_assistant_id:
                return True, new_assistant_id
            else:
                return False, "Failed to clone assistant"
                
        except Exception as e:
            logger.error(f"Error cloning assistant {source_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def update_usage_stats(self, assistant_id: str, user_id: str, message_count: int, response_time: float, user_rating: Optional[int] = None) -> tuple[bool, str]:
        """Update assistant usage statistics"""
        try:
            # Verify user has access to assistant
            success, result = self.get_assistant(assistant_id, user_id)
            if not success:
                return False, result
            
            # Update stats
            if self.assistant_repo.update_usage_stats(assistant_id, message_count, response_time, user_rating):
                return True, "Usage statistics updated"
            else:
                return False, "Failed to update usage statistics"
                
        except Exception as e:
            logger.error(f"Error updating usage stats for {assistant_id}: {e}")
            return False, f"Internal error: {str(e)}"


# Initialize service
assistant_service = AssistantService()


def require_user_id(f):
    """Decorator to require user_id in request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # In production, this would extract user_id from JWT token
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({'error': 'User authentication required'}), 401
        g.user_id = user_id
        return f(*args, **kwargs)
    return decorated_function


# API Endpoints
@assistant_bp.route('', methods=['POST'])
@require_user_id
def create_assistant():
    """Create a new assistant"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        success, result = assistant_service.create_assistant(data, g.user_id)
        
        if success:
            return jsonify({
                'message': 'Assistant created successfully',
                'assistant': {
                    'id': result.id,
                    'name': result.name,
                    'assistant_type': result.assistant_type.value,
                    'status': result.status.value,
                    'version': result.version,
                    'created_at': result.created_at
                }
            }), 201
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in create_assistant endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@assistant_bp.route('/<assistant_id>', methods=['GET'])
@require_user_id
def get_assistant(assistant_id: str):
    """Get assistant by ID"""
    try:
        success, result = assistant_service.get_assistant(assistant_id, g.user_id)
        
        if success:
            assistant = result
            return jsonify({
                'assistant': {
                    'id': assistant.id,
                    'name': assistant.name,
                    'description': assistant.description,
                    'system_prompt': assistant.system_prompt,
                    'model_id': assistant.model_id,
                    'user_id': assistant.user_id,
                    'assistant_type': assistant.assistant_type.value,
                    'status': assistant.status.value,
                    'version': assistant.version,
                    'primary_prompt_id': assistant.primary_prompt_id,
                    'prompt_version_id': assistant.prompt_version_id,
                    'personality_traits': assistant.personality_traits,
                    'response_guidelines': assistant.response_guidelines,
                    'context_memory_size': assistant.context_memory_size,
                    'temperature': assistant.temperature,
                    'max_tokens': assistant.max_tokens,
                    'total_conversations': assistant.total_conversations,
                    'avg_response_time': assistant.avg_response_time,
                    'user_satisfaction_rating': assistant.user_satisfaction_rating,
                    'tags': assistant.tags,
                    'category_ids': assistant.category_ids,
                    'created_at': assistant.created_at,
                    'updated_at': assistant.updated_at,
                    'is_active': assistant.is_active
                }
            }), 200
        else:
            return jsonify({'error': result}), 404
            
    except Exception as e:
        logger.error(f"Error in get_assistant endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@assistant_bp.route('/<assistant_id>', methods=['PUT'])
@require_user_id
def update_assistant(assistant_id: str):
    """Update assistant"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        success, result = assistant_service.update_assistant(assistant_id, g.user_id, data)
        
        if success:
            return jsonify({'message': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in update_assistant endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@assistant_bp.route('/<assistant_id>', methods=['DELETE'])
@require_user_id
def delete_assistant(assistant_id: str):
    """Delete assistant"""
    try:
        soft_delete = request.args.get('soft', 'true').lower() == 'true'
        
        success, result = assistant_service.delete_assistant(assistant_id, g.user_id, soft_delete)
        
        if success:
            return jsonify({'message': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in delete_assistant endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@assistant_bp.route('', methods=['GET'])
@require_user_id
def list_assistants():
    """List user's assistants"""
    try:
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        
        success, result = assistant_service.list_user_assistants(g.user_id, include_archived)
        
        if success:
            assistants_data = []
            for assistant in result:
                assistants_data.append({
                    'id': assistant.id,
                    'name': assistant.name,
                    'description': assistant.description,
                    'assistant_type': assistant.assistant_type.value,
                    'status': assistant.status.value,
                    'version': assistant.version,
                    'total_conversations': assistant.total_conversations,
                    'user_satisfaction_rating': assistant.user_satisfaction_rating,
                    'tags': assistant.tags,
                    'created_at': assistant.created_at,
                    'updated_at': assistant.updated_at,
                    'is_active': assistant.is_active
                })
            
            return jsonify({'assistants': assistants_data}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in list_assistants endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@assistant_bp.route('/search', methods=['GET'])
def search_assistants():
    """Search assistants"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Search query required'}), 400
        
        assistant_type = request.args.get('type')
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 results
        
        success, result = assistant_service.search_assistants(query, assistant_type, limit)
        
        if success:
            assistants_data = []
            for assistant in result:
                assistants_data.append({
                    'id': assistant.id,
                    'name': assistant.name,
                    'description': assistant.description,
                    'assistant_type': assistant.assistant_type.value,
                    'status': assistant.status.value,
                    'total_conversations': assistant.total_conversations,
                    'user_satisfaction_rating': assistant.user_satisfaction_rating,
                    'tags': assistant.tags,
                    'creator_name': assistant.user_id  # In production, resolve to actual name
                })
            
            return jsonify({'assistants': assistants_data}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in search_assistants endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@assistant_bp.route('/popular', methods=['GET'])
def get_popular_assistants():
    """Get popular assistants"""
    try:
        limit = min(int(request.args.get('limit', 20)), 50)  # Max 50 results
        
        success, result = assistant_service.get_popular_assistants(limit)
        
        if success:
            assistants_data = []
            for assistant in result:
                assistants_data.append({
                    'id': assistant.id,
                    'name': assistant.name,
                    'description': assistant.description,
                    'assistant_type': assistant.assistant_type.value,
                    'total_conversations': assistant.total_conversations,
                    'user_satisfaction_rating': assistant.user_satisfaction_rating,
                    'tags': assistant.tags,
                    'creator_name': assistant.user_id  # In production, resolve to actual name
                })
            
            return jsonify({'assistants': assistants_data}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in get_popular_assistants endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@assistant_bp.route('/<source_id>/clone', methods=['POST'])
@require_user_id
def clone_assistant(source_id: str):
    """Clone an assistant"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'New assistant name required'}), 400
        
        new_name = data['name'].strip()
        if not new_name:
            return jsonify({'error': 'Assistant name cannot be empty'}), 400
        
        success, result = assistant_service.clone_assistant(source_id, new_name, g.user_id)
        
        if success:
            return jsonify({
                'message': 'Assistant cloned successfully',
                'new_assistant_id': result
            }), 201
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in clone_assistant endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@assistant_bp.route('/<assistant_id>/usage', methods=['POST'])
@require_user_id
def update_usage_stats(assistant_id: str):
    """Update assistant usage statistics"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if 'message_count' not in data or 'response_time' not in data:
            return jsonify({'error': 'message_count and response_time are required'}), 400
        
        message_count = int(data['message_count'])
        response_time = float(data['response_time'])
        user_rating = data.get('user_rating')
        
        if user_rating is not None:
            user_rating = int(user_rating)
            if not 1 <= user_rating <= 5:
                return jsonify({'error': 'User rating must be between 1 and 5'}), 400
        
        success, result = assistant_service.update_usage_stats(
            assistant_id, g.user_id, message_count, response_time, user_rating
        )
        
        if success:
            return jsonify({'message': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except (ValueError, TypeError) as e:
        return jsonify({'error': 'Invalid data format'}), 400
    except Exception as e:
        logger.error(f"Error in update_usage_stats endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@assistant_bp.route('/types', methods=['GET'])
def get_assistant_types():
    """Get available assistant types"""
    try:
        types = [{'value': t.value, 'name': t.value.replace('_', ' ').title()} for t in AssistantType]
        return jsonify({'types': types}), 200
    except Exception as e:
        logger.error(f"Error in get_assistant_types endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@assistant_bp.route('/statuses', methods=['GET'])
def get_assistant_statuses():
    """Get available assistant statuses"""
    try:
        statuses = [{'value': s.value, 'name': s.value.replace('_', ' ').title()} for s in AssistantStatus]
        return jsonify({'statuses': statuses}), 200
    except Exception as e:
        logger.error(f"Error in get_assistant_statuses endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500