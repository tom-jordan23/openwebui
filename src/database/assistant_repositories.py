"""
Assistant Framework Repository Classes
Data access layer for the AI Assistant Framework
"""

import time
import json
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from .connection import get_db_connection
from .assistant_models import (
    AssistantProfile, AssistantDeployment, ConversationContext,
    AssistantStatus, AssistantType, DeploymentEnvironment
)

logger = logging.getLogger(__name__)


class AssistantRepository:
    """Repository for AI Assistant operations"""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def create(self, assistant: AssistantProfile) -> bool:
        """Create a new assistant"""
        try:
            with self.db.get_transaction() as cursor:
                assistant_data = assistant.to_dict()
                
                # Extract column names and values
                columns = list(assistant_data.keys())
                placeholders = ', '.join(['%s'] * len(columns))
                values = list(assistant_data.values())
                
                query = f"""
                    INSERT INTO ai_assistant ({', '.join(columns)})
                    VALUES ({placeholders})
                """
                
                cursor.execute(query, values)
                return True
                
        except Exception as e:
            logger.error(f"Failed to create assistant: {e}")
            return False
    
    def get_by_id(self, assistant_id: str) -> Optional[AssistantProfile]:
        """Get assistant by ID"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM ai_assistant WHERE id = %s
                """, (assistant_id,))
                
                row = cursor.fetchone()
                if row:
                    return AssistantProfile.from_db_row(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get assistant {assistant_id}: {e}")
            return None
    
    def get_by_user_id(self, user_id: str, include_archived: bool = False) -> List[AssistantProfile]:
        """Get assistants by user ID"""
        try:
            with self.db.get_cursor() as cursor:
                query = """
                    SELECT * FROM ai_assistant 
                    WHERE user_id = %s
                """
                params = [user_id]
                
                if not include_archived:
                    query += " AND status != %s"
                    params.append(AssistantStatus.ARCHIVED.value)
                
                query += " ORDER BY created_at DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [AssistantProfile.from_db_row(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get assistants for user {user_id}: {e}")
            return []
    
    def get_by_type(self, assistant_type: AssistantType, limit: int = 50) -> List[AssistantProfile]:
        """Get assistants by type"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM ai_assistant 
                    WHERE assistant_type = %s AND is_active = TRUE
                    ORDER BY user_satisfaction_rating DESC, total_conversations DESC
                    LIMIT %s
                """, (assistant_type.value, limit))
                
                rows = cursor.fetchall()
                return [AssistantProfile.from_db_row(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get assistants by type {assistant_type}: {e}")
            return []
    
    def get_popular(self, limit: int = 20) -> List[AssistantProfile]:
        """Get popular assistants based on usage and satisfaction"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM ai_assistant 
                    WHERE is_active = TRUE AND status = %s
                    AND total_conversations > 0
                    ORDER BY (user_satisfaction_rating * 0.7 + (total_conversations / 100.0) * 0.3) DESC
                    LIMIT %s
                """, (AssistantStatus.ACTIVE.value, limit))
                
                rows = cursor.fetchall()
                return [AssistantProfile.from_db_row(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get popular assistants: {e}")
            return []
    
    def search(self, query: str, assistant_type: Optional[AssistantType] = None, 
               limit: int = 50) -> List[AssistantProfile]:
        """Search assistants by name, description, or tags"""
        try:
            with self.db.get_cursor() as cursor:
                search_query = """
                    SELECT * FROM ai_assistant 
                    WHERE is_active = TRUE 
                    AND (
                        name ILIKE %s 
                        OR description ILIKE %s
                        OR tags::text ILIKE %s
                        OR capabilities::text ILIKE %s
                    )
                """
                params = [f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"]
                
                if assistant_type:
                    search_query += " AND assistant_type = %s"
                    params.append(assistant_type.value)
                
                search_query += " ORDER BY user_satisfaction_rating DESC LIMIT %s"
                params.append(limit)
                
                cursor.execute(search_query, params)
                rows = cursor.fetchall()
                
                return [AssistantProfile.from_db_row(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to search assistants: {e}")
            return []
    
    def update(self, assistant: AssistantProfile) -> bool:
        """Update an assistant"""
        try:
            assistant.updated_at = int(time.time() * 1000)
            
            with self.db.get_transaction() as cursor:
                assistant_data = assistant.to_dict()
                
                # Remove id from update data
                assistant_data.pop('id', None)
                
                # Build update query
                set_clauses = [f"{col} = %s" for col in assistant_data.keys()]
                values = list(assistant_data.values())
                values.append(assistant.id)
                
                query = f"""
                    UPDATE ai_assistant 
                    SET {', '.join(set_clauses)}
                    WHERE id = %s
                """
                
                cursor.execute(query, values)
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update assistant {assistant.id}: {e}")
            return False
    
    def delete(self, assistant_id: str, soft_delete: bool = True) -> bool:
        """Delete an assistant (soft delete by default)"""
        try:
            with self.db.get_transaction() as cursor:
                if soft_delete:
                    cursor.execute("""
                        UPDATE ai_assistant 
                        SET status = %s, is_active = FALSE, updated_at = %s
                        WHERE id = %s
                    """, (AssistantStatus.ARCHIVED.value, int(time.time() * 1000), assistant_id))
                else:
                    cursor.execute("DELETE FROM ai_assistant WHERE id = %s", (assistant_id,))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to delete assistant {assistant_id}: {e}")
            return False
    
    def update_usage_stats(self, assistant_id: str, message_count: int, 
                          response_time: float, user_rating: Optional[int] = None) -> bool:
        """Update assistant usage statistics"""
        try:
            with self.db.get_transaction() as cursor:
                cursor.execute(
                    "SELECT update_assistant_usage_stats(%s, %s, %s, %s)",
                    (assistant_id, message_count, response_time, user_rating)
                )
                return True
                
        except Exception as e:
            logger.error(f"Failed to update usage stats for {assistant_id}: {e}")
            return False
    
    def get_deployment_status(self, assistant_id: str) -> List[Dict[str, Any]]:
        """Get deployment status across all environments"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM assistant_deployment_status 
                    WHERE id = %s
                """, (assistant_id,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get deployment status for {assistant_id}: {e}")
            return []
    
    def get_performance_summary(self, assistant_id: str) -> Optional[Dict[str, Any]]:
        """Get performance summary for an assistant"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM assistant_performance_summary 
                    WHERE id = %s
                """, (assistant_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get performance summary for {assistant_id}: {e}")
            return None
    
    def clone_assistant(self, source_id: str, new_name: str, user_id: str) -> Optional[str]:
        """Clone an existing assistant"""
        try:
            # Get source assistant
            source = self.get_by_id(source_id)
            if not source:
                return None
            
            # Create new assistant based on source
            cloned = AssistantProfile(
                name=new_name,
                description=f"Cloned from {source.name}",
                system_prompt=source.system_prompt,
                model_id=source.model_id,
                user_id=user_id,
                assistant_type=source.assistant_type,
                parent_assistant_id=source_id,
                version="1.0.0",
                status=AssistantStatus.DRAFT,
                primary_prompt_id=source.primary_prompt_id,
                prompt_version_id=source.prompt_version_id,
                fallback_prompts=source.fallback_prompts.copy(),
                personality_traits=source.personality_traits.copy(),
                response_guidelines=source.response_guidelines.copy(),
                configuration=source.configuration.copy(),
                capabilities=source.capabilities.copy(),
                tags=source.tags.copy()
            )
            
            if self.create(cloned):
                return cloned.id
            return None
            
        except Exception as e:
            logger.error(f"Failed to clone assistant {source_id}: {e}")
            return None


class AssistantDeploymentRepository:
    """Repository for Assistant Deployment operations"""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def create_deployment(self, deployment: AssistantDeployment) -> bool:
        """Create a new deployment record"""
        try:
            with self.db.get_transaction() as cursor:
                deployment_data = deployment.to_dict()
                
                columns = list(deployment_data.keys())
                placeholders = ', '.join(['%s'] * len(columns))
                values = list(deployment_data.values())
                
                query = f"""
                    INSERT INTO assistant_deployment ({', '.join(columns)})
                    VALUES ({placeholders})
                    RETURNING id
                """
                
                cursor.execute(query, values)
                result = cursor.fetchone()
                if result:
                    deployment.id = result['id']
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Failed to create deployment: {e}")
            return False
    
    def get_deployments(self, assistant_id: str) -> List[AssistantDeployment]:
        """Get all deployments for an assistant"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM assistant_deployment 
                    WHERE assistant_id = %s
                    ORDER BY deployed_at DESC
                """, (assistant_id,))
                
                rows = cursor.fetchall()
                return [AssistantDeployment.from_db_row(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get deployments for {assistant_id}: {e}")
            return []
    
    def get_active_deployment(self, assistant_id: str, 
                            environment: DeploymentEnvironment) -> Optional[AssistantDeployment]:
        """Get active deployment for specific environment"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM assistant_deployment 
                    WHERE assistant_id = %s AND environment = %s AND status = 'active'
                    ORDER BY deployed_at DESC
                    LIMIT 1
                """, (assistant_id, environment.value))
                
                row = cursor.fetchone()
                return AssistantDeployment.from_db_row(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get active deployment: {e}")
            return None
    
    def update_deployment_status(self, deployment_id: int, status: str) -> bool:
        """Update deployment status"""
        try:
            with self.db.get_transaction() as cursor:
                cursor.execute("""
                    UPDATE assistant_deployment 
                    SET status = %s, updated_at = %s
                    WHERE id = %s
                """, (status, int(time.time() * 1000), deployment_id))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update deployment status: {e}")
            return False


class ConversationContextRepository:
    """Repository for Conversation Context operations"""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def create_context(self, context: ConversationContext) -> bool:
        """Create a new conversation context"""
        try:
            with self.db.get_transaction() as cursor:
                context_data = context.to_dict()
                
                columns = list(context_data.keys())
                placeholders = ', '.join(['%s'] * len(columns))
                values = list(context_data.values())
                
                query = f"""
                    INSERT INTO conversation_context ({', '.join(columns)})
                    VALUES ({placeholders})
                    RETURNING id
                """
                
                cursor.execute(query, values)
                result = cursor.fetchone()
                if result:
                    context.id = result['id']
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Failed to create conversation context: {e}")
            return False
    
    def get_by_session_id(self, session_id: str) -> Optional[ConversationContext]:
        """Get context by session ID"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM conversation_context WHERE session_id = %s
                """, (session_id,))
                
                row = cursor.fetchone()
                return ConversationContext.from_db_row(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get context for session {session_id}: {e}")
            return None
    
    def get_active_sessions(self, assistant_id: str, hours: int = 24) -> List[ConversationContext]:
        """Get active sessions for an assistant"""
        try:
            cutoff_time = int((time.time() - hours * 3600) * 1000)
            
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM conversation_context 
                    WHERE assistant_id = %s AND last_interaction > %s
                    ORDER BY last_interaction DESC
                """, (assistant_id, cutoff_time))
                
                rows = cursor.fetchall()
                return [ConversationContext.from_db_row(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get active sessions for {assistant_id}: {e}")
            return []
    
    def update_context(self, context: ConversationContext) -> bool:
        """Update conversation context"""
        try:
            with self.db.get_transaction() as cursor:
                cursor.execute("""
                    UPDATE conversation_context SET
                        conversation_history = %s,
                        context_variables = %s,
                        active_prompt_id = %s,
                        prompt_variables = %s,
                        current_context_length = %s,
                        last_interaction = %s,
                        interaction_count = %s,
                        avg_response_time = %s,
                        total_tokens_used = %s,
                        errors_encountered = %s,
                        updated_at = %s
                    WHERE id = %s
                """, (
                    json.dumps(context.conversation_history),
                    json.dumps(context.context_variables),
                    context.active_prompt_id,
                    json.dumps(context.prompt_variables),
                    context.current_context_length,
                    context.last_interaction,
                    context.interaction_count,
                    context.avg_response_time,
                    context.total_tokens_used,
                    context.errors_encountered,
                    int(time.time() * 1000),
                    context.id
                ))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update context {context.id}: {e}")
            return False
    
    def cleanup_old_contexts(self, days: int = 30) -> int:
        """Clean up old conversation contexts"""
        try:
            cutoff_time = int((time.time() - days * 24 * 3600) * 1000)
            
            with self.db.get_transaction() as cursor:
                cursor.execute("""
                    DELETE FROM conversation_context 
                    WHERE last_interaction < %s
                """, (cutoff_time,))
                
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"Failed to cleanup old contexts: {e}")
            return 0


class AssistantAnalyticsRepository:
    """Repository for Assistant Analytics operations"""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def record_metric(self, assistant_id: str, metric_name: str, metric_value: float,
                     time_period: str = 'daily', metadata: Dict[str, Any] = None) -> bool:
        """Record an analytics metric"""
        try:
            with self.db.get_transaction() as cursor:
                cursor.execute(
                    "SELECT record_assistant_metric(%s, %s, %s, %s, %s)",
                    (assistant_id, metric_name, metric_value, time_period, 
                     json.dumps(metadata or {}))
                )
                return True
                
        except Exception as e:
            logger.error(f"Failed to record metric {metric_name} for {assistant_id}: {e}")
            return False
    
    def get_metrics(self, assistant_id: str, metric_name: str = None, 
                   time_period: str = None, days: int = 30) -> List[Dict[str, Any]]:
        """Get metrics for an assistant"""
        try:
            cutoff_time = int((time.time() - days * 24 * 3600) * 1000)
            
            with self.db.get_cursor() as cursor:
                query = """
                    SELECT * FROM assistant_analytics 
                    WHERE assistant_id = %s AND recorded_at > %s
                """
                params = [assistant_id, cutoff_time]
                
                if metric_name:
                    query += " AND metric_name = %s"
                    params.append(metric_name)
                
                if time_period:
                    query += " AND time_period = %s"
                    params.append(time_period)
                
                query += " ORDER BY recorded_at DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get metrics for {assistant_id}: {e}")
            return []
    
    def get_aggregated_metrics(self, assistant_id: str, days: int = 7) -> Dict[str, Any]:
        """Get aggregated metrics summary"""
        try:
            cutoff_time = int((time.time() - days * 24 * 3600) * 1000)
            
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        metric_name,
                        COUNT(*) as count,
                        AVG(metric_value) as avg_value,
                        MIN(metric_value) as min_value,
                        MAX(metric_value) as max_value,
                        SUM(metric_value) as total_value
                    FROM assistant_analytics 
                    WHERE assistant_id = %s AND recorded_at > %s
                    GROUP BY metric_name
                    ORDER BY metric_name
                """, (assistant_id, cutoff_time))
                
                rows = cursor.fetchall()
                
                return {
                    row['metric_name']: {
                        'count': row['count'],
                        'average': float(row['avg_value']),
                        'minimum': float(row['min_value']),
                        'maximum': float(row['max_value']),
                        'total': float(row['total_value'])
                    }
                    for row in rows
                }
                
        except Exception as e:
            logger.error(f"Failed to get aggregated metrics for {assistant_id}: {e}")
            return {}