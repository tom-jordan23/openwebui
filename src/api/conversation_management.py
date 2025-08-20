"""
Conversation Management API
Handles conversation sessions, context management, and message routing for AI assistants
"""

import logging
import time
import json
import uuid
from typing import List, Dict, Optional, Any, Union
from functools import wraps
from flask import Blueprint, request, jsonify, g

from ..database.assistant_repositories import (
    AssistantRepository,
    ConversationContextRepository,
    AssistantAnalyticsRepository
)
from ..database.assistant_models import (
    AssistantProfile, ConversationContext
)

logger = logging.getLogger(__name__)

# Create Blueprint
conversation_bp = Blueprint('conversation_management', __name__, url_prefix='/api/v1/conversations')


class ConversationService:
    """Core service for conversation management operations"""
    
    def __init__(self):
        self.assistant_repo = AssistantRepository()
        self.context_repo = ConversationContextRepository()
        self.analytics_repo = AssistantAnalyticsRepository()
    
    def start_conversation(self, assistant_id: str, user_id: str, initial_message: Optional[str] = None) -> tuple[bool, Union[ConversationContext, str]]:
        """Start a new conversation session with an assistant"""
        try:
            # Verify assistant exists and is active
            assistant = self.assistant_repo.get_by_id(assistant_id)
            if not assistant:
                return False, "Assistant not found"
            
            if not assistant.is_active:
                return False, "Assistant is not active"
            
            # Create new conversation context
            session_id = str(uuid.uuid4())
            context = ConversationContext(
                session_id=session_id,
                assistant_id=assistant_id,
                user_id=user_id,
                max_context_length=assistant.context_memory_size,
                active_prompt_id=assistant.primary_prompt_id
            )
            
            # Add system message if assistant has system prompt
            if assistant.system_prompt:
                context.add_message('system', assistant.system_prompt, {
                    'prompt_id': assistant.primary_prompt_id,
                    'prompt_version_id': assistant.prompt_version_id
                })
            
            # Add initial user message if provided
            if initial_message:
                context.add_message('user', initial_message)
            
            # Save context to database
            if self.context_repo.create_context(context):
                return True, context
            else:
                return False, "Failed to create conversation context"
                
        except Exception as e:
            logger.error(f"Error starting conversation with assistant {assistant_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def get_conversation(self, session_id: str, user_id: str) -> tuple[bool, Union[ConversationContext, str]]:
        """Get conversation context with permission check"""
        try:
            context = self.context_repo.get_by_session_id(session_id)
            if not context:
                return False, "Conversation not found"
            
            # Check permissions
            if context.user_id != user_id:
                return False, "Access denied"
            
            return True, context
            
        except Exception as e:
            logger.error(f"Error getting conversation {session_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def add_message(self, session_id: str, user_id: str, role: str, content: str, 
                    metadata: Dict[str, Any] = None, response_time: Optional[float] = None, 
                    tokens_used: int = 0) -> tuple[bool, Union[ConversationContext, str]]:
        """Add a message to an existing conversation"""
        try:
            # Get conversation context
            success, result = self.get_conversation(session_id, user_id)
            if not success:
                return False, result
            
            context = result
            
            # Validate role
            if role not in ['user', 'assistant', 'system']:
                return False, "Invalid message role"
            
            # Add message to context
            context.add_message(role, content, metadata)
            
            # Update performance metrics if this is an assistant response
            if role == 'assistant' and response_time is not None:
                context.update_performance_metrics(response_time, tokens_used)
            
            # Save updated context
            if self.context_repo.update_context(context):
                # Record analytics if assistant response
                if role == 'assistant':
                    self._record_conversation_analytics(context, response_time, tokens_used)
                
                return True, context
            else:
                return False, "Failed to update conversation"
                
        except Exception as e:
            logger.error(f"Error adding message to conversation {session_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def get_conversation_history(self, session_id: str, user_id: str, limit: Optional[int] = None) -> tuple[bool, Union[List[Dict[str, Any]], str]]:
        """Get conversation message history"""
        try:
            success, result = self.get_conversation(session_id, user_id)
            if not success:
                return False, result
            
            context = result
            history = context.conversation_history.copy()
            
            # Apply limit if specified
            if limit and limit > 0:
                history = history[-limit:]
            
            return True, history
            
        except Exception as e:
            logger.error(f"Error getting conversation history {session_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def update_context_variables(self, session_id: str, user_id: str, variables: Dict[str, Any]) -> tuple[bool, str]:
        """Update context variables for a conversation"""
        try:
            success, result = self.get_conversation(session_id, user_id)
            if not success:
                return False, result
            
            context = result
            
            # Update context variables
            context.context_variables.update(variables)
            
            # Save updated context
            if self.context_repo.update_context(context):
                return True, "Context variables updated successfully"
            else:
                return False, "Failed to update context variables"
                
        except Exception as e:
            logger.error(f"Error updating context variables for {session_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def end_conversation(self, session_id: str, user_id: str, user_rating: Optional[int] = None) -> tuple[bool, str]:
        """End a conversation session"""
        try:
            success, result = self.get_conversation(session_id, user_id)
            if not success:
                return False, result
            
            context = result
            
            # Update assistant usage statistics
            message_count = len([msg for msg in context.conversation_history if msg['role'] in ['user', 'assistant']])
            if message_count > 0:
                self.assistant_repo.update_usage_stats(
                    context.assistant_id,
                    message_count // 2,  # Conversation pairs
                    context.avg_response_time,
                    user_rating
                )
            
            # Record final analytics
            if user_rating:
                self.analytics_repo.record_metric(
                    context.assistant_id,
                    'user_satisfaction',
                    user_rating,
                    'conversation'
                )
            
            # Clean up old contexts (optional - could be done by background job)
            self.context_repo.cleanup_old_contexts(30)  # Clean up contexts older than 30 days
            
            return True, "Conversation ended successfully"
            
        except Exception as e:
            logger.error(f"Error ending conversation {session_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def get_active_sessions(self, user_id: str, hours: int = 24) -> tuple[bool, Union[List[Dict[str, Any]], str]]:
        """Get active conversation sessions for a user"""
        try:
            cutoff_time = int((time.time() - hours * 3600) * 1000)
            
            # Get all assistants for the user
            user_assistants = self.assistant_repo.get_by_user_id(user_id, include_archived=False)
            assistant_ids = [assistant.id for assistant in user_assistants]
            
            if not assistant_ids:
                return True, []
            
            active_sessions = []
            for assistant_id in assistant_ids:
                sessions = self.context_repo.get_active_sessions(assistant_id, hours)
                for session in sessions:
                    if session.user_id == user_id:  # Double-check permissions
                        session_data = {
                            'session_id': session.session_id,
                            'assistant_id': session.assistant_id,
                            'started_at': session.started_at,
                            'last_interaction': session.last_interaction,
                            'interaction_count': session.interaction_count,
                            'message_count': len(session.conversation_history),
                            'avg_response_time': session.avg_response_time,
                            'assistant_name': next((a.name for a in user_assistants if a.id == session.assistant_id), 'Unknown')
                        }
                        active_sessions.append(session_data)
            
            # Sort by last interaction
            active_sessions.sort(key=lambda x: x['last_interaction'], reverse=True)
            
            return True, active_sessions
            
        except Exception as e:
            logger.error(f"Error getting active sessions for user {user_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def get_conversation_summary(self, session_id: str, user_id: str) -> tuple[bool, Union[Dict[str, Any], str]]:
        """Get conversation summary and statistics"""
        try:
            success, result = self.get_conversation(session_id, user_id)
            if not success:
                return False, result
            
            context = result
            
            # Calculate statistics
            user_messages = [msg for msg in context.conversation_history if msg['role'] == 'user']
            assistant_messages = [msg for msg in context.conversation_history if msg['role'] == 'assistant']
            
            duration_minutes = (context.last_interaction - context.started_at) / 60000  # Convert ms to minutes
            
            summary = {
                'session_id': context.session_id,
                'assistant_id': context.assistant_id,
                'started_at': context.started_at,
                'last_interaction': context.last_interaction,
                'duration_minutes': round(duration_minutes, 2),
                'statistics': {
                    'total_messages': len(context.conversation_history),
                    'user_messages': len(user_messages),
                    'assistant_messages': len(assistant_messages),
                    'interaction_count': context.interaction_count,
                    'avg_response_time': context.avg_response_time,
                    'total_tokens_used': context.total_tokens_used,
                    'current_context_length': context.current_context_length,
                    'errors_encountered': context.errors_encountered
                },
                'context_info': {
                    'active_prompt_id': context.active_prompt_id,
                    'max_context_length': context.max_context_length,
                    'compression_enabled': context.context_compression_enabled,
                    'context_variables_count': len(context.context_variables)
                }
            }
            
            return True, summary
            
        except Exception as e:
            logger.error(f"Error getting conversation summary {session_id}: {e}")
            return False, f"Internal error: {str(e)}"
    
    def _record_conversation_analytics(self, context: ConversationContext, response_time: Optional[float], tokens_used: int):
        """Record analytics for conversation interactions"""
        try:
            if response_time:
                self.analytics_repo.record_metric(
                    context.assistant_id,
                    'response_time',
                    response_time,
                    'interaction'
                )
            
            if tokens_used > 0:
                self.analytics_repo.record_metric(
                    context.assistant_id,
                    'tokens_used',
                    tokens_used,
                    'interaction'
                )
            
            # Record conversation length metric
            self.analytics_repo.record_metric(
                context.assistant_id,
                'conversation_length',
                context.interaction_count,
                'session'
            )
            
        except Exception as e:
            logger.error(f"Error recording conversation analytics: {e}")


# Initialize service
conversation_service = ConversationService()


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
@conversation_bp.route('', methods=['POST'])
@require_user_id
def start_conversation():
    """Start a new conversation with an assistant"""
    try:
        data = request.get_json()
        if not data or 'assistant_id' not in data:
            return jsonify({'error': 'assistant_id is required'}), 400
        
        assistant_id = data['assistant_id']
        initial_message = data.get('initial_message')
        
        success, result = conversation_service.start_conversation(assistant_id, g.user_id, initial_message)
        
        if success:
            context = result
            return jsonify({
                'message': 'Conversation started successfully',
                'session_id': context.session_id,
                'assistant_id': context.assistant_id,
                'started_at': context.started_at,
                'max_context_length': context.max_context_length,
                'active_prompt_id': context.active_prompt_id
            }), 201
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in start_conversation endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@conversation_bp.route('/<session_id>', methods=['GET'])
@require_user_id
def get_conversation(session_id: str):
    """Get conversation context"""
    try:
        success, result = conversation_service.get_conversation(session_id, g.user_id)
        
        if success:
            context = result
            return jsonify({
                'session_id': context.session_id,
                'assistant_id': context.assistant_id,
                'started_at': context.started_at,
                'last_interaction': context.last_interaction,
                'interaction_count': context.interaction_count,
                'max_context_length': context.max_context_length,
                'current_context_length': context.current_context_length,
                'context_compression_enabled': context.context_compression_enabled,
                'active_prompt_id': context.active_prompt_id,
                'context_variables': context.context_variables,
                'performance': {
                    'avg_response_time': context.avg_response_time,
                    'total_tokens_used': context.total_tokens_used,
                    'errors_encountered': context.errors_encountered
                }
            }), 200
        else:
            return jsonify({'error': result}), 404
            
    except Exception as e:
        logger.error(f"Error in get_conversation endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@conversation_bp.route('/<session_id>/messages', methods=['POST'])
@require_user_id
def add_message(session_id: str):
    """Add a message to the conversation"""
    try:
        data = request.get_json()
        if not data or 'role' not in data or 'content' not in data:
            return jsonify({'error': 'role and content are required'}), 400
        
        role = data['role']
        content = data['content']
        metadata = data.get('metadata', {})
        response_time = data.get('response_time')
        tokens_used = data.get('tokens_used', 0)
        
        success, result = conversation_service.add_message(
            session_id, g.user_id, role, content, metadata, response_time, tokens_used
        )
        
        if success:
            context = result
            return jsonify({
                'message': 'Message added successfully',
                'interaction_count': context.interaction_count,
                'current_context_length': context.current_context_length,
                'last_interaction': context.last_interaction
            }), 201
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in add_message endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@conversation_bp.route('/<session_id>/messages', methods=['GET'])
@require_user_id
def get_conversation_history(session_id: str):
    """Get conversation message history"""
    try:
        limit = request.args.get('limit')
        if limit:
            limit = int(limit)
        
        success, result = conversation_service.get_conversation_history(session_id, g.user_id, limit)
        
        if success:
            return jsonify({'history': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except (ValueError, TypeError) as e:
        return jsonify({'error': 'Invalid limit parameter'}), 400
    except Exception as e:
        logger.error(f"Error in get_conversation_history endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@conversation_bp.route('/<session_id>/context', methods=['PUT'])
@require_user_id
def update_context_variables(session_id: str):
    """Update context variables for the conversation"""
    try:
        data = request.get_json()
        if not data or 'variables' not in data:
            return jsonify({'error': 'variables object is required'}), 400
        
        variables = data['variables']
        if not isinstance(variables, dict):
            return jsonify({'error': 'variables must be an object'}), 400
        
        success, result = conversation_service.update_context_variables(session_id, g.user_id, variables)
        
        if success:
            return jsonify({'message': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in update_context_variables endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@conversation_bp.route('/<session_id>/end', methods=['POST'])
@require_user_id
def end_conversation(session_id: str):
    """End a conversation session"""
    try:
        data = request.get_json() or {}
        user_rating = data.get('user_rating')
        
        if user_rating is not None:
            user_rating = int(user_rating)
            if not 1 <= user_rating <= 5:
                return jsonify({'error': 'User rating must be between 1 and 5'}), 400
        
        success, result = conversation_service.end_conversation(session_id, g.user_id, user_rating)
        
        if success:
            return jsonify({'message': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except (ValueError, TypeError) as e:
        return jsonify({'error': 'Invalid user rating'}), 400
    except Exception as e:
        logger.error(f"Error in end_conversation endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@conversation_bp.route('/active', methods=['GET'])
@require_user_id
def get_active_sessions():
    """Get active conversation sessions for the user"""
    try:
        hours = int(request.args.get('hours', 24))
        hours = max(1, min(hours, 168))  # Between 1 hour and 1 week
        
        success, result = conversation_service.get_active_sessions(g.user_id, hours)
        
        if success:
            return jsonify({'active_sessions': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except (ValueError, TypeError) as e:
        return jsonify({'error': 'Invalid hours parameter'}), 400
    except Exception as e:
        logger.error(f"Error in get_active_sessions endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@conversation_bp.route('/<session_id>/summary', methods=['GET'])
@require_user_id
def get_conversation_summary(session_id: str):
    """Get conversation summary and statistics"""
    try:
        success, result = conversation_service.get_conversation_summary(session_id, g.user_id)
        
        if success:
            return jsonify({'summary': result}), 200
        else:
            return jsonify({'error': result}), 400
            
    except Exception as e:
        logger.error(f"Error in get_conversation_summary endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500