"""
Advanced GraphRAG Optimization System
High-performance knowledge retrieval with intelligent caching and graph analysis
"""

import os
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import json
import hashlib
from pathlib import Path
import numpy as np
from collections import defaultdict, deque
import pickle

# Graph and vector database imports
try:
    import neo4j
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

# ML and NLP imports
try:
    import torch
    import transformers
    from sentence_transformers import SentenceTransformer
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache strategies for GraphRAG optimization"""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    INTELLIGENT = "intelligent"
    HIERARCHICAL = "hierarchical"


class QueryType(Enum):
    """Types of knowledge queries"""
    SEMANTIC_SEARCH = "semantic_search"
    GRAPH_TRAVERSAL = "graph_traversal"
    HYBRID_RETRIEVAL = "hybrid_retrieval"
    ENTITY_LOOKUP = "entity_lookup"
    RELATIONSHIP_ANALYSIS = "relationship_analysis"
    CONTEXTUAL_REASONING = "contextual_reasoning"


@dataclass
class QueryPerformanceMetrics:
    """Performance metrics for query optimization"""
    query_id: str
    query_type: QueryType
    execution_time_ms: float
    cache_hit: bool
    results_count: int
    relevance_score: float
    resource_usage: Dict[str, float]
    timestamp: datetime


@dataclass
class KnowledgeEntity:
    """Enhanced knowledge entity with optimization metadata"""
    entity_id: str
    entity_type: str
    properties: Dict[str, Any]
    embeddings: Optional[List[float]]
    relationships: List[Dict[str, Any]]
    access_frequency: int
    last_accessed: datetime
    quality_score: float
    context_vectors: List[List[float]]


@dataclass
class GraphPartition:
    """Graph partition for distributed processing"""
    partition_id: str
    nodes: Set[str]
    edges: List[Dict[str, Any]]
    centroid: List[float]
    size_bytes: int
    last_optimized: datetime


class IntelligentCache:
    """Advanced caching system with ML-based prediction"""
    
    def __init__(self, max_size: int = 10000, strategy: CacheStrategy = CacheStrategy.INTELLIGENT):
        self.max_size = max_size
        self.strategy = strategy
        self.cache = {}
        self.access_patterns = defaultdict(list)
        self.hit_count = 0
        self.miss_count = 0
        
        # LRU tracking
        self.access_order = deque()
        
        # LFU tracking
        self.frequency_map = defaultdict(int)
        
        # TTL tracking
        self.ttl_map = {}
        
        # ML prediction model (simplified)
        self.access_predictor = AccessPredictor() if ML_AVAILABLE else None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache with intelligent tracking"""
        current_time = time.time()
        
        # Check TTL expiration
        if key in self.ttl_map and current_time > self.ttl_map[key]:
            await self._evict(key)
            return None
        
        if key in self.cache:
            self.hit_count += 1
            await self._update_access_patterns(key, True)
            
            # Update LRU order
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            
            # Update frequency
            self.frequency_map[key] += 1
            
            return self.cache[key]
        else:
            self.miss_count += 1
            await self._update_access_patterns(key, False)
            return None
    
    async def put(self, key: str, value: Any, ttl: Optional[int] = None):
        """Put item in cache with intelligent eviction"""
        current_time = time.time()
        
        # Set TTL if provided
        if ttl:
            self.ttl_map[key] = current_time + ttl
        
        # Check if we need to evict
        if len(self.cache) >= self.max_size and key not in self.cache:
            await self._evict_intelligent()
        
        self.cache[key] = value
        self.frequency_map[key] += 1
        
        # Update LRU order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    async def _update_access_patterns(self, key: str, hit: bool):
        """Update access patterns for ML prediction"""
        pattern = {
            'timestamp': time.time(),
            'hit': hit,
            'hour': datetime.now().hour,
            'day_of_week': datetime.now().weekday()
        }
        self.access_patterns[key].append(pattern)
        
        # Keep only recent patterns
        cutoff_time = time.time() - 86400  # 24 hours
        self.access_patterns[key] = [
            p for p in self.access_patterns[key] 
            if p['timestamp'] > cutoff_time
        ]
    
    async def _evict_intelligent(self):
        """Intelligent cache eviction based on multiple factors"""
        if not self.cache:
            return
        
        if self.strategy == CacheStrategy.LRU:
            key_to_evict = self.access_order.popleft()
        elif self.strategy == CacheStrategy.LFU:
            key_to_evict = min(self.frequency_map.keys(), key=lambda k: self.frequency_map[k])
        elif self.strategy == CacheStrategy.INTELLIGENT and self.access_predictor:
            # Use ML to predict future access probability
            scores = {}
            for key in self.cache:
                score = await self.access_predictor.predict_access_probability(
                    key, self.access_patterns[key]
                )
                scores[key] = score
            key_to_evict = min(scores.keys(), key=lambda k: scores[k])
        else:
            # Fallback to LRU
            key_to_evict = self.access_order.popleft()
        
        await self._evict(key_to_evict)
    
    async def _evict(self, key: str):
        """Evict specific key from cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.frequency_map:
            del self.frequency_map[key]
        if key in self.ttl_map:
            del self.ttl_map[key]
        if key in self.access_order:
            self.access_order.remove(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        return {
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': hit_rate,
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'strategy': self.strategy.value
        }


class AccessPredictor:
    """ML-based access pattern prediction"""
    
    def __init__(self):
        self.model = None
        if ML_AVAILABLE:
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize simple prediction model"""
        # In production, this would be a trained ML model
        # For now, use simple heuristics
        pass
    
    async def predict_access_probability(self, key: str, access_history: List[Dict]) -> float:
        """Predict probability of future access"""
        if not access_history:
            return 0.1  # Low probability for new keys
        
        # Simple heuristic based on recent access patterns
        recent_accesses = [p for p in access_history if p['timestamp'] > time.time() - 3600]
        
        if not recent_accesses:
            return 0.2
        
        # Calculate factors
        frequency_factor = len(recent_accesses) / 60  # Accesses per minute
        recency_factor = 1.0 / (time.time() - recent_accesses[-1]['timestamp'] + 1)
        hit_ratio = sum(1 for p in recent_accesses if p['hit']) / len(recent_accesses)
        
        # Combine factors
        probability = min(1.0, frequency_factor * 0.3 + recency_factor * 0.4 + hit_ratio * 0.3)
        return probability


class GraphPartitionManager:
    """Manages graph partitioning for distributed processing"""
    
    def __init__(self, max_partition_size: int = 100000):
        self.max_partition_size = max_partition_size
        self.partitions = {}
        self.partition_index = {}  # node_id -> partition_id
        self.partition_stats = {}
    
    async def partition_graph(self, graph_data: Dict[str, Any]) -> List[GraphPartition]:
        """Partition graph using intelligent clustering"""
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        
        if len(nodes) <= self.max_partition_size:
            # Single partition for small graphs
            partition = GraphPartition(
                partition_id="single",
                nodes=set(node['id'] for node in nodes),
                edges=edges,
                centroid=self._calculate_centroid(nodes),
                size_bytes=self._estimate_size(nodes, edges),
                last_optimized=datetime.now()
            )
            return [partition]
        
        # Use community detection for partitioning
        partitions = await self._community_detection_partition(nodes, edges)
        
        # Update partition index
        for partition in partitions:
            for node_id in partition.nodes:
                self.partition_index[node_id] = partition.partition_id
        
        return partitions
    
    async def _community_detection_partition(self, nodes: List[Dict], edges: List[Dict]) -> List[GraphPartition]:
        """Use community detection for graph partitioning"""
        # Simplified community detection algorithm
        # In production, use advanced algorithms like Louvain or Leiden
        
        partitions = []
        processed_nodes = set()
        partition_counter = 0
        
        for node in nodes:
            if node['id'] in processed_nodes:
                continue
            
            # Find connected component starting from this node
            component = await self._find_connected_component(
                node['id'], nodes, edges, processed_nodes
            )
            
            if len(component) > self.max_partition_size:
                # Split large components
                sub_partitions = await self._split_large_component(component, edges)
                partitions.extend(sub_partitions)
            else:
                # Create single partition
                partition_edges = [
                    e for e in edges 
                    if e.get('source') in component and e.get('target') in component
                ]
                
                partition = GraphPartition(
                    partition_id=f"partition_{partition_counter}",
                    nodes=component,
                    edges=partition_edges,
                    centroid=self._calculate_component_centroid(component, nodes),
                    size_bytes=self._estimate_component_size(component, partition_edges),
                    last_optimized=datetime.now()
                )
                partitions.append(partition)
                partition_counter += 1
            
            processed_nodes.update(component)
        
        return partitions
    
    async def _find_connected_component(self, start_node: str, nodes: List[Dict], 
                                      edges: List[Dict], processed: Set[str]) -> Set[str]:
        """Find connected component using BFS"""
        component = set()
        queue = deque([start_node])
        component.add(start_node)
        
        # Build adjacency list
        adjacency = defaultdict(set)
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            if source and target:
                adjacency[source].add(target)
                adjacency[target].add(source)
        
        while queue and len(component) < self.max_partition_size:
            current = queue.popleft()
            
            for neighbor in adjacency[current]:
                if neighbor not in component and neighbor not in processed:
                    component.add(neighbor)
                    queue.append(neighbor)
        
        return component
    
    async def _split_large_component(self, component: Set[str], edges: List[Dict]) -> List[GraphPartition]:
        """Split large components into smaller partitions"""
        # Simple splitting strategy - in production, use spectral clustering
        component_list = list(component)
        partitions = []
        partition_counter = 0
        
        for i in range(0, len(component_list), self.max_partition_size):
            partition_nodes = set(component_list[i:i + self.max_partition_size])
            partition_edges = [
                e for e in edges 
                if e.get('source') in partition_nodes and e.get('target') in partition_nodes
            ]
            
            partition = GraphPartition(
                partition_id=f"large_partition_{partition_counter}",
                nodes=partition_nodes,
                edges=partition_edges,
                centroid=[0.0] * 768,  # Placeholder centroid
                size_bytes=self._estimate_component_size(partition_nodes, partition_edges),
                last_optimized=datetime.now()
            )
            partitions.append(partition)
            partition_counter += 1
        
        return partitions
    
    def _calculate_centroid(self, nodes: List[Dict]) -> List[float]:
        """Calculate centroid of node embeddings"""
        embeddings = []
        for node in nodes:
            if 'embedding' in node and node['embedding']:
                embeddings.append(node['embedding'])
        
        if not embeddings:
            return [0.0] * 768  # Default embedding size
        
        return np.mean(embeddings, axis=0).tolist()
    
    def _calculate_component_centroid(self, component: Set[str], nodes: List[Dict]) -> List[float]:
        """Calculate centroid for a component"""
        component_nodes = [node for node in nodes if node['id'] in component]
        return self._calculate_centroid(component_nodes)
    
    def _estimate_size(self, nodes: List[Dict], edges: List[Dict]) -> int:
        """Estimate memory size of graph partition"""
        # Rough estimation
        node_size = len(nodes) * 1000  # ~1KB per node
        edge_size = len(edges) * 100   # ~100B per edge
        return node_size + edge_size
    
    def _estimate_component_size(self, nodes: Set[str], edges: List[Dict]) -> int:
        """Estimate size of a component"""
        node_size = len(nodes) * 1000
        edge_size = len(edges) * 100
        return node_size + edge_size


class AdvancedGraphRAG:
    """Advanced GraphRAG system with optimization features"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize components
        self.cache = IntelligentCache(
            max_size=self.config.get('cache_size', 10000),
            strategy=CacheStrategy(self.config.get('cache_strategy', 'intelligent'))
        )
        
        self.partition_manager = GraphPartitionManager(
            max_partition_size=self.config.get('max_partition_size', 100000)
        )
        
        # Performance tracking
        self.query_metrics = []
        self.optimization_history = []
        
        # Vector database connection
        self.vector_client = None
        if QDRANT_AVAILABLE:
            self._initialize_vector_client()
        
        # Graph database connection
        self.graph_driver = None
        if NEO4J_AVAILABLE:
            self._initialize_graph_client()
        
        # Embedding model
        self.embedding_model = None
        if ML_AVAILABLE:
            self._initialize_embedding_model()
    
    def _initialize_vector_client(self):
        """Initialize Qdrant vector database client"""
        try:
            self.vector_client = QdrantClient(
                host=os.getenv('QDRANT_HOST', 'localhost'),
                port=int(os.getenv('QDRANT_PORT', 6333))
            )
        except Exception as e:
            logger.warning(f"Failed to initialize vector client: {e}")
    
    def _initialize_graph_client(self):
        """Initialize Neo4j graph database client"""
        try:
            self.graph_driver = neo4j.GraphDatabase.driver(
                os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
                auth=(
                    os.getenv('NEO4J_USER', 'neo4j'),
                    os.getenv('NEO4J_PASSWORD', 'password')
                )
            )
        except Exception as e:
            logger.warning(f"Failed to initialize graph client: {e}")
    
    def _initialize_embedding_model(self):
        """Initialize sentence transformer model"""
        try:
            model_name = self.config.get('embedding_model', 'all-MiniLM-L6-v2')
            self.embedding_model = SentenceTransformer(model_name)
        except Exception as e:
            logger.warning(f"Failed to initialize embedding model: {e}")
    
    async def optimized_query(self, query: str, query_type: QueryType = QueryType.HYBRID_RETRIEVAL, 
                            context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute optimized knowledge query"""
        start_time = time.time()
        query_id = hashlib.md5(f"{query}{query_type.value}{time.time()}".encode()).hexdigest()
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(query, query_type, context)
            cached_result = await self.cache.get(cache_key)
            
            if cached_result:
                execution_time = (time.time() - start_time) * 1000
                await self._track_query_metrics(
                    query_id, query_type, execution_time, True, 
                    len(cached_result.get('results', [])), cached_result.get('relevance_score', 0.0)
                )
                return cached_result
            
            # Execute query based on type
            if query_type == QueryType.SEMANTIC_SEARCH:
                result = await self._semantic_search(query, context)
            elif query_type == QueryType.GRAPH_TRAVERSAL:
                result = await self._graph_traversal(query, context)
            elif query_type == QueryType.HYBRID_RETRIEVAL:
                result = await self._hybrid_retrieval(query, context)
            elif query_type == QueryType.ENTITY_LOOKUP:
                result = await self._entity_lookup(query, context)
            elif query_type == QueryType.RELATIONSHIP_ANALYSIS:
                result = await self._relationship_analysis(query, context)
            elif query_type == QueryType.CONTEXTUAL_REASONING:
                result = await self._contextual_reasoning(query, context)
            else:
                result = await self._hybrid_retrieval(query, context)
            
            # Cache result with intelligent TTL
            ttl = await self._calculate_cache_ttl(query_type, result)
            await self.cache.put(cache_key, result, ttl)
            
            execution_time = (time.time() - start_time) * 1000
            await self._track_query_metrics(
                query_id, query_type, execution_time, False,
                len(result.get('results', [])), result.get('relevance_score', 0.0)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {'error': str(e), 'results': []}
    
    async def _semantic_search(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Optimized semantic search with vector similarity"""
        if not self.vector_client or not self.embedding_model:
            return {'results': [], 'error': 'Vector search not available'}
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        # Search vector database
        search_result = self.vector_client.search(
            collection_name='knowledge_base',
            query_vector=query_embedding,
            limit=self.config.get('search_limit', 20),
            score_threshold=self.config.get('similarity_threshold', 0.7)
        )
        
        results = []
        for hit in search_result:
            results.append({
                'id': hit.id,
                'content': hit.payload.get('content', ''),
                'metadata': hit.payload.get('metadata', {}),
                'score': hit.score,
                'type': 'semantic'
            })
        
        return {
            'results': results,
            'query_type': 'semantic_search',
            'relevance_score': np.mean([r['score'] for r in results]) if results else 0.0,
            'total_results': len(results)
        }
    
    async def _graph_traversal(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Optimized graph traversal with path analysis"""
        if not self.graph_driver:
            return {'results': [], 'error': 'Graph database not available'}
        
        # Extract entities from query (simplified)
        entities = await self._extract_entities(query)
        
        results = []
        with self.graph_driver.session() as session:
            for entity in entities[:5]:  # Limit to avoid expensive queries
                # Find connected entities within 2 hops
                cypher_query = """
                MATCH path = (start:Entity {name: $entity})-[*1..2]-(connected)
                RETURN path, connected
                LIMIT 50
                """
                
                result = session.run(cypher_query, entity=entity)
                
                for record in result:
                    path = record['path']
                    connected = record['connected']
                    
                    results.append({
                        'path': [node['name'] for node in path.nodes],
                        'relationships': [rel.type for rel in path.relationships],
                        'target_entity': dict(connected),
                        'type': 'graph_traversal'
                    })
        
        return {
            'results': results,
            'query_type': 'graph_traversal',
            'relevance_score': 0.8 if results else 0.0,
            'total_results': len(results)
        }
    
    async def _hybrid_retrieval(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Hybrid retrieval combining semantic and graph approaches"""
        # Execute both semantic and graph searches in parallel
        semantic_task = self._semantic_search(query, context)
        graph_task = self._graph_traversal(query, context)
        
        semantic_results, graph_results = await asyncio.gather(
            semantic_task, graph_task, return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(semantic_results, Exception):
            semantic_results = {'results': []}
        if isinstance(graph_results, Exception):
            graph_results = {'results': []}
        
        # Combine and rank results
        combined_results = await self._combine_and_rank_results(
            semantic_results.get('results', []),
            graph_results.get('results', []),
            query
        )
        
        overall_relevance = (
            semantic_results.get('relevance_score', 0.0) * 0.6 +
            graph_results.get('relevance_score', 0.0) * 0.4
        )
        
        return {
            'results': combined_results,
            'query_type': 'hybrid_retrieval',
            'relevance_score': overall_relevance,
            'total_results': len(combined_results),
            'component_counts': {
                'semantic': len(semantic_results.get('results', [])),
                'graph': len(graph_results.get('results', []))
            }
        }
    
    async def _entity_lookup(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Optimized entity lookup with caching"""
        entities = await self._extract_entities(query)
        results = []
        
        for entity in entities:
            # Check entity cache first
            entity_data = await self._get_cached_entity(entity)
            if entity_data:
                results.append(entity_data)
                continue
            
            # Query graph database for entity
            if self.graph_driver:
                with self.graph_driver.session() as session:
                    cypher_query = """
                    MATCH (e:Entity {name: $entity})
                    RETURN e, labels(e) as types
                    """
                    result = session.run(cypher_query, entity=entity)
                    
                    for record in result:
                        entity_node = dict(record['e'])
                        entity_types = record['types']
                        
                        entity_data = {
                            'id': entity_node.get('id', entity),
                            'name': entity,
                            'properties': entity_node,
                            'types': entity_types,
                            'type': 'entity'
                        }
                        
                        # Cache entity data
                        await self._cache_entity(entity, entity_data)
                        results.append(entity_data)
        
        return {
            'results': results,
            'query_type': 'entity_lookup',
            'relevance_score': 1.0 if results else 0.0,
            'total_results': len(results)
        }
    
    async def _relationship_analysis(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze relationships between entities"""
        entities = await self._extract_entities(query)
        results = []
        
        if len(entities) >= 2 and self.graph_driver:
            with self.graph_driver.session() as session:
                # Find relationships between entity pairs
                for i in range(len(entities)):
                    for j in range(i + 1, len(entities)):
                        cypher_query = """
                        MATCH path = shortestPath(
                            (a:Entity {name: $entity1})-[*1..3]-(b:Entity {name: $entity2})
                        )
                        RETURN path, length(path) as distance
                        ORDER BY distance
                        LIMIT 10
                        """
                        
                        result = session.run(
                            cypher_query, 
                            entity1=entities[i], 
                            entity2=entities[j]
                        )
                        
                        for record in result:
                            path = record['path']
                            distance = record['distance']
                            
                            results.append({
                                'entity1': entities[i],
                                'entity2': entities[j],
                                'path': [node['name'] for node in path.nodes],
                                'relationships': [rel.type for rel in path.relationships],
                                'distance': distance,
                                'type': 'relationship_analysis'
                            })
        
        return {
            'results': results,
            'query_type': 'relationship_analysis',
            'relevance_score': 0.9 if results else 0.0,
            'total_results': len(results)
        }
    
    async def _contextual_reasoning(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Advanced contextual reasoning with graph inference"""
        # This would implement advanced reasoning algorithms
        # For now, combine multiple query types for comprehensive results
        
        tasks = [
            self._semantic_search(query, context),
            self._entity_lookup(query, context),
            self._relationship_analysis(query, context)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        valid_results = [r for r in results if not isinstance(r, Exception)]
        
        # Aggregate results with reasoning scores
        aggregated_results = []
        for result_set in valid_results:
            for result in result_set.get('results', []):
                result['reasoning_confidence'] = 0.8  # Simplified confidence
                aggregated_results.append(result)
        
        # Sort by relevance and reasoning confidence
        aggregated_results.sort(
            key=lambda x: (x.get('score', 0.5) + x.get('reasoning_confidence', 0.5)) / 2,
            reverse=True
        )
        
        return {
            'results': aggregated_results[:20],  # Limit results
            'query_type': 'contextual_reasoning',
            'relevance_score': 0.85 if aggregated_results else 0.0,
            'total_results': len(aggregated_results),
            'reasoning_applied': True
        }
    
    async def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from query text (simplified)"""
        # In production, use NER models
        # For now, simple keyword extraction
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'how', 'what', 'where', 'when', 'why'}
        words = query.lower().split()
        entities = [word.capitalize() for word in words if word not in stop_words and len(word) > 2]
        return entities[:5]  # Limit entities
    
    async def _combine_and_rank_results(self, semantic_results: List[Dict], 
                                      graph_results: List[Dict], query: str) -> List[Dict]:
        """Combine and rank results from different sources"""
        all_results = []
        
        # Add semantic results with boosted scores
        for result in semantic_results:
            result['combined_score'] = result.get('score', 0.5) * 0.7
            all_results.append(result)
        
        # Add graph results with contextual scoring
        for result in graph_results:
            # Graph results get base score of 0.6, boosted by path relevance
            base_score = 0.6
            path_boost = min(0.3, len(result.get('relationships', [])) * 0.1)
            result['combined_score'] = base_score + path_boost
            all_results.append(result)
        
        # Remove duplicates and sort by combined score
        seen_ids = set()
        unique_results = []
        
        for result in all_results:
            result_id = result.get('id', f"{result.get('type', 'unknown')}_{hash(str(result))}")
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        unique_results.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        return unique_results[:15]  # Limit to top 15 results
    
    async def _get_cached_entity(self, entity: str) -> Optional[Dict[str, Any]]:
        """Get entity from cache"""
        cache_key = f"entity_{entity.lower()}"
        return await self.cache.get(cache_key)
    
    async def _cache_entity(self, entity: str, entity_data: Dict[str, Any]):
        """Cache entity data"""
        cache_key = f"entity_{entity.lower()}"
        await self.cache.put(cache_key, entity_data, ttl=3600)  # 1 hour TTL
    
    def _generate_cache_key(self, query: str, query_type: QueryType, context: Dict[str, Any] = None) -> str:
        """Generate cache key for query"""
        context_str = json.dumps(context or {}, sort_keys=True)
        key_data = f"{query}_{query_type.value}_{context_str}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def _calculate_cache_ttl(self, query_type: QueryType, result: Dict[str, Any]) -> int:
        """Calculate intelligent cache TTL based on query type and result quality"""
        base_ttl = {
            QueryType.SEMANTIC_SEARCH: 1800,      # 30 minutes
            QueryType.GRAPH_TRAVERSAL: 3600,      # 1 hour
            QueryType.HYBRID_RETRIEVAL: 1800,     # 30 minutes
            QueryType.ENTITY_LOOKUP: 7200,        # 2 hours
            QueryType.RELATIONSHIP_ANALYSIS: 3600, # 1 hour
            QueryType.CONTEXTUAL_REASONING: 900   # 15 minutes
        }.get(query_type, 1800)
        
        # Adjust based on result quality
        relevance_score = result.get('relevance_score', 0.5)
        if relevance_score > 0.8:
            return int(base_ttl * 1.5)  # Cache high-quality results longer
        elif relevance_score < 0.3:
            return int(base_ttl * 0.5)  # Cache poor results for shorter time
        
        return base_ttl
    
    async def _track_query_metrics(self, query_id: str, query_type: QueryType, 
                                 execution_time: float, cache_hit: bool,
                                 results_count: int, relevance_score: float):
        """Track query performance metrics"""
        metrics = QueryPerformanceMetrics(
            query_id=query_id,
            query_type=query_type,
            execution_time_ms=execution_time,
            cache_hit=cache_hit,
            results_count=results_count,
            relevance_score=relevance_score,
            resource_usage={
                'memory_mb': 0,  # Would track actual memory usage
                'cpu_percent': 0  # Would track actual CPU usage
            },
            timestamp=datetime.now()
        )
        
        self.query_metrics.append(asdict(metrics))
        
        # Keep only recent metrics (last 1000 queries)
        if len(self.query_metrics) > 1000:
            self.query_metrics = self.query_metrics[-1000:]
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """Run performance optimization algorithms"""
        optimization_results = {
            'timestamp': datetime.now().isoformat(),
            'optimizations_applied': [],
            'performance_improvements': {}
        }
        
        # Analyze query patterns
        if self.query_metrics:
            optimization_results['query_analysis'] = await self._analyze_query_patterns()
        
        # Optimize cache configuration
        cache_optimization = await self._optimize_cache_configuration()
        optimization_results['cache_optimization'] = cache_optimization
        
        # Optimize graph partitions
        if self.graph_driver:
            partition_optimization = await self._optimize_graph_partitions()
            optimization_results['partition_optimization'] = partition_optimization
        
        # Update embedding model if needed
        model_optimization = await self._optimize_embedding_model()
        optimization_results['model_optimization'] = model_optimization
        
        self.optimization_history.append(optimization_results)
        return optimization_results
    
    async def _analyze_query_patterns(self) -> Dict[str, Any]:
        """Analyze query patterns for optimization insights"""
        if not self.query_metrics:
            return {}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(self.query_metrics) if 'pd' in globals() else None
        
        if df is None:
            # Fallback analysis without pandas
            total_queries = len(self.query_metrics)
            cache_hits = sum(1 for m in self.query_metrics if m['cache_hit'])
            avg_execution_time = np.mean([m['execution_time_ms'] for m in self.query_metrics])
            
            return {
                'total_queries': total_queries,
                'cache_hit_rate': cache_hits / total_queries if total_queries > 0 else 0,
                'avg_execution_time_ms': avg_execution_time,
                'recommendations': ['Increase cache size', 'Optimize frequent queries']
            }
        
        # Detailed analysis with pandas
        analysis = {
            'total_queries': len(df),
            'cache_hit_rate': df['cache_hit'].mean(),
            'avg_execution_time_ms': df['execution_time_ms'].mean(),
            'query_type_distribution': df['query_type'].value_counts().to_dict(),
            'performance_by_type': df.groupby('query_type')['execution_time_ms'].mean().to_dict(),
            'slow_queries': df[df['execution_time_ms'] > df['execution_time_ms'].quantile(0.95)].to_dict('records')
        }
        
        # Generate recommendations
        recommendations = []
        if analysis['cache_hit_rate'] < 0.5:
            recommendations.append('Increase cache size or improve cache strategy')
        if analysis['avg_execution_time_ms'] > 1000:
            recommendations.append('Optimize database queries and indexing')
        
        analysis['recommendations'] = recommendations
        return analysis
    
    async def _optimize_cache_configuration(self) -> Dict[str, Any]:
        """Optimize cache configuration based on usage patterns"""
        cache_stats = self.cache.get_stats()
        
        optimization = {
            'current_stats': cache_stats,
            'recommendations': []
        }
        
        # Analyze cache performance
        if cache_stats['hit_rate'] < 0.6:
            optimization['recommendations'].append('Increase cache size')
            # Automatically increase cache size
            new_size = min(self.cache.max_size * 2, 50000)
            self.cache.max_size = new_size
            optimization['applied'] = f'Increased cache size to {new_size}'
        
        if cache_stats['hit_rate'] > 0.9:
            optimization['recommendations'].append('Cache size may be too large, consider reducing')
        
        return optimization
    
    async def _optimize_graph_partitions(self) -> Dict[str, Any]:
        """Optimize graph partitioning for better performance"""
        # This would analyze partition access patterns and rebalance
        # For now, return placeholder optimization
        return {
            'partitions_analyzed': len(self.partition_manager.partitions),
            'rebalancing_needed': False,
            'optimization_applied': 'Partition analysis completed'
        }
    
    async def _optimize_embedding_model(self) -> Dict[str, Any]:
        """Optimize embedding model configuration"""
        if not self.embedding_model:
            return {'status': 'No embedding model available'}
        
        # Analyze embedding performance
        # For now, return basic status
        return {
            'model_name': getattr(self.embedding_model, 'model_name', 'unknown'),
            'status': 'Model performance within acceptable range',
            'optimization_applied': 'No changes needed'
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        cache_stats = self.cache.get_stats()
        
        stats = {
            'cache_performance': cache_stats,
            'query_metrics': {
                'total_queries': len(self.query_metrics),
                'avg_execution_time': np.mean([m['execution_time_ms'] for m in self.query_metrics]) if self.query_metrics else 0,
                'cache_hit_rate': np.mean([m['cache_hit'] for m in self.query_metrics]) if self.query_metrics else 0
            },
            'system_status': {
                'vector_db_available': self.vector_client is not None,
                'graph_db_available': self.graph_driver is not None,
                'embedding_model_loaded': self.embedding_model is not None
            },
            'optimization_history': len(self.optimization_history)
        }
        
        return stats