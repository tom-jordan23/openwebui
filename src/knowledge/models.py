"""
Knowledge Management Models
Data models for GraphRAG integration including documents, entities, relationships, and embeddings
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime


class DocumentType(Enum):
    """Types of documents that can be processed"""
    TEXT = "text"
    PDF = "pdf"
    MARKDOWN = "markdown"
    HTML = "html"
    CSV = "csv"
    JSON = "json"
    CODE = "code"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class ProcessingStatus(Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    INDEXED = "indexed"
    ERROR = "error"


class EntityType(Enum):
    """Types of entities extracted from documents"""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    CONCEPT = "concept"
    PRODUCT = "product"
    EVENT = "event"
    DATE = "date"
    TECHNOLOGY = "technology"
    PROCESS = "process"
    CUSTOM = "custom"


class RelationshipType(Enum):
    """Types of relationships between entities"""
    RELATED_TO = "related_to"
    PART_OF = "part_of"
    CREATED_BY = "created_by"
    USED_BY = "used_by"
    LOCATED_IN = "located_in"
    WORKS_FOR = "works_for"
    MENTIONS = "mentions"
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"
    SIMILAR_TO = "similar_to"


@dataclass
class KnowledgeSource:
    """Enhanced knowledge source with GraphRAG capabilities"""
    id: Optional[int] = None
    name: str = ""
    source_type: DocumentType = DocumentType.TEXT
    source_path: str = ""
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    content_hash: Optional[str] = None
    
    # Processing information
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    last_processed_at: Optional[int] = None
    processing_error: Optional[str] = None
    processing_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Content analysis
    content_preview: Optional[str] = None
    extracted_text: Optional[str] = None
    language: Optional[str] = None
    content_length: Optional[int] = None
    
    # Graph extraction results
    entities_extracted: int = 0
    relationships_extracted: int = 0
    chunks_created: int = 0
    embeddings_generated: int = 0
    
    # Metadata
    user_id: str = ""
    collection_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = field(default_factory=lambda: int(time.time() * 1000))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'name': self.name,
            'source_type': self.source_type.value,
            'source_path': self.source_path,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'content_hash': self.content_hash,
            'processing_status': self.processing_status.value,
            'last_processed_at': self.last_processed_at,
            'processing_error': self.processing_error,
            'processing_metadata': json.dumps(self.processing_metadata),
            'content_preview': self.content_preview,
            'extracted_text': self.extracted_text,
            'language': self.language,
            'content_length': self.content_length,
            'entities_extracted': self.entities_extracted,
            'relationships_extracted': self.relationships_extracted,
            'chunks_created': self.chunks_created,
            'embeddings_generated': self.embeddings_generated,
            'user_id': self.user_id,
            'collection_id': self.collection_id,
            'tags': json.dumps(self.tags),
            'custom_metadata': json.dumps(self.custom_metadata),
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'KnowledgeSource':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            name=row['name'],
            source_type=DocumentType(row['source_type']),
            source_path=row['source_path'],
            original_filename=row['original_filename'],
            file_size=row['file_size'],
            content_hash=row['content_hash'],
            processing_status=ProcessingStatus(row['processing_status']),
            last_processed_at=row['last_processed_at'],
            processing_error=row['processing_error'],
            processing_metadata=json.loads(row['processing_metadata']) if row['processing_metadata'] else {},
            content_preview=row['content_preview'],
            extracted_text=row['extracted_text'],
            language=row['language'],
            content_length=row['content_length'],
            entities_extracted=row['entities_extracted'],
            relationships_extracted=row['relationships_extracted'],
            chunks_created=row['chunks_created'],
            embeddings_generated=row['embeddings_generated'],
            user_id=row['user_id'],
            collection_id=row['collection_id'],
            tags=json.loads(row['tags']) if row['tags'] else [],
            custom_metadata=json.loads(row['custom_metadata']) if row['custom_metadata'] else {},
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )


@dataclass
class DocumentChunk:
    """Represents a chunk of a document for vector embedding"""
    id: Optional[str] = None
    source_id: int = 0
    chunk_index: int = 0
    content: str = ""
    content_type: str = "text"
    
    # Chunking metadata
    start_position: int = 0
    end_position: int = 0
    token_count: Optional[int] = None
    character_count: int = 0
    
    # Vector embedding
    embedding_model: Optional[str] = None
    embedding_vector: Optional[List[float]] = None
    embedding_dimension: Optional[int] = None
    
    # Context information
    parent_chunk_id: Optional[str] = None
    child_chunk_ids: List[str] = field(default_factory=list)
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    
    # Graph relationships
    entities_mentioned: List[str] = field(default_factory=list)
    concepts_identified: List[str] = field(default_factory=list)
    
    # Quality metrics
    relevance_score: Optional[float] = None
    coherence_score: Optional[float] = None
    completeness_score: Optional[float] = None
    
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.character_count:
            self.character_count = len(self.content)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'source_id': self.source_id,
            'chunk_index': self.chunk_index,
            'content': self.content,
            'content_type': self.content_type,
            'start_position': self.start_position,
            'end_position': self.end_position,
            'token_count': self.token_count,
            'character_count': self.character_count,
            'embedding_model': self.embedding_model,
            'embedding_vector': json.dumps(self.embedding_vector) if self.embedding_vector else None,
            'embedding_dimension': self.embedding_dimension,
            'parent_chunk_id': self.parent_chunk_id,
            'child_chunk_ids': json.dumps(self.child_chunk_ids),
            'section_title': self.section_title,
            'page_number': self.page_number,
            'entities_mentioned': json.dumps(self.entities_mentioned),
            'concepts_identified': json.dumps(self.concepts_identified),
            'relevance_score': self.relevance_score,
            'coherence_score': self.coherence_score,
            'completeness_score': self.completeness_score,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'DocumentChunk':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            source_id=row['source_id'],
            chunk_index=row['chunk_index'],
            content=row['content'],
            content_type=row['content_type'],
            start_position=row['start_position'],
            end_position=row['end_position'],
            token_count=row['token_count'],
            character_count=row['character_count'],
            embedding_model=row['embedding_model'],
            embedding_vector=json.loads(row['embedding_vector']) if row['embedding_vector'] else None,
            embedding_dimension=row['embedding_dimension'],
            parent_chunk_id=row['parent_chunk_id'],
            child_chunk_ids=json.loads(row['child_chunk_ids']) if row['child_chunk_ids'] else [],
            section_title=row['section_title'],
            page_number=row['page_number'],
            entities_mentioned=json.loads(row['entities_mentioned']) if row['entities_mentioned'] else [],
            concepts_identified=json.loads(row['concepts_identified']) if row['concepts_identified'] else [],
            relevance_score=row['relevance_score'],
            coherence_score=row['coherence_score'],
            completeness_score=row['completeness_score'],
            created_at=row['created_at']
        )


@dataclass
class KnowledgeEntity:
    """Represents an entity extracted from documents"""
    id: Optional[str] = None
    name: str = ""
    entity_type: EntityType = EntityType.CONCEPT
    canonical_name: Optional[str] = None
    
    # Entity properties
    description: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # Source tracking
    source_documents: List[int] = field(default_factory=list)
    mention_count: int = 0
    first_mentioned_at: Optional[int] = None
    last_mentioned_at: Optional[int] = None
    
    # Graph metrics
    degree_centrality: Optional[float] = None
    betweenness_centrality: Optional[float] = None
    pagerank_score: Optional[float] = None
    
    # Vector representation
    embedding_vector: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    
    # Confidence scores
    extraction_confidence: float = 0.0
    type_confidence: float = 0.0
    
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = field(default_factory=lambda: int(time.time() * 1000))
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.canonical_name:
            self.canonical_name = self.name.lower().strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'name': self.name,
            'entity_type': self.entity_type.value,
            'canonical_name': self.canonical_name,
            'description': self.description,
            'aliases': json.dumps(self.aliases),
            'properties': json.dumps(self.properties),
            'source_documents': json.dumps(self.source_documents),
            'mention_count': self.mention_count,
            'first_mentioned_at': self.first_mentioned_at,
            'last_mentioned_at': self.last_mentioned_at,
            'degree_centrality': self.degree_centrality,
            'betweenness_centrality': self.betweenness_centrality,
            'pagerank_score': self.pagerank_score,
            'embedding_vector': json.dumps(self.embedding_vector) if self.embedding_vector else None,
            'embedding_model': self.embedding_model,
            'extraction_confidence': self.extraction_confidence,
            'type_confidence': self.type_confidence,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'KnowledgeEntity':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            name=row['name'],
            entity_type=EntityType(row['entity_type']),
            canonical_name=row['canonical_name'],
            description=row['description'],
            aliases=json.loads(row['aliases']) if row['aliases'] else [],
            properties=json.loads(row['properties']) if row['properties'] else {},
            source_documents=json.loads(row['source_documents']) if row['source_documents'] else [],
            mention_count=row['mention_count'],
            first_mentioned_at=row['first_mentioned_at'],
            last_mentioned_at=row['last_mentioned_at'],
            degree_centrality=row['degree_centrality'],
            betweenness_centrality=row['betweenness_centrality'],
            pagerank_score=row['pagerank_score'],
            embedding_vector=json.loads(row['embedding_vector']) if row['embedding_vector'] else None,
            embedding_model=row['embedding_model'],
            extraction_confidence=row['extraction_confidence'],
            type_confidence=row['type_confidence'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )


@dataclass
class KnowledgeRelationship:
    """Represents a relationship between entities"""
    id: Optional[str] = None
    source_entity_id: str = ""
    target_entity_id: str = ""
    relationship_type: RelationshipType = RelationshipType.RELATED_TO
    
    # Relationship properties
    description: Optional[str] = None
    weight: float = 1.0
    confidence: float = 0.0
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # Source tracking
    source_documents: List[int] = field(default_factory=list)
    source_chunks: List[str] = field(default_factory=list)
    evidence_text: List[str] = field(default_factory=list)
    
    # Temporal information
    temporal_context: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = field(default_factory=lambda: int(time.time() * 1000))
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'source_entity_id': self.source_entity_id,
            'target_entity_id': self.target_entity_id,
            'relationship_type': self.relationship_type.value,
            'description': self.description,
            'weight': self.weight,
            'confidence': self.confidence,
            'properties': json.dumps(self.properties),
            'source_documents': json.dumps(self.source_documents),
            'source_chunks': json.dumps(self.source_chunks),
            'evidence_text': json.dumps(self.evidence_text),
            'temporal_context': self.temporal_context,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'KnowledgeRelationship':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            source_entity_id=row['source_entity_id'],
            target_entity_id=row['target_entity_id'],
            relationship_type=RelationshipType(row['relationship_type']),
            description=row['description'],
            weight=row['weight'],
            confidence=row['confidence'],
            properties=json.loads(row['properties']) if row['properties'] else {},
            source_documents=json.loads(row['source_documents']) if row['source_documents'] else [],
            source_chunks=json.loads(row['source_chunks']) if row['source_chunks'] else [],
            evidence_text=json.loads(row['evidence_text']) if row['evidence_text'] else [],
            temporal_context=row['temporal_context'],
            start_date=row['start_date'],
            end_date=row['end_date'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )


@dataclass
class KnowledgeCollection:
    """Represents a collection of related knowledge sources"""
    id: Optional[str] = None
    name: str = ""
    description: Optional[str] = None
    user_id: str = ""
    
    # Collection properties
    is_public: bool = False
    source_count: int = 0
    total_entities: int = 0
    total_relationships: int = 0
    total_chunks: int = 0
    
    # Processing status
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    last_updated: Optional[int] = None
    
    # Configuration
    chunking_strategy: str = "semantic"
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    chunk_size: int = 512
    chunk_overlap: int = 50
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    updated_at: int = field(default_factory=lambda: int(time.time() * 1000))
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'is_public': self.is_public,
            'source_count': self.source_count,
            'total_entities': self.total_entities,
            'total_relationships': self.total_relationships,
            'total_chunks': self.total_chunks,
            'processing_status': self.processing_status.value,
            'last_updated': self.last_updated,
            'chunking_strategy': self.chunking_strategy,
            'embedding_model': self.embedding_model,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'tags': json.dumps(self.tags),
            'custom_settings': json.dumps(self.custom_settings),
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'KnowledgeCollection':
        """Create instance from database row"""
        return cls(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            user_id=row['user_id'],
            is_public=row['is_public'],
            source_count=row['source_count'],
            total_entities=row['total_entities'],
            total_relationships=row['total_relationships'],
            total_chunks=row['total_chunks'],
            processing_status=ProcessingStatus(row['processing_status']),
            last_updated=row['last_updated'],
            chunking_strategy=row['chunking_strategy'],
            embedding_model=row['embedding_model'],
            chunk_size=row['chunk_size'],
            chunk_overlap=row['chunk_overlap'],
            tags=json.loads(row['tags']) if row['tags'] else [],
            custom_settings=json.loads(row['custom_settings']) if row['custom_settings'] else {},
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )


@dataclass
class RetrievalQuery:
    """Represents a knowledge retrieval query"""
    id: Optional[str] = None
    query_text: str = ""
    user_id: str = ""
    assistant_id: Optional[str] = None
    
    # Query configuration
    max_results: int = 10
    similarity_threshold: float = 0.7
    use_graph_expansion: bool = True
    graph_depth: int = 2
    include_entities: bool = True
    include_relationships: bool = True
    
    # Filtering
    source_types: List[DocumentType] = field(default_factory=list)
    entity_types: List[EntityType] = field(default_factory=list)
    collection_ids: List[str] = field(default_factory=list)
    date_range: Optional[Dict[str, str]] = None
    
    # Results
    results_found: int = 0
    processing_time_ms: Optional[float] = None
    retrieval_strategy: Optional[str] = None
    
    created_at: int = field(default_factory=lambda: int(time.time() * 1000))
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class RetrievalResult:
    """Represents a single result from knowledge retrieval"""
    id: Optional[str] = None
    query_id: str = ""
    
    # Source information
    source_type: str = "chunk"  # chunk, entity, relationship
    source_id: str = ""
    content: str = ""
    
    # Scoring
    similarity_score: float = 0.0
    relevance_score: float = 0.0
    graph_score: Optional[float] = None
    combined_score: float = 0.0
    
    # Context
    source_document_id: Optional[int] = None
    source_document_name: Optional[str] = None
    chunk_position: Optional[int] = None
    
    # Related entities
    related_entities: List[Dict[str, Any]] = field(default_factory=list)
    related_relationships: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())