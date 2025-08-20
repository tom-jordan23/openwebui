"""
Database models for AI Assistant Platform
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from enum import Enum
import time
import json


@dataclass
class PromptVersion:
    """Prompt version model"""
    id: Optional[int] = None
    prompt_id: int = 0
    version_number: int = 1
    title: str = ""
    content: str = ""
    variables: Dict[str, Any] = field(default_factory=dict)
    created_by: str = ""
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    is_active: bool = False
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'prompt_id': self.prompt_id,
            'version_number': self.version_number,
            'title': self.title,
            'content': self.content,
            'variables': json.dumps(self.variables) if isinstance(self.variables, dict) else self.variables,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'is_active': self.is_active,
            'performance_metrics': json.dumps(self.performance_metrics) if isinstance(self.performance_metrics, dict) else self.performance_metrics
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'PromptVersion':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            prompt_id=row['prompt_id'],
            version_number=row['version_number'],
            title=row['title'],
            content=row['content'],
            variables=cls._parse_json_field(row['variables'], {}),
            created_by=row['created_by'],
            created_at=row['created_at'],
            is_active=row['is_active'],
            performance_metrics=cls._parse_json_field(row['performance_metrics'], {})
        )
    
    @staticmethod
    def _parse_json_field(value: Any, default: Any) -> Any:
        """Parse JSON field that might be string or already parsed"""
        if not value:
            return default
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default


@dataclass
class PromptCategory:
    """Prompt category model"""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    color: Optional[str] = None
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    created_by: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': self.created_at,
            'created_by': self.created_by
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'PromptCategory':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            color=row['color'],
            created_at=row['created_at'],
            created_by=row['created_by']
        )


@dataclass
class AIAssistant:
    """AI Assistant model"""
    id: str = ""
    name: str = ""
    description: Optional[str] = None
    system_prompt: str = ""
    model_id: str = ""
    user_id: str = ""
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = field(default_factory=lambda: int(time.time() * 1000))
    is_active: bool = True
    configuration: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    access_control: Dict[str, Any] = field(default_factory=dict)
    performance_stats: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'system_prompt': self.system_prompt,
            'model_id': self.model_id,
            'user_id': self.user_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_active': self.is_active,
            'configuration': json.dumps(self.configuration) if isinstance(self.configuration, dict) else self.configuration,
            'capabilities': json.dumps(self.capabilities) if isinstance(self.capabilities, list) else self.capabilities,
            'access_control': json.dumps(self.access_control) if isinstance(self.access_control, dict) else self.access_control,
            'performance_stats': json.dumps(self.performance_stats) if isinstance(self.performance_stats, dict) else self.performance_stats
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'AIAssistant':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            system_prompt=row['system_prompt'],
            model_id=row['model_id'],
            user_id=row['user_id'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            is_active=row['is_active'],
            configuration=cls._parse_json_field(row['configuration'], {}),
            capabilities=cls._parse_json_field(row['capabilities'], []),
            access_control=cls._parse_json_field(row['access_control'], {}),
            performance_stats=cls._parse_json_field(row['performance_stats'], {})
        )
    
    @staticmethod
    def _parse_json_field(value: Any, default: Any) -> Any:
        """Parse JSON field that might be string or already parsed"""
        if not value:
            return default
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default


@dataclass
class ConversationSession:
    """Conversation session model"""
    id: str = ""
    chat_id: str = ""
    assistant_id: Optional[str] = None
    user_id: str = ""
    model_used: str = ""
    started_at: int = field(default_factory=lambda: int(time.time() * 1000))
    ended_at: Optional[int] = None
    message_count: int = 0
    total_tokens: int = 0
    avg_response_time: float = 0.0
    user_satisfaction: Optional[int] = None
    session_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'assistant_id': self.assistant_id,
            'user_id': self.user_id,
            'model_used': self.model_used,
            'started_at': self.started_at,
            'ended_at': self.ended_at,
            'message_count': self.message_count,
            'total_tokens': self.total_tokens,
            'avg_response_time': self.avg_response_time,
            'user_satisfaction': self.user_satisfaction,
            'session_metadata': json.dumps(self.session_metadata)
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'ConversationSession':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            chat_id=row['chat_id'],
            assistant_id=row['assistant_id'],
            user_id=row['user_id'],
            model_used=row['model_used'],
            started_at=row['started_at'],
            ended_at=row['ended_at'],
            message_count=row['message_count'],
            total_tokens=row['total_tokens'],
            avg_response_time=float(row['avg_response_time']) if row['avg_response_time'] else 0.0,
            user_satisfaction=row['user_satisfaction'],
            session_metadata=json.loads(row['session_metadata']) if row['session_metadata'] else {}
        )


class ExperimentStatus(Enum):
    """Experiment status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class Experiment:
    """A/B testing experiment model"""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    experiment_type: str = ""
    status: ExperimentStatus = ExperimentStatus.DRAFT
    start_date: Optional[int] = None
    end_date: Optional[int] = None
    target_metrics: Dict[str, Any] = field(default_factory=dict)
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    created_by: str = ""
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'name': self.name,
            'description': self.description,
            'experiment_type': self.experiment_type,
            'status': self.status.value,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'target_metrics': json.dumps(self.target_metrics),
            'success_criteria': json.dumps(self.success_criteria),
            'created_by': self.created_by,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'Experiment':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            experiment_type=row['experiment_type'],
            status=ExperimentStatus(row['status']),
            start_date=row['start_date'],
            end_date=row['end_date'],
            target_metrics=json.loads(row['target_metrics']) if row['target_metrics'] else {},
            success_criteria=json.loads(row['success_criteria']) if row['success_criteria'] else {},
            created_by=row['created_by'],
            created_at=row['created_at']
        )


@dataclass
class KnowledgeSource:
    """Knowledge source model for GraphRAG"""
    id: Optional[int] = None
    name: str = ""
    source_type: str = ""
    source_path: str = ""
    content_hash: Optional[str] = None
    last_processed_at: Optional[int] = None
    processing_status: str = "pending"
    user_id: str = ""
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = field(default_factory=lambda: int(time.time() * 1000))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'name': self.name,
            'source_type': self.source_type,
            'source_path': self.source_path,
            'content_hash': self.content_hash,
            'last_processed_at': self.last_processed_at,
            'processing_status': self.processing_status,
            'user_id': self.user_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': json.dumps(self.metadata)
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'KnowledgeSource':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            name=row['name'],
            source_type=row['source_type'],
            source_path=row['source_path'],
            content_hash=row['content_hash'],
            last_processed_at=row['last_processed_at'],
            processing_status=row['processing_status'],
            user_id=row['user_id'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )