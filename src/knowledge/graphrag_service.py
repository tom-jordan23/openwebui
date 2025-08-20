"""
GraphRAG Service
Core service for Graph-based Retrieval Augmented Generation
Integrates vector similarity search with knowledge graph traversal
"""

import logging
import time
import json
import asyncio
from typing import List, Dict, Optional, Any, Tuple, Union
from datetime import datetime
from dataclasses import dataclass

from .repositories import (
    KnowledgeCollectionRepository, KnowledgeSourceRepository,
    DocumentChunkRepository, KnowledgeEntityRepository,
    KnowledgeRelationshipRepository, KnowledgeQueryRepository
)
from .models import (
    KnowledgeCollection, KnowledgeSource, DocumentChunk,
    KnowledgeEntity, KnowledgeRelationship, RetrievalQuery, RetrievalResult,
    DocumentType, EntityType, RelationshipType
)
from .extractors import EntityExtractor, RelationshipExtractor
from .chunking import DocumentChunker
from .embeddings import EmbeddingService
# from .graph_analysis import GraphAnalyzer  # To be implemented

logger = logging.getLogger(__name__)


@dataclass
class GraphRAGConfig:
    """Configuration for GraphRAG operations"""
    # Chunking configuration
    chunk_size: int = 512
    chunk_overlap: int = 50
    chunking_strategy: str = "semantic"  # semantic, fixed, sentence
    
    # Embedding configuration
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    embedding_dimension: int = 768
    batch_size: int = 32
    
    # Entity extraction configuration
    entity_extraction_model: str = "spacy"  # spacy, transformers, openai
    entity_confidence_threshold: float = 0.7
    max_entities_per_chunk: int = 10
    
    # Relationship extraction configuration
    relationship_extraction_model: str = "openie"  # openie, rebel, custom
    relationship_confidence_threshold: float = 0.6
    max_relationships_per_chunk: int = 15
    
    # Graph analysis configuration
    enable_centrality_metrics: bool = True
    pagerank_iterations: int = 100
    pagerank_damping: float = 0.85
    
    # Retrieval configuration
    vector_search_limit: int = 50
    graph_expansion_depth: int = 2
    similarity_threshold: float = 0.7
    graph_weight: float = 0.3  # Weight for graph-based scores vs vector similarity
    
    # Performance configuration
    async_processing: bool = True
    max_concurrent_jobs: int = 5
    enable_caching: bool = True
    cache_ttl_hours: int = 24


