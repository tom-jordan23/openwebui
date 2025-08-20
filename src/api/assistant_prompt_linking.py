"""
Assistant-Prompt Linking API
Manages relationships between assistants and prompts, including version mapping and fallback configurations
"""

import logging
import json
import time
from typing import List, Dict, Optional, Any, Union
from functools import wraps
from flask import Blueprint, request, jsonify, g

from ..database.connection import get_db_connection
from ..database.assistant_repositories import AssistantRepository
from ..database.assistant_models import AssistantProfile

logger = logging.getLogger(__name__)

# Create Blueprint
assistant_prompt_bp = Blueprint('assistant_prompt_linking', __name__, url_prefix='/api/v1/assistants')


class AssistantPromptService:
    """Service for managing assistant-prompt relationships"""
    
    def __init__(self):
        self.db = get_db_connection()
        self.assistant_repo = AssistantRepository()
    
    def link_prompt_to_assistant(self, assistant_id: str, prompt_id: int, prompt_version_id: Optional[int] = None, 
                                mapping_type: str = 'secondary', priority: int = 0, conditions: Dict[str, Any] = None) -> tuple[bool, str]:
        """Link a prompt to an assistant with specific configuration"""
        try:
            with self.db.get_transaction() as cursor:
                # Verify assistant exists
                assistant = self.assistant_repo.get_by_id(assistant_id)
                if not assistant:
                    return False, "Assistant not found"
                
                # Verify prompt exists
                cursor.execute("SELECT id FROM prompt WHERE id = %s", (prompt_id,))
                if not cursor.fetchone():
                    return False, "Prompt not found"
                
                # Verify prompt version if specified
                if prompt_version_id:
                    cursor.execute("SELECT id FROM prompt_version WHERE id = %s AND prompt_id = %s", 
                                 (prompt_version_id, prompt_id))
                    if not cursor.fetchone():
                        return False, "Prompt version not found or doesn't belong to the specified prompt"
                
                # Check if mapping already exists
                cursor.execute("""
                    SELECT assistant_id FROM assistant_prompt_mapping 
                    WHERE assistant_id = %s AND prompt_id = %s
                """, (assistant_id, prompt_id))
                
                if cursor.fetchone():
                    return False, "Prompt already linked to this assistant"
                
                # If this is a primary prompt, update assistant record
                if mapping_type == 'primary':
                    # Remove existing primary mapping
                    cursor.execute("""
                        UPDATE assistant_prompt_mapping 
                        SET mapping_type = 'secondary' 
                        WHERE assistant_id = %s AND mapping_type = 'primary'
                    """, (assistant_id,))
                    
                    # Update assistant's primary prompt fields
                    cursor.execute("""
                        UPDATE ai_assistant 
                        SET primary_prompt_id = %s, prompt_version_id = %s, updated_at = %s
                        WHERE id = %s
                    """, (prompt_id, prompt_version_id, int(time.time() * 1000), assistant_id))
                
                # Create the mapping
                cursor.execute("""
                    INSERT INTO assistant_prompt_mapping (
                        assistant_id, prompt_id, prompt_version_id, 
                        mapping_type, priority, conditions
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    assistant_id, prompt_id, prompt_version_id,
                    mapping_type, priority, json.dumps(conditions or {})
                ))
                
                return True, "Prompt linked successfully"
                
        except Exception as e:
            logger.error(f"Error linking prompt {prompt_id} to assistant {assistant_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def unlink_prompt_from_assistant(self, assistant_id: str, prompt_id: int) -> tuple[bool, str]:
        """Remove prompt link from assistant"""
        try:
            with self.db.get_transaction() as cursor:
                # Check if mapping exists
                cursor.execute("""
                    SELECT mapping_type FROM assistant_prompt_mapping 
                    WHERE assistant_id = %s AND prompt_id = %s
                """, (assistant_id, prompt_id))
                
                result = cursor.fetchone()
                if not result:
                    return False, "Prompt link not found"
                
                mapping_type = result['mapping_type']
                
                # If removing primary prompt, clear assistant's primary fields
                if mapping_type == 'primary':
                    cursor.execute("""
                        UPDATE ai_assistant 
                        SET primary_prompt_id = NULL, prompt_version_id = NULL, updated_at = %s
                        WHERE id = %s
                    """, (int(time.time() * 1000), assistant_id))
                
                # Remove the mapping
                cursor.execute("""
                    DELETE FROM assistant_prompt_mapping 
                    WHERE assistant_id = %s AND prompt_id = %s
                """, (assistant_id, prompt_id))
                
                return True, "Prompt unlinked successfully"
                
        except Exception as e:
            logger.error(f"Error unlinking prompt {prompt_id} from assistant {assistant_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def get_assistant_prompts(self, assistant_id: str) -> tuple[bool, Union[List[Dict[str, Any]], str]]:
        """Get all prompts linked to an assistant"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        apm.prompt_id,
                        apm.prompt_version_id,
                        apm.mapping_type,
                        apm.priority,
                        apm.conditions,
                        apm.created_at as linked_at,
                        p.title as prompt_title,
                        p.description as prompt_description,
                        p.category_id,
                        p.created_by as prompt_creator,
                        pv.version_number,
                        pv.title as version_title,
                        pv.is_active as version_is_active,
                        pc.name as category_name,
                        pc.color as category_color
                    FROM assistant_prompt_mapping apm
                    JOIN prompt p ON apm.prompt_id = p.id
                    LEFT JOIN prompt_version pv ON apm.prompt_version_id = pv.id
                    LEFT JOIN prompt_category pc ON p.category_id = pc.id
                    WHERE apm.assistant_id = %s
                    ORDER BY apm.mapping_type DESC, apm.priority DESC, apm.created_at ASC
                """, (assistant_id,))
                
                rows = cursor.fetchall()
                
                prompts = []
                for row in rows:
                    prompt_data = {
                        'prompt_id': row['prompt_id'],
                        'prompt_version_id': row['prompt_version_id'],
                        'mapping_type': row['mapping_type'],
                        'priority': row['priority'],
                        'conditions': json.loads(row['conditions']) if row['conditions'] else {},
                        'linked_at': row['linked_at'],
                        'prompt': {
                            'title': row['prompt_title'],
                            'description': row['prompt_description'],
                            'category_id': row['category_id'],
                            'creator': row['prompt_creator']
                        },
                        'version': {
                            'number': row['version_number'],
                            'title': row['version_title'],
                            'is_active': row['version_is_active']
                        } if row['version_number'] else None,
                        'category': {
                            'name': row['category_name'],
                            'color': row['category_color']
                        } if row['category_name'] else None
                    }
                    prompts.append(prompt_data)
                
                return True, prompts
                
        except Exception as e:
            logger.error(f"Error getting prompts for assistant {assistant_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def update_prompt_link(self, assistant_id: str, prompt_id: int, update_data: Dict[str, Any]) -> tuple[bool, str]:
        """Update prompt link configuration"""
        try:
            with self.db.get_transaction() as cursor:
                # Check if mapping exists
                cursor.execute("""
                    SELECT mapping_type FROM assistant_prompt_mapping 
                    WHERE assistant_id = %s AND prompt_id = %s
                """, (assistant_id, prompt_id))
                
                if not cursor.fetchone():
                    return False, "Prompt link not found"
                
                # Build update query dynamically
                update_fields = []
                params = []
                
                if 'prompt_version_id' in update_data:
                    update_fields.append("prompt_version_id = %s")
                    params.append(update_data['prompt_version_id'])
                
                if 'mapping_type' in update_data:
                    new_type = update_data['mapping_type']
                    if new_type not in ['primary', 'secondary', 'fallback']:
                        return False, "Invalid mapping type"
                    
                    # If changing to primary, remove existing primary
                    if new_type == 'primary':
                        cursor.execute("""
                            UPDATE assistant_prompt_mapping 
                            SET mapping_type = 'secondary' 
                            WHERE assistant_id = %s AND mapping_type = 'primary'
                        """, (assistant_id,))
                        
                        # Update assistant's primary prompt fields
                        version_id = update_data.get('prompt_version_id')
                        cursor.execute("""
                            UPDATE ai_assistant 
                            SET primary_prompt_id = %s, prompt_version_id = %s, updated_at = %s
                            WHERE id = %s
                        """, (prompt_id, version_id, int(time.time() * 1000), assistant_id))
                    
                    update_fields.append("mapping_type = %s")
                    params.append(new_type)
                
                if 'priority' in update_data:
                    update_fields.append("priority = %s")
                    params.append(update_data['priority'])
                
                if 'conditions' in update_data:
                    update_fields.append("conditions = %s")
                    params.append(json.dumps(update_data['conditions']))
                
                if not update_fields:
                    return False, "No fields to update"
                
                # Execute update
                params.extend([assistant_id, prompt_id])
                query = f"""
                    UPDATE assistant_prompt_mapping 
                    SET {', '.join(update_fields)}
                    WHERE assistant_id = %s AND prompt_id = %s
                """
                
                cursor.execute(query, params)
                
                return True, "Prompt link updated successfully"
                
        except Exception as e:
            logger.error(f"Error updating prompt link: {e}")
            return False, f"Internal error: {str(e)}"
    
    def get_prompt_assistants(self, prompt_id: int) -> tuple[bool, Union[List[Dict[str, Any]], str]]:
        """Get all assistants using a specific prompt"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        apm.assistant_id,
                        apm.mapping_type,
                        apm.priority,
                        apm.created_at as linked_at,
                        a.name as assistant_name,
                        a.description as assistant_description,
                        a.assistant_type,
                        a.status,
                        a.version as assistant_version,
                        a.user_satisfaction_rating,
                        a.total_conversations,
                        a.user_id as creator_id
                    FROM assistant_prompt_mapping apm
                    JOIN ai_assistant a ON apm.assistant_id = a.id
                    WHERE apm.prompt_id = %s AND a.is_active = TRUE
                    ORDER BY apm.mapping_type DESC, apm.priority DESC, a.user_satisfaction_rating DESC
                """, (prompt_id,))
                
                rows = cursor.fetchall()
                
                assistants = []
                for row in rows:
                    assistant_data = {
                        'assistant_id': row['assistant_id'],
                        'mapping_type': row['mapping_type'],
                        'priority': row['priority'],
                        'linked_at': row['linked_at'],
                        'assistant': {
                            'name': row['assistant_name'],
                            'description': row['assistant_description'],
                            'type': row['assistant_type'],
                            'status': row['status'],
                            'version': row['assistant_version'],
                            'satisfaction_rating': row['user_satisfaction_rating'],
                            'total_conversations': row['total_conversations'],
                            'creator_id': row['creator_id']
                        }
                    }
                    assistants.append(assistant_data)
                
                return True, assistants
                
        except Exception as e:
            logger.error(f"Error getting assistants for prompt {prompt_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def get_prompt_suggestions(self, assistant_id: str, limit: int = 10) -> tuple[bool, Union[List[Dict[str, Any]], str]]:
        """Get prompt suggestions for an assistant based on type and usage patterns"""
        try:
            with self.db.get_cursor() as cursor:
                # Get assistant info
                assistant = self.assistant_repo.get_by_id(assistant_id)
                if not assistant:
                    return False, "Assistant not found"
                
                # Get prompts that might be suitable for this assistant type
                cursor.execute("""
                    SELECT DISTINCT
                        p.id,
                        p.title,
                        p.description,
                        p.category_id,
                        pc.name as category_name,
                        pc.color as category_color,
                        COUNT(apm.assistant_id) as usage_count,
                        AVG(a.user_satisfaction_rating) as avg_satisfaction
                    FROM prompt p
                    LEFT JOIN prompt_category pc ON p.category_id = pc.id
                    LEFT JOIN assistant_prompt_mapping apm ON p.id = apm.prompt_id
                    LEFT JOIN ai_assistant a ON apm.assistant_id = a.id AND a.assistant_type = %s
                    WHERE p.id NOT IN (
                        SELECT prompt_id FROM assistant_prompt_mapping WHERE assistant_id = %s
                    )
                    AND p.is_active = TRUE
                    GROUP BY p.id, p.title, p.description, p.category_id, pc.name, pc.color
                    ORDER BY 
                        CASE WHEN AVG(a.user_satisfaction_rating) IS NOT NULL THEN AVG(a.user_satisfaction_rating) ELSE 0 END DESC,
                        COUNT(apm.assistant_id) DESC,
                        p.created_at DESC
                    LIMIT %s
                """, (assistant.assistant_type.value, assistant_id, limit))
                
                rows = cursor.fetchall()
                
                suggestions = []
                for row in rows:
                    suggestion = {
                        'prompt_id': row['id'],
                        'title': row['title'],
                        'description': row['description'],
                        'category': {
                            'id': row['category_id'],
                            'name': row['category_name'],
                            'color': row['category_color']
                        } if row['category_name'] else None,
                        'usage_stats': {
                            'usage_count': row['usage_count'] or 0,
                            'avg_satisfaction': float(row['avg_satisfaction']) if row['avg_satisfaction'] else 0.0
                        },
                        'relevance_score': self._calculate_relevance_score(
                            row['usage_count'] or 0,
                            row['avg_satisfaction'] or 0
                        )
                    }
                    suggestions.append(suggestion)
                
                return True, suggestions
                
        except Exception as e:
            logger.error(f"Error getting prompt suggestions for assistant {assistant_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def _calculate_relevance_score(self, usage_count: int, avg_satisfaction: float) -> float:
        """Calculate relevance score for prompt suggestions"""
        # Simple scoring algorithm: weight satisfaction more heavily than usage
        return (avg_satisfaction * 0.7) + (min(usage_count / 10.0, 1.0) * 0.3)


# Initialize service
assistant_prompt_service = AssistantPromptService()


def require_user_id(f):
    """Decorator to require user_id in request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({'error': 'User authentication required'}), 401
        g.user_id = user_id
        return f(*args, **kwargs)
    return decorated_function


# API Endpoints
@assistant_prompt_bp.route('/<assistant_id>/prompts', methods=['POST'])
@require_user_id
def link_prompt_to_assistant(assistant_id: str):
    """Link a prompt to an assistant"""
    try:
        data = request.get_json()
        if not data or 'prompt_id' not in data:
            return jsonify({'error': 'prompt_id is required'}), 400
        
        prompt_id = int(data['prompt_id'])
        prompt_version_id = data.get('prompt_version_id')
        mapping_type = data.get('mapping_type', 'secondary')
        priority = data.get('priority', 0)
        conditions = data.get('conditions', {})
        
        if prompt_version_id:
            prompt_version_id = int(prompt_version_id)
        
        # Validate mapping type
        if mapping_type not in ['primary', 'secondary', 'fallback']:
            return jsonify({'error': 'Invalid mapping type'}), 400
        
        success, result = assistant_prompt_service.link_prompt_to_assistant(
            assistant_id, prompt_id, prompt_version_id, mapping_type, priority, conditions
        )
        
        if success:
            return jsonify({'message': result}), 201
        else:
            return jsonify({'error': result}), 400
            
    except (ValueError, TypeError) as e:
        return jsonify({'error': 'Invalid data format'}), 400
    except Exception as e:
        logger.error(f"Error in link_prompt_to_assistant endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@assistant_prompt_bp.route('/<assistant_id>/prompts/<int:prompt_id>', methods=['DELETE'])
@require_user_id
def unlink_prompt_from_assistant(assistant_id: str, prompt_id: int):
    """Remove prompt link from assistant"""
    try:
        success, result = assistant_prompt_service.unlink_prompt_from_assistant(assistant_id, prompt_id)
        
        if success:
            return jsonify({'message': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in unlink_prompt_from_assistant endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@assistant_prompt_bp.route('/<assistant_id>/prompts', methods=['GET'])
def get_assistant_prompts(assistant_id: str):
    """Get all prompts linked to an assistant"""
    try:
        success, result = assistant_prompt_service.get_assistant_prompts(assistant_id)
        
        if success:
            return jsonify({'prompts': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in get_assistant_prompts endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@assistant_prompt_bp.route('/<assistant_id>/prompts/<int:prompt_id>', methods=['PUT'])
@require_user_id
def update_prompt_link(assistant_id: str, prompt_id: int):
    """Update prompt link configuration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        success, result = assistant_prompt_service.update_prompt_link(assistant_id, prompt_id, data)
        
        if success:
            return jsonify({'message': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in update_prompt_link endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@assistant_prompt_bp.route('/<assistant_id>/prompts/suggestions', methods=['GET'])
def get_prompt_suggestions(assistant_id: str):
    """Get prompt suggestions for an assistant"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)  # Max 50 suggestions
        
        success, result = assistant_prompt_service.get_prompt_suggestions(assistant_id, limit)
        
        if success:
            return jsonify({'suggestions': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in get_prompt_suggestions endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@assistant_prompt_bp.route('/prompts/<int:prompt_id>/assistants', methods=['GET'])
def get_prompt_assistants(prompt_id: int):
    """Get all assistants using a specific prompt"""
    try:
        success, result = assistant_prompt_service.get_prompt_assistants(prompt_id)
        
        if success:
            return jsonify({'assistants': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in get_prompt_assistants endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500