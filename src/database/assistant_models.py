"""
Enhanced AI Assistant Framework Models
Extends the base models with assistant framework functionality
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime

from .models import AIAssistant as BaseAIAssistant


class AssistantStatus(Enum):
    """Assistant deployment status"""
    DRAFT = "draft"
    ACTIVE = "active" 
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class AssistantType(Enum):
    """Types of AI assistants"""
    GENERAL = "general"
    SPECIALIZED = "specialized"
    CONVERSATIONAL = "conversational"
    TASK_ORIENTED = "task_oriented"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    SUPPORT = "support"
    EDUCATIONAL = "educational"


class DeploymentEnvironment(Enum):
    """Assistant deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class AssistantProfile(BaseAIAssistant):
    """Enhanced AI Assistant with framework capabilities"""
    
    # Framework-specific fields
    assistant_type: AssistantType = AssistantType.GENERAL
    status: AssistantStatus = AssistantStatus.DRAFT
    version: str = "1.0.0"
    parent_assistant_id: Optional[str] = None  # For versioning/forking
    
    # Prompt integration
    primary_prompt_id: Optional[int] = None
    prompt_version_id: Optional[int] = None
    fallback_prompts: List[int] = field(default_factory=list)
    
    # Advanced configuration
    personality_traits: Dict[str, Any] = field(default_factory=dict)
    response_guidelines: Dict[str, Any] = field(default_factory=dict)
    context_memory_size: int = 4000  # Token limit for conversation context
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # Deployment settings
    deployment_config: Dict[str, Any] = field(default_factory=dict)
    environment: DeploymentEnvironment = DeploymentEnvironment.DEVELOPMENT
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    
    # Usage tracking
    total_conversations: int = 0
    total_messages: int = 0
    avg_conversation_length: float = 0.0
    avg_response_time: float = 0.0
    user_satisfaction_rating: float = 0.0
    
    # Analytics and monitoring
    usage_analytics: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    error_logs: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    category_ids: List[int] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization processing"""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        # Initialize default configuration if empty
        if not self.configuration:
            self.configuration = self._default_configuration()
        
        # Initialize default capabilities if empty  
        if not self.capabilities:
            self.capabilities = self._default_capabilities()
    
    def _default_configuration(self) -> Dict[str, Any]:
        """Get default configuration based on assistant type"""
        base_config = {
            "response_format": "markdown",
            "include_sources": True,
            "max_context_turns": 10,
            "enable_memory": True,
            "safety_filters": ["profanity", "harmful_content"]
        }
        
        type_specific = {
            AssistantType.CONVERSATIONAL: {
                "personality_enabled": True,
                "emotion_detection": True,
                "context_awareness": "high"
            },
            AssistantType.TASK_ORIENTED: {
                "step_by_step": True,
                "progress_tracking": True,
                "result_validation": True
            },
            AssistantType.ANALYTICAL: {
                "data_visualization": True,
                "statistical_analysis": True,
                "citation_required": True
            },
            AssistantType.CREATIVE: {
                "inspiration_mode": True,
                "iteration_support": True,
                "style_adaptation": True
            }
        }
        
        if self.assistant_type in type_specific:
            base_config.update(type_specific[self.assistant_type])
        
        return base_config
    
    def _default_capabilities(self) -> List[str]:
        """Get default capabilities based on assistant type"""
        base_capabilities = ["text_generation", "conversation", "context_awareness"]
        
        type_capabilities = {
            AssistantType.ANALYTICAL: ["data_analysis", "visualization", "statistics"],
            AssistantType.CREATIVE: ["creative_writing", "ideation", "storytelling"],
            AssistantType.TASK_ORIENTED: ["task_planning", "step_guidance", "progress_tracking"],
            AssistantType.EDUCATIONAL: ["explanation", "quiz_generation", "learning_paths"],
            AssistantType.SUPPORT: ["troubleshooting", "documentation", "user_guidance"]
        }
        
        if self.assistant_type in type_capabilities:
            base_capabilities.extend(type_capabilities[self.assistant_type])
        
        return base_capabilities
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        base_dict = super().to_dict()
        
        # Add framework-specific fields
        framework_fields = {
            'assistant_type': self.assistant_type.value,
            'status': self.status.value,
            'version': self.version,
            'parent_assistant_id': self.parent_assistant_id,
            'primary_prompt_id': self.primary_prompt_id,
            'prompt_version_id': self.prompt_version_id,
            'fallback_prompts': json.dumps(self.fallback_prompts),
            'personality_traits': json.dumps(self.personality_traits),
            'response_guidelines': json.dumps(self.response_guidelines),
            'context_memory_size': self.context_memory_size,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'deployment_config': json.dumps(self.deployment_config),
            'environment': self.environment.value,
            'resource_limits': json.dumps(self.resource_limits),
            'total_conversations': self.total_conversations,
            'total_messages': self.total_messages,
            'avg_conversation_length': self.avg_conversation_length,
            'avg_response_time': self.avg_response_time,
            'user_satisfaction_rating': self.user_satisfaction_rating,
            'usage_analytics': json.dumps(self.usage_analytics),
            'performance_metrics': json.dumps(self.performance_metrics),
            'error_logs': json.dumps(self.error_logs[-10:]),  # Keep last 10 errors
            'tags': json.dumps(self.tags),
            'category_ids': json.dumps(self.category_ids)
        }
        
        base_dict.update(framework_fields)
        return base_dict
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'AssistantProfile':
        """Create instance from database row"""
        # Get base fields
        base_fields = {
            'id': row['id'],
            'name': row['name'],
            'description': row['description'],
            'system_prompt': row['system_prompt'],
            'model_id': row['model_id'],
            'user_id': row['user_id'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'is_active': row['is_active'],
            'configuration': json.loads(row['configuration']) if row['configuration'] else {},
            'capabilities': json.loads(row['capabilities']) if row['capabilities'] else [],
            'access_control': json.loads(row['access_control']) if row['access_control'] else {},
            'performance_stats': json.loads(row['performance_stats']) if row['performance_stats'] else {}
        }
        
        # Add framework fields
        framework_fields = {
            'assistant_type': AssistantType(row.get('assistant_type', 'general')),
            'status': AssistantStatus(row.get('status', 'draft')),
            'version': row.get('version', '1.0.0'),
            'parent_assistant_id': row.get('parent_assistant_id'),
            'primary_prompt_id': row.get('primary_prompt_id'),
            'prompt_version_id': row.get('prompt_version_id'),
            'fallback_prompts': json.loads(row['fallback_prompts']) if row.get('fallback_prompts') else [],
            'personality_traits': json.loads(row['personality_traits']) if row.get('personality_traits') else {},
            'response_guidelines': json.loads(row['response_guidelines']) if row.get('response_guidelines') else {},
            'context_memory_size': row.get('context_memory_size', 4000),
            'temperature': float(row.get('temperature', 0.7)),
            'max_tokens': row.get('max_tokens', 2000),
            'deployment_config': json.loads(row['deployment_config']) if row.get('deployment_config') else {},
            'environment': DeploymentEnvironment(row.get('environment', 'development')),
            'resource_limits': json.loads(row['resource_limits']) if row.get('resource_limits') else {},
            'total_conversations': row.get('total_conversations', 0),
            'total_messages': row.get('total_messages', 0),
            'avg_conversation_length': float(row.get('avg_conversation_length', 0.0)),
            'avg_response_time': float(row.get('avg_response_time', 0.0)),
            'user_satisfaction_rating': float(row.get('user_satisfaction_rating', 0.0)),
            'usage_analytics': json.loads(row['usage_analytics']) if row.get('usage_analytics') else {},
            'performance_metrics': json.loads(row['performance_metrics']) if row.get('performance_metrics') else {},
            'error_logs': json.loads(row['error_logs']) if row.get('error_logs') else [],
            'tags': json.loads(row['tags']) if row.get('tags') else [],
            'category_ids': json.loads(row['category_ids']) if row.get('category_ids') else []
        }
        
        return cls(**{**base_fields, **framework_fields})
    
    def update_usage_stats(self, messages_count: int, response_time: float, user_rating: Optional[int] = None):
        """Update usage statistics"""
        self.total_conversations += 1
        self.total_messages += messages_count
        
        # Update averages
        if self.total_conversations > 1:
            self.avg_conversation_length = (
                (self.avg_conversation_length * (self.total_conversations - 1) + messages_count) 
                / self.total_conversations
            )
            self.avg_response_time = (
                (self.avg_response_time * (self.total_conversations - 1) + response_time)
                / self.total_conversations
            )
        else:
            self.avg_conversation_length = messages_count
            self.avg_response_time = response_time
        
        # Update satisfaction rating if provided
        if user_rating is not None:
            if self.user_satisfaction_rating == 0:
                self.user_satisfaction_rating = user_rating
            else:
                # Weighted average with more weight on recent ratings
                self.user_satisfaction_rating = (
                    self.user_satisfaction_rating * 0.8 + user_rating * 0.2
                )
        
        self.updated_at = int(time.time() * 1000)
    
    def add_error_log(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Add error to error log"""
        error_entry = {
            'timestamp': int(time.time() * 1000),
            'type': error_type,
            'message': error_message,
            'context': context or {}
        }
        
        self.error_logs.append(error_entry)
        # Keep only last 50 errors
        if len(self.error_logs) > 50:
            self.error_logs = self.error_logs[-50:]
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status"""
        return {
            'status': self.status.value,
            'environment': self.environment.value,
            'version': self.version,
            'is_active': self.is_active,
            'total_conversations': self.total_conversations,
            'avg_response_time': self.avg_response_time,
            'user_satisfaction': self.user_satisfaction_rating,
            'last_updated': self.updated_at
        }
    
    def can_deploy_to(self, environment: DeploymentEnvironment) -> tuple[bool, str]:
        """Check if assistant can be deployed to environment"""
        if self.status == AssistantStatus.DRAFT:
            return False, "Assistant is still in draft status"
        
        if self.status == AssistantStatus.ARCHIVED:
            return False, "Assistant is archived"
        
        if not self.primary_prompt_id:
            return False, "No primary prompt assigned"
        
        if environment == DeploymentEnvironment.PRODUCTION:
            if self.user_satisfaction_rating < 3.0:
                return False, "User satisfaction rating too low for production"
            
            if self.total_conversations < 10:
                return False, "Insufficient testing conversations for production"
        
        return True, "Ready for deployment"


@dataclass
class AssistantDeployment:
    """Assistant deployment record"""
    id: Optional[int] = None
    assistant_id: str = ""
    environment: DeploymentEnvironment = DeploymentEnvironment.DEVELOPMENT
    version: str = "1.0.0"
    status: str = "active"  # active, inactive, failed
    deployed_at: int = field(default_factory=lambda: int(time.time() * 1000))
    deployed_by: str = ""
    configuration_snapshot: Dict[str, Any] = field(default_factory=dict)
    resource_allocation: Dict[str, Any] = field(default_factory=dict)
    health_check_url: Optional[str] = None
    metrics_endpoint: Optional[str] = None
    rollback_version: Optional[str] = None
    deployment_logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'assistant_id': self.assistant_id,
            'environment': self.environment.value,
            'version': self.version,
            'status': self.status,
            'deployed_at': self.deployed_at,
            'deployed_by': self.deployed_by,
            'configuration_snapshot': json.dumps(self.configuration_snapshot),
            'resource_allocation': json.dumps(self.resource_allocation),
            'health_check_url': self.health_check_url,
            'metrics_endpoint': self.metrics_endpoint,
            'rollback_version': self.rollback_version,
            'deployment_logs': json.dumps(self.deployment_logs[-20:])  # Keep last 20 logs
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'AssistantDeployment':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            assistant_id=row['assistant_id'],
            environment=DeploymentEnvironment(row['environment']),
            version=row['version'],
            status=row['status'],
            deployed_at=row['deployed_at'],
            deployed_by=row['deployed_by'],
            configuration_snapshot=json.loads(row['configuration_snapshot']) if row['configuration_snapshot'] else {},
            resource_allocation=json.loads(row['resource_allocation']) if row['resource_allocation'] else {},
            health_check_url=row['health_check_url'],
            metrics_endpoint=row['metrics_endpoint'],
            rollback_version=row['rollback_version'],
            deployment_logs=json.loads(row['deployment_logs']) if row['deployment_logs'] else []
        )


@dataclass 
class ConversationContext:
    """Enhanced conversation context with assistant integration"""
    id: Optional[int] = None
    session_id: str = ""
    assistant_id: str = ""
    user_id: str = ""
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    context_variables: Dict[str, Any] = field(default_factory=dict)
    active_prompt_id: Optional[int] = None
    prompt_variables: Dict[str, Any] = field(default_factory=dict)
    
    # Context management
    max_context_length: int = 4000  # Token limit
    current_context_length: int = 0
    context_compression_enabled: bool = True
    
    # Session metadata
    started_at: int = field(default_factory=lambda: int(time.time() * 1000))
    last_interaction: int = field(default_factory=lambda: int(time.time() * 1000))
    interaction_count: int = 0
    
    # Performance tracking
    avg_response_time: float = 0.0
    total_tokens_used: int = 0
    errors_encountered: int = 0
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add message to conversation history"""
        message = {
            'role': role,
            'content': content,
            'timestamp': int(time.time() * 1000),
            'metadata': metadata or {}
        }
        
        self.conversation_history.append(message)
        self.interaction_count += 1
        self.last_interaction = message['timestamp']
        
        # Estimate token count (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = len(content) // 4
        self.current_context_length += estimated_tokens
        self.total_tokens_used += estimated_tokens
        
        # Compress context if needed
        if self.current_context_length > self.max_context_length and self.context_compression_enabled:
            self._compress_context()
    
    def _compress_context(self):
        """Compress conversation history to stay within limits"""
        # Keep first message (usually system prompt) and recent messages
        if len(self.conversation_history) <= 3:
            return
        
        # Keep system message and last N messages that fit in context
        system_message = self.conversation_history[0] if self.conversation_history[0]['role'] == 'system' else None
        recent_messages = []
        token_count = 0
        
        # Work backwards from most recent messages
        for message in reversed(self.conversation_history[1:]):
            estimated_tokens = len(message['content']) // 4
            if token_count + estimated_tokens > self.max_context_length * 0.8:  # Leave some buffer
                break
            
            recent_messages.insert(0, message)
            token_count += estimated_tokens
        
        # Reconstruct conversation history
        new_history = []
        if system_message:
            new_history.append(system_message)
        
        # Add compression marker if we removed messages
        if len(recent_messages) < len(self.conversation_history) - (1 if system_message else 0):
            compression_marker = {
                'role': 'system',
                'content': f'[Context compressed - {len(self.conversation_history) - len(recent_messages) - (1 if system_message else 0)} earlier messages summarized]',
                'timestamp': int(time.time() * 1000),
                'metadata': {'compressed': True}
            }
            new_history.append(compression_marker)
        
        new_history.extend(recent_messages)
        self.conversation_history = new_history
        self.current_context_length = token_count
    
    def update_performance_metrics(self, response_time: float, tokens_used: int):
        """Update performance metrics for this context"""
        # Update average response time
        if self.interaction_count > 1:
            self.avg_response_time = (
                (self.avg_response_time * (self.interaction_count - 1) + response_time)
                / self.interaction_count
            )
        else:
            self.avg_response_time = response_time
        
        self.total_tokens_used += tokens_used
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'session_id': self.session_id,
            'assistant_id': self.assistant_id,
            'user_id': self.user_id,
            'conversation_history': json.dumps(self.conversation_history),
            'context_variables': json.dumps(self.context_variables),
            'active_prompt_id': self.active_prompt_id,
            'prompt_variables': json.dumps(self.prompt_variables),
            'max_context_length': self.max_context_length,
            'current_context_length': self.current_context_length,
            'context_compression_enabled': self.context_compression_enabled,
            'started_at': self.started_at,
            'last_interaction': self.last_interaction,
            'interaction_count': self.interaction_count,
            'avg_response_time': self.avg_response_time,
            'total_tokens_used': self.total_tokens_used,
            'errors_encountered': self.errors_encountered
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'ConversationContext':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            session_id=row['session_id'],
            assistant_id=row['assistant_id'],
            user_id=row['user_id'],
            conversation_history=json.loads(row['conversation_history']) if row['conversation_history'] else [],
            context_variables=json.loads(row['context_variables']) if row['context_variables'] else {},
            active_prompt_id=row['active_prompt_id'],
            prompt_variables=json.loads(row['prompt_variables']) if row['prompt_variables'] else {},
            max_context_length=row['max_context_length'],
            current_context_length=row['current_context_length'],
            context_compression_enabled=row['context_compression_enabled'],
            started_at=row['started_at'],
            last_interaction=row['last_interaction'],
            interaction_count=row['interaction_count'],
            avg_response_time=float(row['avg_response_time']),
            total_tokens_used=row['total_tokens_used'],
            errors_encountered=row['errors_encountered']
        )