class GraphRAGService:
    """Core GraphRAG service integrating vector search with knowledge graphs"""
    
    def __init__(self, config: GraphRAGConfig = None):
        self.config = config or GraphRAGConfig()
        
        # Initialize repositories
        self.collection_repo = KnowledgeCollectionRepository()
        self.source_repo = KnowledgeSourceRepository()
        self.chunk_repo = DocumentChunkRepository()
        self.entity_repo = KnowledgeEntityRepository()
        self.relationship_repo = KnowledgeRelationshipRepository()
        self.query_repo = KnowledgeQueryRepository()
        
        # Initialize processing components
        self.chunker = DocumentChunker()
        self.entity_extractor = EntityExtractor()
        self.relationship_extractor = RelationshipExtractor()
        self.embedding_service = EmbeddingService()
        self.graph_analyzer = None  # GraphAnalyzer(self.config) - To be implemented
        
        # Processing state
        self.processing_queue = asyncio.Queue()
        self.active_jobs = set()
    
    async def create_collection(self, name: str, description: str, user_id: str,
                              custom_config: Dict[str, Any] = None) -> Tuple[bool, Union[KnowledgeCollection, str]]:
        """Create a new knowledge collection"""
        try:
            collection = KnowledgeCollection(
                name=name,
                description=description,
                user_id=user_id,
                chunking_strategy=custom_config.get('chunking_strategy', self.config.chunking_strategy),
                embedding_model=custom_config.get('embedding_model', self.config.embedding_model),
                chunk_size=custom_config.get('chunk_size', self.config.chunk_size),
                chunk_overlap=custom_config.get('chunk_overlap', self.config.chunk_overlap),
                custom_settings=custom_config or {}
            )
            
            if self.collection_repo.create(collection):
                return True, collection
            else:
                return False, "Failed to create collection in database"
                
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False, f"Internal error: {str(e)}"
    
    async def add_document(self, collection_id: str, file_path: str, file_name: str,
                          user_id: str, document_type: DocumentType = None,
                          custom_metadata: Dict[str, Any] = None) -> Tuple[bool, Union[KnowledgeSource, str]]:
        """Add a document to a knowledge collection"""
        try:
            # Verify collection exists and user has access
            collection = self.collection_repo.get_by_id(collection_id)
            if not collection:
                return False, "Collection not found"
            
            if collection.user_id != user_id:
                return False, "Access denied"
            
            # Auto-detect document type if not provided
            if document_type is None:
                document_type = self._detect_document_type(file_name)
            
            # Create knowledge source
            source = KnowledgeSource(
                name=file_name,
                source_type=document_type,
                source_path=file_path,
                original_filename=file_name,
                user_id=user_id,
                collection_id=collection_id,
                custom_metadata=custom_metadata or {}
            )
            
            if self.source_repo.create(source):
                # Queue for processing
                if self.config.async_processing:
                    await self._queue_document_processing(source)
                else:
                    await self._process_document_sync(source)
                
                return True, source
            else:
                return False, "Failed to create knowledge source"
                
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False, f"Internal error: {str(e)}"
    
    async def process_document_pipeline(self, source: KnowledgeSource) -> bool:
        """Complete document processing pipeline"""
        try:
            logger.info(f"Starting processing pipeline for source {source.id}")
            
            # Update status to processing
            self.source_repo.update_processing_status(source.id, ProcessingStatus.PROCESSING)
            
            # Step 1: Extract text content
            extracted_text = await self._extract_text_content(source)
            if not extracted_text:
                self.source_repo.update_processing_status(
                    source.id, ProcessingStatus.FAILED, "Failed to extract text content"
                )
                return False
            
            # Step 2: Chunk the document
            chunks = await self._chunk_document(source, extracted_text)
            if not chunks:
                self.source_repo.update_processing_status(
                    source.id, ProcessingStatus.FAILED, "Failed to chunk document"
                )
                return False
            
            # Step 3: Create embeddings for chunks
            embedded_chunks = await self._create_embeddings(chunks)
            
            # Step 4: Extract entities and relationships
            entities, relationships = await self._extract_knowledge_graph(chunks)
            
            # Step 5: Store all data
            await self._store_processing_results(source, embedded_chunks, entities, relationships)
            
            # Step 6: Update graph metrics
            await self._update_graph_metrics(source.collection_id)
            
            # Update final status
            self.source_repo.update_processing_status(source.id, ProcessingStatus.COMPLETED)
            self.source_repo.update_extraction_results(
                source.id, len(entities), len(relationships), len(chunks), len(embedded_chunks)
            )
            
            # Update collection statistics
            self.collection_repo.update_statistics(source.collection_id)
            
            logger.info(f"Completed processing pipeline for source {source.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error in processing pipeline: {e}")
            self.source_repo.update_processing_status(
                source.id, ProcessingStatus.FAILED, str(e)
            )
            return False
    
    async def hybrid_search(self, query: str, collection_ids: List[str] = None,
                           user_id: str = "", assistant_id: str = None,
                           max_results: int = 10, similarity_threshold: float = None,
                           use_graph_expansion: bool = True, entity_types: List[EntityType] = None) -> List[RetrievalResult]:
        """Perform hybrid search combining vector similarity and graph traversal"""
        start_time = time.time()
        
        try:
            # Use config defaults if not specified
            if similarity_threshold is None:
                similarity_threshold = self.config.similarity_threshold
            
            # Step 1: Vector similarity search
            vector_results = await self._vector_search(
                query, collection_ids, max_results * 2, similarity_threshold
            )
            
            # Step 2: Entity-based search
            entity_results = await self._entity_search(query, entity_types, collection_ids)
            
            # Step 3: Graph expansion if enabled
            graph_expanded_results = []
            if use_graph_expansion and entity_results:
                graph_expanded_results = await self._graph_expansion_search(
                    entity_results, self.config.graph_expansion_depth, collection_ids
                )
            
            # Step 4: Combine and rank results
            combined_results = await self._combine_and_rank_results(
                vector_results, entity_results, graph_expanded_results, query
            )
            
            # Step 5: Limit to requested number of results
            final_results = combined_results[:max_results]
            
            # Step 6: Record query for analytics
            processing_time = (time.time() - start_time) * 1000
            query_id = self.query_repo.record_query(
                query, user_id, assistant_id, len(final_results), processing_time
            )
            
            # Add query_id to results
            for result in final_results:
                result.query_id = query_id
            
            logger.info(f"Hybrid search completed: {len(final_results)} results in {processing_time:.2f}ms")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []
    
    async def get_entity_context(self, entity_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get comprehensive context for an entity including relationships"""
        try:
            # Get the entity
            entity = self.entity_repo.get_by_id(entity_id)
            if not entity:
                return {}
            
            # Get direct relationships
            relationships = self.relationship_repo.get_entity_relationships(
                entity_id, "both", limit=50
            )
            
            # Get related entities
            related_entities = []
            for rel_data in relationships:
                rel = rel_data['relationship']
                if rel.source_entity_id != entity_id:
                    related_entity = self.entity_repo.get_by_id(rel.source_entity_id)
                    if related_entity:
                        related_entities.append(related_entity)
                if rel.target_entity_id != entity_id:
                    related_entity = self.entity_repo.get_by_id(rel.target_entity_id)
                    if related_entity:
                        related_entities.append(related_entity)
            
            # Get source documents
            source_chunks = []
            if entity.source_documents:
                for doc_id in entity.source_documents[:10]:  # Limit to recent documents
                    chunks = self.chunk_repo.get_by_source(doc_id)
                    relevant_chunks = [
                        chunk for chunk in chunks 
                        if entity_id in chunk.entities_mentioned
                    ]
                    source_chunks.extend(relevant_chunks[:3])  # Limit chunks per document
            
            return {
                'entity': entity,
                'relationships': relationships[:20],  # Limit relationships
                'related_entities': related_entities[:15],  # Limit related entities
                'source_chunks': source_chunks,
                'centrality_metrics': {
                    'degree_centrality': entity.degree_centrality,
                    'betweenness_centrality': entity.betweenness_centrality,
                    'pagerank_score': entity.pagerank_score
                },
                'total_relationships': len(relationships),
                'total_related_entities': len(related_entities)
            }
            
        except Exception as e:
            logger.error(f"Error getting entity context: {e}")
            return {}
    
    async def find_entity_path(self, source_entity_id: str, target_entity_id: str,
                              max_depth: int = 3) -> List[Dict[str, Any]]:
        """Find connection paths between two entities"""
        try:
            paths = self.relationship_repo.find_path(source_entity_id, target_entity_id, max_depth)
            
            # Enrich paths with entity information
            enriched_paths = []
            for path in paths:
                # Get entity names for the path
                entity_names = []
                for entity_id in path['path']:
                    entity = self.entity_repo.get_by_id(entity_id)
                    if entity:
                        entity_names.append(entity.name)
                
                enriched_paths.append({
                    'path_entities': path['path'],
                    'path_names': entity_names,
                    'depth': path['depth'],
                    'weight': path['weight'],
                    'relationship_type': path['relationship_type']
                })
            
            return enriched_paths
            
        except Exception as e:
            logger.error(f"Error finding entity path: {e}")
            return []
    
    async def get_collection_insights(self, collection_id: str) -> Dict[str, Any]:
        """Get insights and analytics for a knowledge collection"""
        try:
            collection = self.collection_repo.get_by_id(collection_id)
            if not collection:
                return {}
            
            # Get sources
            sources = self.source_repo.get_by_collection(collection_id)
            
            # Get top entities by centrality
            # This is a simplified version - would need to filter by collection
            top_entities = self.entity_repo.get_most_central(20)
            
            # Calculate processing statistics
            processing_stats = {
                'total_sources': len(sources),
                'completed_sources': len([s for s in sources if s.processing_status == ProcessingStatus.COMPLETED]),
                'failed_sources': len([s for s in sources if s.processing_status == ProcessingStatus.FAILED]),
                'pending_sources': len([s for s in sources if s.processing_status == ProcessingStatus.PENDING]),
                'total_entities': collection.total_entities,
                'total_relationships': collection.total_relationships,
                'total_chunks': collection.total_chunks
            }
            
            # Document type distribution
            doc_types = {}
            for source in sources:
                doc_type = source.source_type.value
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            return {
                'collection': collection,
                'processing_stats': processing_stats,
                'document_types': doc_types,
                'top_entities': top_entities[:10],  # Top 10 most central entities
                'last_updated': collection.last_updated,
                'configuration': {
                    'chunking_strategy': collection.chunking_strategy,
                    'embedding_model': collection.embedding_model,
                    'chunk_size': collection.chunk_size,
                    'chunk_overlap': collection.chunk_overlap
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting collection insights: {e}")
            return {}
    
    # Private helper methods
    
    async def _queue_document_processing(self, source: KnowledgeSource):
        """Queue document for asynchronous processing"""
        try:
            await self.processing_queue.put(source)
            
            # Start processing if we have available capacity
            if len(self.active_jobs) < self.config.max_concurrent_jobs:
                task = asyncio.create_task(self._process_document_worker())
                self.active_jobs.add(task)
                task.add_done_callback(self.active_jobs.discard)
                
        except Exception as e:
            logger.error(f"Error queuing document processing: {e}")
    
    async def _process_document_worker(self):
        """Worker for processing documents from queue"""
        try:
            while not self.processing_queue.empty():
                source = await self.processing_queue.get()
                await self.process_document_pipeline(source)
                self.processing_queue.task_done()
                
        except Exception as e:
            logger.error(f"Error in document processing worker: {e}")
    
    async def _process_document_sync(self, source: KnowledgeSource):
        """Process document synchronously"""
        return await self.process_document_pipeline(source)
    
    def _detect_document_type(self, filename: str) -> DocumentType:
        """Auto-detect document type from filename"""
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        type_mapping = {
            'pdf': DocumentType.PDF,
            'txt': DocumentType.TEXT,
            'md': DocumentType.MARKDOWN,
            'html': DocumentType.HTML,
            'htm': DocumentType.HTML,
            'csv': DocumentType.CSV,
            'json': DocumentType.JSON,
            'py': DocumentType.CODE,
            'js': DocumentType.CODE,
            'java': DocumentType.CODE,
            'cpp': DocumentType.CODE,
            'jpg': DocumentType.IMAGE,
            'jpeg': DocumentType.IMAGE,
            'png': DocumentType.IMAGE,
            'gif': DocumentType.IMAGE,
            'mp3': DocumentType.AUDIO,
            'wav': DocumentType.AUDIO,
            'mp4': DocumentType.VIDEO,
            'avi': DocumentType.VIDEO
        }
        
        return type_mapping.get(extension, DocumentType.TEXT)
    
    async def _extract_text_content(self, source: KnowledgeSource) -> str:
        """Extract text content from document"""
        # Placeholder implementation
        # In production, this would handle different file types
        try:
            with open(source.source_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
            return ""
    
    async def _chunk_document(self, source: KnowledgeSource, text: str) -> List[DocumentChunk]:
        """Chunk document into smaller pieces"""
        if self.chunker:
            return self.chunker.chunk_text(text, source.id)
        
        # Fallback implementation - simple fixed-size chunking
        chunks = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        
        for i in range(0, len(text), chunk_size - overlap):
            chunk_text = text[i:i + chunk_size]
            if chunk_text.strip():
                chunk = DocumentChunk(
                    source_id=source.id,
                    chunk_index=len(chunks),
                    content=chunk_text,
                    start_position=i,
                    end_position=min(i + chunk_size, len(text)),
                    character_count=len(chunk_text)
                )
                chunks.append(chunk)
        
        return chunks
    
    async def _create_embeddings(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Create embeddings for document chunks"""
        if self.embedding_service and chunks:
            try:
                # Extract text from chunks
                texts = [chunk.content for chunk in chunks]
                
                # Generate embeddings
                embedding_results = await self.embedding_service.embed_texts(texts)
                
                # Update chunks with embeddings
                for chunk, result in zip(chunks, embedding_results):
                    if result:
                        chunk.embedding_vector = result.embedding
                        chunk.embedding_model = result.model
                        chunk.embedding_dimension = result.dimension
                
                return chunks
                
            except Exception as e:
                logger.error(f"Error creating embeddings: {e}")
        
        # Fallback implementation
        for chunk in chunks:
            # Fake embedding vector
            chunk.embedding_vector = [0.1] * self.config.embedding_dimension
            chunk.embedding_model = self.config.embedding_model
            chunk.embedding_dimension = self.config.embedding_dimension
        
        return chunks
    
    async def _extract_knowledge_graph(self, chunks: List[DocumentChunk]) -> Tuple[List[KnowledgeEntity], List[KnowledgeRelationship]]:
        """Extract entities and relationships from chunks"""
        entities = []
        relationships = []
        
        if self.entity_extractor and self.relationship_extractor and chunks:
            try:
                all_entities = []
                all_relationships = []
                
                for chunk in chunks:
                    # Extract entities from chunk
                    chunk_entities = self.entity_extractor.extract_entities(
                        chunk.content, chunk.id, chunk.source_id
                    )
                    all_entities.extend(chunk_entities)
                    
                    # Extract relationships from chunk (if we have entities)
                    if chunk_entities:
                        chunk_relationships = self.relationship_extractor.extract_relationships(
                            chunk.content, chunk_entities, chunk.id, chunk.source_id
                        )
                        all_relationships.extend(chunk_relationships)
                
                entities = all_entities
                relationships = all_relationships
                
            except Exception as e:
                logger.error(f"Error extracting knowledge graph: {e}")
        
        return entities, relationships
    
    async def _store_processing_results(self, source: KnowledgeSource, chunks: List[DocumentChunk],
                                      entities: List[KnowledgeEntity], relationships: List[KnowledgeRelationship]):
        """Store all processing results in database"""
        try:
            # Store chunks
            if chunks:
                self.chunk_repo.create_batch(chunks)
            
            # Store entities
            for entity in entities:
                self.entity_repo.create(entity)
            
            # Store relationships
            for relationship in relationships:
                self.relationship_repo.create(relationship)
                
        except Exception as e:
            logger.error(f"Error storing processing results: {e}")
            raise
    
    async def _update_graph_metrics(self, collection_id: str):
        """Update graph centrality metrics for collection"""
        # Placeholder implementation
        # In production, this would calculate actual centrality metrics
        pass
    
    async def _vector_search(self, query: str, collection_ids: List[str], limit: int, threshold: float) -> List[Dict[str, Any]]:
        """Perform vector similarity search"""
        # Placeholder implementation
        # In production, this would use actual vector similarity search
        return []
    
    async def _entity_search(self, query: str, entity_types: List[EntityType], collection_ids: List[str]) -> List[Dict[str, Any]]:
        """Search for entities matching query"""
        entities = self.entity_repo.search_by_name(query, entity_types, 20)
        return [{'entity': entity, 'score': 0.8} for entity in entities]
    
    async def _graph_expansion_search(self, entity_results: List[Dict[str, Any]], depth: int, collection_ids: List[str]) -> List[Dict[str, Any]]:
        """Expand search using graph relationships"""
        # Placeholder implementation
        return []
    
    async def _combine_and_rank_results(self, vector_results: List[Dict[str, Any]], 
                                      entity_results: List[Dict[str, Any]], 
                                      graph_results: List[Dict[str, Any]], 
                                      query: str) -> List[RetrievalResult]:
        """Combine and rank all search results"""
        # Placeholder implementation
        # In production, this would implement sophisticated ranking algorithms
        all_results = []
        
        # Convert entity results to RetrievalResult objects
        for i, entity_result in enumerate(entity_results):
            entity = entity_result['entity']
            result = RetrievalResult(
                source_type="entity",
                source_id=entity.id,
                content=f"{entity.name}: {entity.description or 'No description'}",
                similarity_score=entity_result['score'],
                relevance_score=entity_result['score'],
                combined_score=entity_result['score']
            )
            all_results.append(result)
        
        # Sort by combined score
        all_results.sort(key=lambda x: x.combined_score, reverse=True)
        
        return all_results