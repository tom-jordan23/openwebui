"""
Repository classes for database access
"""
from typing import List, Optional, Dict, Any
from .connection import get_db_connection
from .models import (
    PromptVersion, PromptCategory, AIAssistant, 
    ConversationSession, Experiment, KnowledgeSource
)
import logging
import uuid
import time

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository with common database operations"""
    
    def __init__(self):
        self.db = get_db_connection()


class PromptRepository(BaseRepository):
    """Repository for prompt management"""
    
    def create_version(self, prompt_version: PromptVersion) -> Optional[int]:
        """Create a new prompt version"""
        try:
            with self.db.get_transaction() as cursor:
                # Check if this is the first version for this prompt
                cursor.execute(
                    "SELECT COUNT(*) as count FROM prompt_version WHERE prompt_id = %s",
                    (prompt_version.prompt_id,)
                )
                is_first_version = cursor.fetchone()['count'] == 0
                
                # If first version, make it active
                if is_first_version:
                    prompt_version.is_active = True
                
                # Insert the new version
                insert_query = """
                    INSERT INTO prompt_version (
                        prompt_id, version_number, title, content, variables,
                        created_by, created_at, is_active, performance_metrics
                    ) VALUES (
                        %(prompt_id)s, %(version_number)s, %(title)s, %(content)s, %(variables)s,
                        %(created_by)s, %(created_at)s, %(is_active)s, %(performance_metrics)s
                    ) RETURNING id
                """
                cursor.execute(insert_query, prompt_version.to_dict())
                result = cursor.fetchone()
                return result['id'] if result else None
                
        except Exception as e:
            logger.error(f"Failed to create prompt version: {e}")
            return None
    
    def get_version_by_id(self, version_id: int) -> Optional[PromptVersion]:
        """Get prompt version by ID"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM prompt_version WHERE id = %s",
                    (version_id,)
                )
                row = cursor.fetchone()
                return PromptVersion.from_db_row(dict(row)) if row else None
        except Exception as e:
            logger.error(f"Failed to get prompt version {version_id}: {e}")
            return None
    
    def get_versions_by_prompt_id(self, prompt_id: int) -> List[PromptVersion]:
        """Get all versions for a prompt"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """SELECT * FROM prompt_version 
                       WHERE prompt_id = %s 
                       ORDER BY version_number DESC""",
                    (prompt_id,)
                )
                rows = cursor.fetchall()
                return [PromptVersion.from_db_row(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get prompt versions for prompt {prompt_id}: {e}")
            return []
    
    def get_active_version(self, prompt_id: int) -> Optional[PromptVersion]:
        """Get active version for a prompt"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """SELECT * FROM prompt_version 
                       WHERE prompt_id = %s AND is_active = TRUE 
                       LIMIT 1""",
                    (prompt_id,)
                )
                row = cursor.fetchone()
                return PromptVersion.from_db_row(dict(row)) if row else None
        except Exception as e:
            logger.error(f"Failed to get active prompt version for prompt {prompt_id}: {e}")
            return None
    
    def set_active_version(self, prompt_id: int, version_id: int) -> bool:
        """Set a version as active (deactivates others)"""
        try:
            with self.db.get_transaction() as cursor:
                # Deactivate all versions for this prompt
                cursor.execute(
                    "UPDATE prompt_version SET is_active = FALSE WHERE prompt_id = %s",
                    (prompt_id,)
                )
                
                # Activate the specified version
                cursor.execute(
                    "UPDATE prompt_version SET is_active = TRUE WHERE id = %s AND prompt_id = %s",
                    (version_id, prompt_id)
                )
                
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to set active version {version_id} for prompt {prompt_id}: {e}")
            return False
    
    def create_category(self, category: PromptCategory) -> Optional[int]:
        """Create a new prompt category"""
        try:
            with self.db.get_transaction() as cursor:
                insert_query = """
                    INSERT INTO prompt_category (name, description, color, created_at, created_by)
                    VALUES (%(name)s, %(description)s, %(color)s, %(created_at)s, %(created_by)s)
                    RETURNING id
                """
                cursor.execute(insert_query, category.to_dict())
                result = cursor.fetchone()
                return result['id'] if result else None
        except Exception as e:
            logger.error(f"Failed to create prompt category: {e}")
            return None
    
    def get_categories(self) -> List[PromptCategory]:
        """Get all prompt categories"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM prompt_category ORDER BY name")
                rows = cursor.fetchall()
                return [PromptCategory.from_db_row(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get prompt categories: {e}")
            return []


class AIAssistantRepository(BaseRepository):
    """Repository for AI Assistant management"""
    
    def create(self, assistant: AIAssistant) -> bool:
        """Create a new AI assistant"""
        try:
            # Generate ID if not provided
            if not assistant.id:
                assistant.id = str(uuid.uuid4())
            
            with self.db.get_transaction() as cursor:
                insert_query = """
                    INSERT INTO ai_assistant (
                        id, name, description, system_prompt, model_id, user_id,
                        created_at, updated_at, is_active, configuration, 
                        capabilities, access_control, performance_stats
                    ) VALUES (
                        %(id)s, %(name)s, %(description)s, %(system_prompt)s, %(model_id)s, %(user_id)s,
                        %(created_at)s, %(updated_at)s, %(is_active)s, %(configuration)s,
                        %(capabilities)s, %(access_control)s, %(performance_stats)s
                    )
                """
                cursor.execute(insert_query, assistant.to_dict())
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to create AI assistant: {e}")
            return False
    
    def get_by_id(self, assistant_id: str) -> Optional[AIAssistant]:
        """Get AI assistant by ID"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM ai_assistant WHERE id = %s",
                    (assistant_id,)
                )
                row = cursor.fetchone()
                return AIAssistant.from_db_row(dict(row)) if row else None
        except Exception as e:
            logger.error(f"Failed to get AI assistant {assistant_id}: {e}")
            return None
    
    def get_by_user_id(self, user_id: str) -> List[AIAssistant]:
        """Get all assistants for a user"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """SELECT * FROM ai_assistant 
                       WHERE user_id = %s AND is_active = TRUE
                       ORDER BY created_at DESC""",
                    (user_id,)
                )
                rows = cursor.fetchall()
                return [AIAssistant.from_db_row(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get assistants for user {user_id}: {e}")
            return []
    
    def update(self, assistant: AIAssistant) -> bool:
        """Update an AI assistant"""
        try:
            assistant.updated_at = int(time.time() * 1000)
            
            with self.db.get_transaction() as cursor:
                update_query = """
                    UPDATE ai_assistant SET
                        name = %(name)s,
                        description = %(description)s,
                        system_prompt = %(system_prompt)s,
                        model_id = %(model_id)s,
                        updated_at = %(updated_at)s,
                        is_active = %(is_active)s,
                        configuration = %(configuration)s,
                        capabilities = %(capabilities)s,
                        access_control = %(access_control)s,
                        performance_stats = %(performance_stats)s
                    WHERE id = %(id)s
                """
                cursor.execute(update_query, assistant.to_dict())
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update AI assistant {assistant.id}: {e}")
            return False
    
    def delete(self, assistant_id: str) -> bool:
        """Soft delete an AI assistant"""
        try:
            with self.db.get_transaction() as cursor:
                cursor.execute(
                    "UPDATE ai_assistant SET is_active = FALSE WHERE id = %s",
                    (assistant_id,)
                )
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete AI assistant {assistant_id}: {e}")
            return False
    
    def get_active_assistants_with_stats(self) -> List[Dict[str, Any]]:
        """Get active assistants with performance statistics"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM active_assistants")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get active assistants with stats: {e}")
            return []


class ConversationRepository(BaseRepository):
    """Repository for conversation tracking"""
    
    def create_session(self, session: ConversationSession) -> bool:
        """Create a new conversation session"""
        try:
            # Generate ID if not provided
            if not session.id:
                session.id = str(uuid.uuid4())
            
            with self.db.get_transaction() as cursor:
                insert_query = """
                    INSERT INTO conversation_session (
                        id, chat_id, assistant_id, user_id, model_used,
                        started_at, ended_at, message_count, total_tokens,
                        avg_response_time, user_satisfaction, session_metadata
                    ) VALUES (
                        %(id)s, %(chat_id)s, %(assistant_id)s, %(user_id)s, %(model_used)s,
                        %(started_at)s, %(ended_at)s, %(message_count)s, %(total_tokens)s,
                        %(avg_response_time)s, %(user_satisfaction)s, %(session_metadata)s
                    )
                """
                cursor.execute(insert_query, session.to_dict())
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to create conversation session: {e}")
            return False
    
    def update_session(self, session: ConversationSession) -> bool:
        """Update a conversation session"""
        try:
            with self.db.get_transaction() as cursor:
                update_query = """
                    UPDATE conversation_session SET
                        ended_at = %(ended_at)s,
                        message_count = %(message_count)s,
                        total_tokens = %(total_tokens)s,
                        avg_response_time = %(avg_response_time)s,
                        user_satisfaction = %(user_satisfaction)s,
                        session_metadata = %(session_metadata)s
                    WHERE id = %(id)s
                """
                cursor.execute(update_query, session.to_dict())
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update conversation session {session.id}: {e}")
            return False
    
    def get_sessions_by_assistant(self, assistant_id: str, limit: int = 100) -> List[ConversationSession]:
        """Get conversation sessions for an assistant"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """SELECT * FROM conversation_session 
                       WHERE assistant_id = %s 
                       ORDER BY started_at DESC 
                       LIMIT %s""",
                    (assistant_id, limit)
                )
                rows = cursor.fetchall()
                return [ConversationSession.from_db_row(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get sessions for assistant {assistant_id}: {e}")
            return []


class KnowledgeRepository(BaseRepository):
    """Repository for knowledge management"""
    
    def create_source(self, source: KnowledgeSource) -> Optional[int]:
        """Create a new knowledge source"""
        try:
            with self.db.get_transaction() as cursor:
                insert_query = """
                    INSERT INTO knowledge_source (
                        name, source_type, source_path, content_hash,
                        last_processed_at, processing_status, user_id,
                        created_at, updated_at, metadata
                    ) VALUES (
                        %(name)s, %(source_type)s, %(source_path)s, %(content_hash)s,
                        %(last_processed_at)s, %(processing_status)s, %(user_id)s,
                        %(created_at)s, %(updated_at)s, %(metadata)s
                    ) RETURNING id
                """
                cursor.execute(insert_query, source.to_dict())
                result = cursor.fetchone()
                return result['id'] if result else None
        except Exception as e:
            logger.error(f"Failed to create knowledge source: {e}")
            return None
    
    def get_sources_by_user(self, user_id: str) -> List[KnowledgeSource]:
        """Get knowledge sources for a user"""
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    """SELECT * FROM knowledge_source 
                       WHERE user_id = %s 
                       ORDER BY created_at DESC""",
                    (user_id,)
                )
                rows = cursor.fetchall()
                return [KnowledgeSource.from_db_row(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get knowledge sources for user {user_id}: {e}")
            return []
    
    def update_processing_status(self, source_id: int, status: str, processed_at: Optional[int] = None) -> bool:
        """Update knowledge source processing status"""
        try:
            with self.db.get_transaction() as cursor:
                update_query = """
                    UPDATE knowledge_source SET 
                        processing_status = %s,
                        last_processed_at = COALESCE(%s, last_processed_at),
                        updated_at = %s
                    WHERE id = %s
                """
                current_time = int(time.time() * 1000)
                cursor.execute(update_query, (status, processed_at, current_time, source_id))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update processing status for source {source_id}: {e}")
            return False