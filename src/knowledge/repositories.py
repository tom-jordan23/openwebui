"""
Knowledge Management Repository Classes
Data access layer for GraphRAG knowledge system
"""

import time
import json
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta

from .models import (
    KnowledgeCollection, KnowledgeSource, DocumentChunk,
    KnowledgeEntity, KnowledgeRelationship, ProcessingStatus, 
    EntityType, RelationshipType
)

logger = logging.getLogger(__name__)


class KnowledgeCollectionRepository:
    """Repository for knowledge collection operations"""
    
    def __init__(self):
        # For now, use in-memory storage
        # In production, this would use actual database connections
        self._collections = {}
    
    def create(self, collection: KnowledgeCollection) -> bool:
        """Create a new knowledge collection"""
        try:
            self._collections[collection.id] = collection
            return True
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False
    
    def get_by_id(self, collection_id: str) -> Optional[KnowledgeCollection]:
        """Get collection by ID"""
        return self._collections.get(collection_id)
    
    def get_by_user(self, user_id: str) -> List[KnowledgeCollection]:
        """Get collections by user ID"""
        return [c for c in self._collections.values() if c.user_id == user_id]
    
    def update(self, collection: KnowledgeCollection) -> bool:
        """Update collection"""
        try:
            if collection.id in self._collections:
                self._collections[collection.id] = collection
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating collection: {e}")
            return False
    
    def delete(self, collection_id: str) -> bool:
        """Delete collection"""
        try:
            if collection_id in self._collections:
                del self._collections[collection_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False
    
    def update_statistics(self, collection_id: str) -> bool:
        """Update collection statistics"""
        # In production, this would calculate actual statistics
        return True


class KnowledgeSourceRepository:
    """Repository for knowledge source operations"""
    
    def __init__(self):
        self._sources = {}
        self._next_id = 1
    
    def create(self, source: KnowledgeSource) -> bool:
        """Create a new knowledge source"""
        try:
            if source.id is None:
                source.id = self._next_id
                self._next_id += 1
            self._sources[source.id] = source
            return True
        except Exception as e:
            logger.error(f"Error creating source: {e}")
            return False
    
    def get_by_id(self, source_id: int) -> Optional[KnowledgeSource]:
        """Get source by ID"""
        return self._sources.get(source_id)
    
    def get_by_collection(self, collection_id: str) -> List[KnowledgeSource]:
        """Get sources by collection ID"""
        return [s for s in self._sources.values() if s.collection_id == collection_id]
    
    def get_by_user(self, user_id: str) -> List[KnowledgeSource]:
        """Get sources by user ID"""
        return [s for s in self._sources.values() if s.user_id == user_id]
    
    def update_processing_status(self, source_id: int, status: ProcessingStatus, error: str = None) -> bool:
        """Update processing status"""
        try:
            if source_id in self._sources:
                self._sources[source_id].processing_status = status
                self._sources[source_id].last_processed_at = int(time.time() * 1000)
                if error:
                    self._sources[source_id].processing_error = error
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating processing status: {e}")
            return False
    
    def update_extraction_results(self, source_id: int, entities: int, relationships: int, chunks: int, embeddings: int) -> bool:
        """Update extraction results"""
        try:
            if source_id in self._sources:
                source = self._sources[source_id]
                source.entities_extracted = entities
                source.relationships_extracted = relationships
                source.chunks_created = chunks
                source.embeddings_generated = embeddings
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating extraction results: {e}")
            return False
    
    def delete(self, source_id: int) -> bool:
        """Delete source"""
        try:
            if source_id in self._sources:
                del self._sources[source_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting source: {e}")
            return False


class DocumentChunkRepository:
    """Repository for document chunk operations"""
    
    def __init__(self):
        self._chunks = {}
    
    def create(self, chunk: DocumentChunk) -> bool:
        """Create a document chunk"""
        try:
            self._chunks[chunk.id] = chunk
            return True
        except Exception as e:
            logger.error(f"Error creating chunk: {e}")
            return False
    
    def create_batch(self, chunks: List[DocumentChunk]) -> bool:
        """Create multiple chunks"""
        try:
            for chunk in chunks:
                self._chunks[chunk.id] = chunk
            return True
        except Exception as e:
            logger.error(f"Error creating chunks batch: {e}")
            return False
    
    def get_by_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        """Get chunk by ID"""
        return self._chunks.get(chunk_id)
    
    def get_by_source(self, source_id: int) -> List[DocumentChunk]:
        """Get chunks by source ID"""
        return [c for c in self._chunks.values() if c.source_id == source_id]
    
    def search_by_content(self, query: str, limit: int = 10) -> List[DocumentChunk]:
        """Search chunks by content"""
        results = []
        query_lower = query.lower()
        
        for chunk in self._chunks.values():
            if query_lower in chunk.content.lower():
                results.append(chunk)
                if len(results) >= limit:
                    break
        
        return results


class KnowledgeEntityRepository:
    """Repository for knowledge entity operations"""
    
    def __init__(self):
        self._entities = {}
    
    def create(self, entity: KnowledgeEntity) -> bool:
        """Create an entity"""
        try:
            self._entities[entity.id] = entity
            return True
        except Exception as e:
            logger.error(f"Error creating entity: {e}")
            return False
    
    def get_by_id(self, entity_id: str) -> Optional[KnowledgeEntity]:
        """Get entity by ID"""
        return self._entities.get(entity_id)
    
    def search_by_name(self, query: str, entity_types: List[EntityType] = None, limit: int = 20) -> List[KnowledgeEntity]:
        """Search entities by name"""
        results = []
        query_lower = query.lower()
        
        for entity in self._entities.values():
            # Check name match
            name_match = query_lower in entity.name.lower() or query_lower in entity.canonical_name.lower()
            
            # Check type filter
            type_match = not entity_types or entity.entity_type in entity_types
            
            if name_match and type_match:
                results.append(entity)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_most_central(self, limit: int = 20) -> List[KnowledgeEntity]:
        """Get most central entities by pagerank score"""
        entities = list(self._entities.values())
        entities.sort(key=lambda e: e.pagerank_score or 0, reverse=True)
        return entities[:limit]


class KnowledgeRelationshipRepository:
    """Repository for knowledge relationship operations"""
    
    def __init__(self):
        self._relationships = {}
    
    def create(self, relationship: KnowledgeRelationship) -> bool:
        """Create a relationship"""
        try:
            self._relationships[relationship.id] = relationship
            return True
        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            return False
    
    def get_by_id(self, relationship_id: str) -> Optional[KnowledgeRelationship]:
        """Get relationship by ID"""
        return self._relationships.get(relationship_id)
    
    def get_entity_relationships(self, entity_id: str, direction: str = "both", limit: int = 50) -> List[Dict[str, Any]]:
        """Get relationships for an entity"""
        results = []
        
        for rel in self._relationships.values():
            include = False
            
            if direction == "outgoing" or direction == "both":
                if rel.source_entity_id == entity_id:
                    include = True
            
            if direction == "incoming" or direction == "both":
                if rel.target_entity_id == entity_id:
                    include = True
            
            if include:
                results.append({'relationship': rel})
                if len(results) >= limit:
                    break
        
        return results
    
    def find_path(self, source_entity_id: str, target_entity_id: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        """Find paths between entities"""
        # Simplified path finding - in production would use graph algorithms
        paths = []
        
        # Direct connection check
        for rel in self._relationships.values():
            if rel.source_entity_id == source_entity_id and rel.target_entity_id == target_entity_id:
                paths.append({
                    'path': [source_entity_id, target_entity_id],
                    'depth': 1,
                    'weight': rel.weight,
                    'relationship_type': rel.relationship_type.value
                })
        
        return paths[:5]  # Limit results


class KnowledgeQueryRepository:
    """Repository for knowledge query tracking"""
    
    def __init__(self):
        self._queries = {}
    
    def record_query(self, query_text: str, user_id: str, assistant_id: str = None, 
                    results_found: int = 0, processing_time_ms: float = None) -> str:
        """Record a knowledge query"""
        try:
            import uuid
            query_id = str(uuid.uuid4())
            
            query_record = {
                'id': query_id,
                'query_text': query_text,
                'user_id': user_id,
                'assistant_id': assistant_id,
                'results_found': results_found,
                'processing_time_ms': processing_time_ms,
                'created_at': int(time.time() * 1000)
            }
            
            self._queries[query_id] = query_record
            return query_id
            
        except Exception as e:
            logger.error(f"Error recording query: {e}")
            return ""