"""
GraphRAG Configuration Management
Centralized configuration for knowledge management and GraphRAG components
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VectorDatabaseConfig:
    """Vector database configuration"""
    provider: str = "qdrant"  # qdrant, weaviate, pinecone, chroma
    host: str = "localhost"
    port: int = 6333
    api_key: Optional[str] = None
    collection_name: str = "openwebui_knowledge"
    
    # Qdrant specific
    grpc_port: Optional[int] = 6334
    prefer_grpc: bool = True
    
    # Weaviate specific  
    scheme: str = "http"
    
    # Performance settings
    batch_size: int = 100
    timeout: int = 30
    max_retries: int = 3


@dataclass
class GraphDatabaseConfig:
    """Graph database configuration (Neo4j)"""
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "password"
    database: str = "neo4j"
    
    # Connection settings
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50
    connection_acquisition_timeout: int = 60
    
    # Performance settings
    batch_size: int = 1000
    enable_encryption: bool = False


@dataclass
class EmbeddingConfig:
    """Embedding model configuration"""
    provider: str = "sentence_transformers"  # sentence_transformers, openai, huggingface
    model_name: str = "sentence-transformers/all-mpnet-base-v2"
    
    # OpenAI specific
    openai_api_key: Optional[str] = None
    openai_model: str = "text-embedding-ada-002"
    
    # HuggingFace specific
    hf_token: Optional[str] = None
    device: str = "auto"  # auto, cpu, cuda, mps
    
    # Processing settings
    batch_size: int = 32
    max_length: int = 512
    normalize_embeddings: bool = True
    cache_embeddings: bool = True


@dataclass
class EntityExtractionConfig:
    """Entity extraction configuration"""
    provider: str = "spacy"  # spacy, transformers, openai, custom
    
    # Spacy specific
    spacy_model: str = "en_core_web_sm"
    custom_entity_types: List[str] = field(default_factory=list)
    
    # Transformers specific
    transformer_model: str = "dbmdz/bert-large-cased-finetuned-conll03-english"
    
    # OpenAI specific
    openai_model: str = "gpt-3.5-turbo"
    openai_api_key: Optional[str] = None
    
    # Processing settings
    confidence_threshold: float = 0.7
    max_entities_per_chunk: int = 10
    merge_similar_entities: bool = True
    entity_similarity_threshold: float = 0.9


@dataclass
class RelationshipExtractionConfig:
    """Relationship extraction configuration"""
    provider: str = "openie"  # openie, rebel, openai, custom
    
    # OpenIE specific
    openie_confidence_threshold: float = 0.6
    
    # REBEL specific
    rebel_model: str = "Babelscape/rebel-large"
    
    # OpenAI specific
    openai_model: str = "gpt-3.5-turbo"
    openai_api_key: Optional[str] = None
    
    # Processing settings
    confidence_threshold: float = 0.6
    max_relationships_per_chunk: int = 15
    merge_similar_relationships: bool = True
    relationship_similarity_threshold: float = 0.8


@dataclass
class ChunkingConfig:
    """Document chunking configuration"""
    strategy: str = "semantic"  # semantic, fixed, sentence, paragraph
    chunk_size: int = 512
    chunk_overlap: int = 50
    
    # Semantic chunking specific
    similarity_threshold: float = 0.8
    min_chunk_size: int = 100
    max_chunk_size: int = 1000
    
    # Sentence chunking specific
    sentences_per_chunk: int = 5
    
    # Paragraph chunking specific
    paragraphs_per_chunk: int = 2
    
    # General settings
    preserve_structure: bool = True
    include_metadata: bool = True


@dataclass
class ProcessingConfig:
    """Document processing configuration"""
    # Async processing
    async_processing: bool = True
    max_concurrent_jobs: int = 5
    queue_timeout: int = 3600
    
    # Retry settings
    max_retries: int = 3
    retry_delay: int = 5
    exponential_backoff: bool = True
    
    # File handling
    max_file_size_mb: int = 100
    supported_formats: List[str] = field(default_factory=lambda: [
        'txt', 'pdf', 'md', 'html', 'csv', 'json', 'docx', 'pptx'
    ])
    temp_dir: str = "/tmp/openwebui_processing"
    cleanup_temp_files: bool = True
    
    # OCR settings (for images/PDFs)
    enable_ocr: bool = True
    ocr_provider: str = "tesseract"  # tesseract, paddleocr, aws_textract
    ocr_languages: List[str] = field(default_factory=lambda: ['eng'])


@dataclass
class RetrievalConfig:
    """Retrieval and search configuration"""
    # Hybrid search settings
    vector_weight: float = 0.7
    graph_weight: float = 0.3
    
    # Vector search
    vector_search_limit: int = 50
    similarity_threshold: float = 0.7
    
    # Graph search
    graph_expansion_depth: int = 2
    max_graph_results: int = 20
    relationship_weight_threshold: float = 0.5
    
    # Result ranking
    enable_reranking: bool = True
    reranking_model: Optional[str] = None
    diversity_threshold: float = 0.8
    
    # Caching
    enable_query_caching: bool = True
    cache_ttl_minutes: int = 60
    max_cache_size: int = 1000


@dataclass
class GraphAnalysisConfig:
    """Graph analysis and metrics configuration"""
    # Centrality calculations
    enable_centrality_metrics: bool = True
    pagerank_iterations: int = 100
    pagerank_damping: float = 0.85
    
    # Community detection
    enable_community_detection: bool = True
    community_algorithm: str = "louvain"  # louvain, leiden, infomap
    
    # Graph metrics
    calculate_clustering_coefficient: bool = True
    calculate_shortest_paths: bool = False  # Expensive for large graphs
    
    # Update scheduling
    metrics_update_interval_hours: int = 24
    incremental_updates: bool = True


@dataclass
class GraphRAGIntegrationConfig:
    """Complete GraphRAG integration configuration"""
    # Database configurations
    vector_db: VectorDatabaseConfig = field(default_factory=VectorDatabaseConfig)
    graph_db: GraphDatabaseConfig = field(default_factory=GraphDatabaseConfig)
    
    # Model configurations
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    entity_extraction: EntityExtractionConfig = field(default_factory=EntityExtractionConfig)
    relationship_extraction: RelationshipExtractionConfig = field(default_factory=RelationshipExtractionConfig)
    
    # Processing configurations
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    graph_analysis: GraphAnalysisConfig = field(default_factory=GraphAnalysisConfig)
    
    # Integration settings
    enable_graphrag: bool = True
    fallback_to_vector_only: bool = True
    enable_analytics: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'vector_db': self.vector_db.__dict__,
            'graph_db': self.graph_db.__dict__,
            'embedding': self.embedding.__dict__,
            'entity_extraction': self.entity_extraction.__dict__,
            'relationship_extraction': self.relationship_extraction.__dict__,
            'chunking': self.chunking.__dict__,
            'processing': self.processing.__dict__,
            'retrieval': self.retrieval.__dict__,
            'graph_analysis': self.graph_analysis.__dict__,
            'enable_graphrag': self.enable_graphrag,
            'fallback_to_vector_only': self.fallback_to_vector_only,
            'enable_analytics': self.enable_analytics
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'GraphRAGIntegrationConfig':
        """Create configuration from dictionary"""
        config = cls()
        
        # Update nested configurations
        if 'vector_db' in config_dict:
            for key, value in config_dict['vector_db'].items():
                if hasattr(config.vector_db, key):
                    setattr(config.vector_db, key, value)
        
        if 'graph_db' in config_dict:
            for key, value in config_dict['graph_db'].items():
                if hasattr(config.graph_db, key):
                    setattr(config.graph_db, key, value)
        
        if 'embedding' in config_dict:
            for key, value in config_dict['embedding'].items():
                if hasattr(config.embedding, key):
                    setattr(config.embedding, key, value)
        
        if 'entity_extraction' in config_dict:
            for key, value in config_dict['entity_extraction'].items():
                if hasattr(config.entity_extraction, key):
                    setattr(config.entity_extraction, key, value)
        
        if 'relationship_extraction' in config_dict:
            for key, value in config_dict['relationship_extraction'].items():
                if hasattr(config.relationship_extraction, key):
                    setattr(config.relationship_extraction, key, value)
        
        if 'chunking' in config_dict:
            for key, value in config_dict['chunking'].items():
                if hasattr(config.chunking, key):
                    setattr(config.chunking, key, value)
        
        if 'processing' in config_dict:
            for key, value in config_dict['processing'].items():
                if hasattr(config.processing, key):
                    setattr(config.processing, key, value)
        
        if 'retrieval' in config_dict:
            for key, value in config_dict['retrieval'].items():
                if hasattr(config.retrieval, key):
                    setattr(config.retrieval, key, value)
        
        if 'graph_analysis' in config_dict:
            for key, value in config_dict['graph_analysis'].items():
                if hasattr(config.graph_analysis, key):
                    setattr(config.graph_analysis, key, value)
        
        # Update top-level settings
        for key in ['enable_graphrag', 'fallback_to_vector_only', 'enable_analytics']:
            if key in config_dict:
                setattr(config, key, config_dict[key])
        
        return config


class GraphRAGConfigManager:
    """Configuration manager for GraphRAG integration"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_file()
        self._config: Optional[GraphRAGIntegrationConfig] = None
    
    def _get_default_config_file(self) -> str:
        """Get default configuration file path"""
        # Check environment variable first
        env_config = os.getenv('GRAPHRAG_CONFIG_FILE')
        if env_config and os.path.exists(env_config):
            return env_config
        
        # Check standard locations
        possible_paths = [
            'config/graphrag.yaml',
            'config/graphrag.yml',
            'config/graphrag.json',
            '../config/graphrag.yaml',
            '/etc/openwebui/graphrag.yaml'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Return default path
        return 'config/graphrag.yaml'
    
    def load_config(self) -> GraphRAGIntegrationConfig:
        """Load configuration from file or create default"""
        if self._config is not None:
            return self._config
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    if self.config_file.endswith('.json'):
                        config_data = json.load(f)
                    else:  # Assume YAML
                        config_data = yaml.safe_load(f)
                
                self._config = GraphRAGIntegrationConfig.from_dict(config_data)
            else:
                # Create default configuration
                self._config = GraphRAGIntegrationConfig()
                self.save_config()
            
            # Override with environment variables
            self._apply_env_overrides()
            
            return self._config
            
        except Exception as e:
            print(f"Error loading GraphRAG config: {e}")
            # Return default configuration
            self._config = GraphRAGIntegrationConfig()
            return self._config
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            if self._config is None:
                return False
            
            # Ensure config directory exists
            config_dir = os.path.dirname(self.config_file)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
            
            config_data = self._config.to_dict()
            
            with open(self.config_file, 'w') as f:
                if self.config_file.endswith('.json'):
                    json.dump(config_data, f, indent=2)
                else:  # YAML
                    yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving GraphRAG config: {e}")
            return False
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        if not self._config:
            return
        
        # Vector database overrides
        if os.getenv('VECTOR_DB_HOST'):
            self._config.vector_db.host = os.getenv('VECTOR_DB_HOST')
        if os.getenv('VECTOR_DB_PORT'):
            self._config.vector_db.port = int(os.getenv('VECTOR_DB_PORT'))
        if os.getenv('VECTOR_DB_API_KEY'):
            self._config.vector_db.api_key = os.getenv('VECTOR_DB_API_KEY')
        
        # Graph database overrides
        if os.getenv('NEO4J_URI'):
            self._config.graph_db.uri = os.getenv('NEO4J_URI')
        if os.getenv('NEO4J_USER'):
            self._config.graph_db.user = os.getenv('NEO4J_USER')
        if os.getenv('NEO4J_PASSWORD'):
            self._config.graph_db.password = os.getenv('NEO4J_PASSWORD')
        
        # Embedding overrides
        if os.getenv('OPENAI_API_KEY'):
            self._config.embedding.openai_api_key = os.getenv('OPENAI_API_KEY')
            self._config.entity_extraction.openai_api_key = os.getenv('OPENAI_API_KEY')
            self._config.relationship_extraction.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if os.getenv('HF_TOKEN'):
            self._config.embedding.hf_token = os.getenv('HF_TOKEN')
        
        # Processing overrides
        if os.getenv('GRAPHRAG_ASYNC_PROCESSING'):
            self._config.processing.async_processing = os.getenv('GRAPHRAG_ASYNC_PROCESSING').lower() == 'true'
        
        if os.getenv('GRAPHRAG_MAX_CONCURRENT_JOBS'):
            self._config.processing.max_concurrent_jobs = int(os.getenv('GRAPHRAG_MAX_CONCURRENT_JOBS'))
    
    def get_config(self) -> GraphRAGIntegrationConfig:
        """Get current configuration"""
        return self.load_config()
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values"""
        try:
            config = self.load_config()
            updated_config = GraphRAGIntegrationConfig.from_dict({
                **config.to_dict(),
                **updates
            })
            self._config = updated_config
            return self.save_config()
            
        except Exception as e:
            print(f"Error updating GraphRAG config: {e}")
            return False
    
    def validate_config(self) -> List[str]:
        """Validate current configuration and return list of issues"""
        issues = []
        config = self.load_config()
        
        # Validate vector database config
        if not config.vector_db.host:
            issues.append("Vector database host not configured")
        
        if config.vector_db.port <= 0:
            issues.append("Invalid vector database port")
        
        # Validate graph database config
        if not config.graph_db.uri:
            issues.append("Graph database URI not configured")
        
        if not config.graph_db.user or not config.graph_db.password:
            issues.append("Graph database credentials not configured")
        
        # Validate embedding config
        if config.embedding.provider == "openai" and not config.embedding.openai_api_key:
            issues.append("OpenAI API key required for OpenAI embeddings")
        
        # Validate file size limits
        if config.processing.max_file_size_mb <= 0:
            issues.append("Invalid maximum file size")
        
        # Validate chunk size
        if config.chunking.chunk_size <= 0:
            issues.append("Invalid chunk size")
        
        if config.chunking.chunk_overlap >= config.chunking.chunk_size:
            issues.append("Chunk overlap should be less than chunk size")
        
        return issues


# Global configuration manager instance
config_manager = GraphRAGConfigManager()

def get_graphrag_config() -> GraphRAGIntegrationConfig:
    """Get the global GraphRAG configuration"""
    return config_manager.get_config()

def update_graphrag_config(updates: Dict[str, Any]) -> bool:
    """Update the global GraphRAG configuration"""
    return config_manager.update_config(updates)

def validate_graphrag_config() -> List[str]:
    """Validate the global GraphRAG configuration"""
    return config_manager.validate_config()