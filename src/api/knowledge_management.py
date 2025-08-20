"""
Knowledge Management API
RESTful API endpoints for GraphRAG knowledge management including document ingestion,
entity/relationship extraction, and hybrid search capabilities
"""

import logging
import json
import os
import hashlib
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..knowledge.graphrag_service import GraphRAGService, GraphRAGConfig
from ..knowledge.models import (
    KnowledgeCollection, KnowledgeSource, DocumentType, ProcessingStatus,
    EntityType, RelationshipType
)
from ..database.connection import get_db_connection

logger = logging.getLogger(__name__)

# Initialize GraphRAG service
graphrag_service = GraphRAGService()

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=4)


class KnowledgeManagementAPI:
    """REST API for knowledge management operations"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize the Flask app with knowledge management routes"""
        self.app = app
        self._register_routes()
    
    def _register_routes(self):
        """Register all API routes"""
        
        # Collection management
        self.app.add_url_rule('/api/v1/knowledge/collections', 
                             'create_collection', self.create_collection, methods=['POST'])
        self.app.add_url_rule('/api/v1/knowledge/collections', 
                             'list_collections', self.list_collections, methods=['GET'])
        self.app.add_url_rule('/api/v1/knowledge/collections/<collection_id>', 
                             'get_collection', self.get_collection, methods=['GET'])
        self.app.add_url_rule('/api/v1/knowledge/collections/<collection_id>', 
                             'update_collection', self.update_collection, methods=['PUT'])
        self.app.add_url_rule('/api/v1/knowledge/collections/<collection_id>', 
                             'delete_collection', self.delete_collection, methods=['DELETE'])
        
        # Document management
        self.app.add_url_rule('/api/v1/knowledge/collections/<collection_id>/documents', 
                             'upload_document', self.upload_document, methods=['POST'])
        self.app.add_url_rule('/api/v1/knowledge/documents', 
                             'list_documents', self.list_documents, methods=['GET'])
        self.app.add_url_rule('/api/v1/knowledge/documents/<int:document_id>', 
                             'get_document', self.get_document, methods=['GET'])
        self.app.add_url_rule('/api/v1/knowledge/documents/<int:document_id>', 
                             'delete_document', self.delete_document, methods=['DELETE'])
        self.app.add_url_rule('/api/v1/knowledge/documents/<int:document_id>/process', 
                             'process_document', self.process_document, methods=['POST'])
        
        # Search and retrieval
        self.app.add_url_rule('/api/v1/knowledge/search', 
                             'hybrid_search', self.hybrid_search, methods=['POST'])
        self.app.add_url_rule('/api/v1/knowledge/entities/search', 
                             'entity_search', self.entity_search, methods=['GET'])
        self.app.add_url_rule('/api/v1/knowledge/entities/<entity_id>', 
                             'get_entity', self.get_entity, methods=['GET'])
        self.app.add_url_rule('/api/v1/knowledge/entities/<entity_id>/context', 
                             'get_entity_context', self.get_entity_context, methods=['GET'])
        self.app.add_url_rule('/api/v1/knowledge/entities/<source_entity_id>/path/<target_entity_id>', 
                             'find_entity_path', self.find_entity_path, methods=['GET'])
        
        # Analytics and insights
        self.app.add_url_rule('/api/v1/knowledge/collections/<collection_id>/insights', 
                             'get_collection_insights', self.get_collection_insights, methods=['GET'])
        self.app.add_url_rule('/api/v1/knowledge/analytics/summary', 
                             'get_analytics_summary', self.get_analytics_summary, methods=['GET'])
        
        # Configuration
        self.app.add_url_rule('/api/v1/knowledge/config', 
                             'get_config', self.get_config, methods=['GET'])
        self.app.add_url_rule('/api/v1/knowledge/config', 
                             'update_config', self.update_config, methods=['PUT'])
    
    # Collection Management Endpoints
    
    def create_collection(self):
        """Create a new knowledge collection"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body is required'}), 400
            
            # Validate required fields
            required_fields = ['name', 'user_id']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # Create collection
            success, result = asyncio.run(graphrag_service.create_collection(
                name=data['name'],
                description=data.get('description', ''),
                user_id=data['user_id'],
                custom_config=data.get('config', {})
            ))
            
            if success:
                return jsonify({
                    'success': True,
                    'collection': {
                        'id': result.id,
                        'name': result.name,
                        'description': result.description,
                        'user_id': result.user_id,
                        'is_public': result.is_public,
                        'created_at': result.created_at,
                        'config': {
                            'chunking_strategy': result.chunking_strategy,
                            'embedding_model': result.embedding_model,
                            'chunk_size': result.chunk_size,
                            'chunk_overlap': result.chunk_overlap
                        }
                    }
                }), 201
            else:
                return jsonify({'success': False, 'error': result}), 500
                
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def list_collections(self):
        """List user's knowledge collections"""
        try:
            user_id = request.args.get('user_id')
            if not user_id:
                return jsonify({'error': 'user_id parameter is required'}), 400
            
            # Get collections from database
            collections = graphrag_service.collection_repo.get_by_user(user_id)
            
            collection_list = []
            for collection in collections:
                collection_list.append({
                    'id': collection.id,
                    'name': collection.name,
                    'description': collection.description,
                    'is_public': collection.is_public,
                    'source_count': collection.source_count,
                    'total_entities': collection.total_entities,
                    'total_relationships': collection.total_relationships,
                    'total_chunks': collection.total_chunks,
                    'processing_status': collection.processing_status.value,
                    'last_updated': collection.last_updated,
                    'created_at': collection.created_at
                })
            
            return jsonify({
                'success': True,
                'collections': collection_list,
                'total': len(collection_list)
            })
            
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def get_collection(self, collection_id: str):
        """Get detailed information about a collection"""
        try:
            collection = graphrag_service.collection_repo.get_by_id(collection_id)
            if not collection:
                return jsonify({'error': 'Collection not found'}), 404
            
            return jsonify({
                'success': True,
                'collection': {
                    'id': collection.id,
                    'name': collection.name,
                    'description': collection.description,
                    'user_id': collection.user_id,
                    'is_public': collection.is_public,
                    'source_count': collection.source_count,
                    'total_entities': collection.total_entities,
                    'total_relationships': collection.total_relationships,
                    'total_chunks': collection.total_chunks,
                    'processing_status': collection.processing_status.value,
                    'last_updated': collection.last_updated,
                    'config': {
                        'chunking_strategy': collection.chunking_strategy,
                        'embedding_model': collection.embedding_model,
                        'chunk_size': collection.chunk_size,
                        'chunk_overlap': collection.chunk_overlap
                    },
                    'tags': collection.tags,
                    'custom_settings': collection.custom_settings,
                    'created_at': collection.created_at,
                    'updated_at': collection.updated_at
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting collection: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def update_collection(self, collection_id: str):
        """Update collection metadata"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body is required'}), 400
            
            collection = graphrag_service.collection_repo.get_by_id(collection_id)
            if not collection:
                return jsonify({'error': 'Collection not found'}), 404
            
            # Update fields
            if 'name' in data:
                collection.name = data['name']
            if 'description' in data:
                collection.description = data['description']
            if 'is_public' in data:
                collection.is_public = data['is_public']
            if 'tags' in data:
                collection.tags = data['tags']
            if 'custom_settings' in data:
                collection.custom_settings.update(data['custom_settings'])
            
            collection.updated_at = int(datetime.now().timestamp() * 1000)
            
            success = graphrag_service.collection_repo.update(collection)
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Collection updated successfully'
                })
            else:
                return jsonify({'error': 'Failed to update collection'}), 500
                
        except Exception as e:
            logger.error(f"Error updating collection: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def delete_collection(self, collection_id: str):
        """Delete a collection and all its data"""
        try:
            collection = graphrag_service.collection_repo.get_by_id(collection_id)
            if not collection:
                return jsonify({'error': 'Collection not found'}), 404
            
            # TODO: Add cascade deletion of related data
            success = graphrag_service.collection_repo.delete(collection_id)
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Collection deleted successfully'
                })
            else:
                return jsonify({'error': 'Failed to delete collection'}), 500
                
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    # Document Management Endpoints
    
    def upload_document(self, collection_id: str):
        """Upload and add a document to a collection"""
        try:
            # Check if collection exists
            collection = graphrag_service.collection_repo.get_by_id(collection_id)
            if not collection:
                return jsonify({'error': 'Collection not found'}), 404
            
            # Check if file was uploaded
            if 'file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            user_id = request.form.get('user_id')
            if not user_id:
                return jsonify({'error': 'user_id is required'}), 400
            
            # Validate user has access to collection
            if collection.user_id != user_id:
                return jsonify({'error': 'Access denied'}), 403
            
            # Secure filename and save file
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', '/tmp'), collection_id)
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            # Get file metadata
            file_size = os.path.getsize(file_path)
            
            # Calculate content hash
            content_hash = self._calculate_file_hash(file_path)
            
            # Detect document type
            document_type = self._detect_document_type(filename)
            
            # Add document to collection
            success, result = asyncio.run(graphrag_service.add_document(
                collection_id=collection_id,
                file_path=file_path,
                file_name=filename,
                user_id=user_id,
                document_type=document_type,
                custom_metadata={
                    'file_size': file_size,
                    'content_hash': content_hash,
                    'upload_timestamp': int(datetime.now().timestamp() * 1000)
                }
            ))
            
            if success:
                return jsonify({
                    'success': True,
                    'document': {
                        'id': result.id,
                        'name': result.name,
                        'source_type': result.source_type.value,
                        'file_size': file_size,
                        'content_hash': content_hash,
                        'processing_status': result.processing_status.value,
                        'created_at': result.created_at
                    }
                }), 201
            else:
                # Clean up uploaded file on failure
                try:
                    os.remove(file_path)
                except OSError:
                    pass
                return jsonify({'success': False, 'error': result}), 500
                
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def list_documents(self):
        """List documents with optional filtering"""
        try:
            user_id = request.args.get('user_id')
            collection_id = request.args.get('collection_id')
            status = request.args.get('status')
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            
            if not user_id:
                return jsonify({'error': 'user_id parameter is required'}), 400
            
            # Get documents
            if collection_id:
                documents = graphrag_service.source_repo.get_by_collection(collection_id)
                # Filter by user
                documents = [doc for doc in documents if doc.user_id == user_id]
            else:
                documents = graphrag_service.source_repo.get_by_user(user_id)
            
            # Filter by status if specified
            if status:
                try:
                    status_enum = ProcessingStatus(status)
                    documents = [doc for doc in documents if doc.processing_status == status_enum]
                except ValueError:
                    return jsonify({'error': f'Invalid status: {status}'}), 400
            
            # Apply pagination
            total = len(documents)
            documents = documents[offset:offset + limit]
            
            document_list = []
            for doc in documents:
                document_list.append({
                    'id': doc.id,
                    'name': doc.name,
                    'source_type': doc.source_type.value,
                    'file_size': doc.file_size,
                    'processing_status': doc.processing_status.value,
                    'entities_extracted': doc.entities_extracted,
                    'relationships_extracted': doc.relationships_extracted,
                    'chunks_created': doc.chunks_created,
                    'collection_id': doc.collection_id,
                    'last_processed_at': doc.last_processed_at,
                    'processing_error': doc.processing_error,
                    'created_at': doc.created_at
                })
            
            return jsonify({
                'success': True,
                'documents': document_list,
                'total': total,
                'offset': offset,
                'limit': limit
            })
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def get_document(self, document_id: int):
        """Get detailed information about a document"""
        try:
            document = graphrag_service.source_repo.get_by_id(document_id)
            if not document:
                return jsonify({'error': 'Document not found'}), 404
            
            return jsonify({
                'success': True,
                'document': {
                    'id': document.id,
                    'name': document.name,
                    'source_type': document.source_type.value,
                    'source_path': document.source_path,
                    'original_filename': document.original_filename,
                    'file_size': document.file_size,
                    'content_hash': document.content_hash,
                    'processing_status': document.processing_status.value,
                    'last_processed_at': document.last_processed_at,
                    'processing_error': document.processing_error,
                    'processing_metadata': document.processing_metadata,
                    'content_preview': document.content_preview,
                    'language': document.language,
                    'content_length': document.content_length,
                    'entities_extracted': document.entities_extracted,
                    'relationships_extracted': document.relationships_extracted,
                    'chunks_created': document.chunks_created,
                    'embeddings_generated': document.embeddings_generated,
                    'collection_id': document.collection_id,
                    'tags': document.tags,
                    'custom_metadata': document.custom_metadata,
                    'created_at': document.created_at,
                    'updated_at': document.updated_at
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def delete_document(self, document_id: int):
        """Delete a document and all its processed data"""
        try:
            document = graphrag_service.source_repo.get_by_id(document_id)
            if not document:
                return jsonify({'error': 'Document not found'}), 404
            
            # TODO: Add cascade deletion of chunks, entities, relationships
            success = graphrag_service.source_repo.delete(document_id)
            if success:
                # Clean up file
                try:
                    if os.path.exists(document.source_path):
                        os.remove(document.source_path)
                except OSError:
                    logger.warning(f"Could not delete file: {document.source_path}")
                
                return jsonify({
                    'success': True,
                    'message': 'Document deleted successfully'
                })
            else:
                return jsonify({'error': 'Failed to delete document'}), 500
                
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def process_document(self, document_id: int):
        """Trigger processing of a document"""
        try:
            document = graphrag_service.source_repo.get_by_id(document_id)
            if not document:
                return jsonify({'error': 'Document not found'}), 404
            
            # Start processing in background
            future = executor.submit(self._process_document_async, document)
            
            return jsonify({
                'success': True,
                'message': 'Document processing started',
                'document_id': document_id,
                'status': 'processing'
            })
            
        except Exception as e:
            logger.error(f"Error starting document processing: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def _process_document_async(self, document):
        """Process document asynchronously"""
        try:
            return asyncio.run(graphrag_service.process_document_pipeline(document))
        except Exception as e:
            logger.error(f"Error in async document processing: {e}")
            return False
    
    # Search and Retrieval Endpoints
    
    def hybrid_search(self):
        """Perform hybrid search using vector similarity and graph traversal"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body is required'}), 400
            
            # Validate required fields
            if 'query' not in data:
                return jsonify({'error': 'Query is required'}), 400
            
            user_id = data.get('user_id', '')
            if not user_id:
                return jsonify({'error': 'user_id is required'}), 400
            
            # Extract search parameters
            query = data['query']
            collection_ids = data.get('collection_ids', [])
            assistant_id = data.get('assistant_id')
            max_results = data.get('max_results', 10)
            similarity_threshold = data.get('similarity_threshold')
            use_graph_expansion = data.get('use_graph_expansion', True)
            entity_types = data.get('entity_types', [])
            
            # Convert entity type strings to enums
            entity_type_enums = []
            for et in entity_types:
                try:
                    entity_type_enums.append(EntityType(et))
                except ValueError:
                    logger.warning(f"Invalid entity type: {et}")
            
            # Perform hybrid search
            results = asyncio.run(graphrag_service.hybrid_search(
                query=query,
                collection_ids=collection_ids,
                user_id=user_id,
                assistant_id=assistant_id,
                max_results=max_results,
                similarity_threshold=similarity_threshold,
                use_graph_expansion=use_graph_expansion,
                entity_types=entity_type_enums
            ))
            
            # Format results
            result_list = []
            for result in results:
                result_list.append({
                    'id': result.id,
                    'source_type': result.source_type,
                    'source_id': result.source_id,
                    'content': result.content,
                    'similarity_score': result.similarity_score,
                    'relevance_score': result.relevance_score,
                    'graph_score': result.graph_score,
                    'combined_score': result.combined_score,
                    'source_document_id': result.source_document_id,
                    'source_document_name': result.source_document_name,
                    'chunk_position': result.chunk_position,
                    'related_entities': result.related_entities,
                    'related_relationships': result.related_relationships,
                    'metadata': result.metadata
                })
            
            return jsonify({
                'success': True,
                'query': query,
                'results': result_list,
                'total_results': len(result_list),
                'search_config': {
                    'max_results': max_results,
                    'similarity_threshold': similarity_threshold,
                    'use_graph_expansion': use_graph_expansion,
                    'collection_ids': collection_ids
                }
            })
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def entity_search(self):
        """Search for entities by name or type"""
        try:
            query = request.args.get('query', '')
            entity_types = request.args.getlist('entity_type')
            limit = int(request.args.get('limit', 20))
            
            # Convert entity type strings to enums
            entity_type_enums = []
            for et in entity_types:
                try:
                    entity_type_enums.append(EntityType(et))
                except ValueError:
                    logger.warning(f"Invalid entity type: {et}")
            
            # Search entities
            entities = graphrag_service.entity_repo.search_by_name(query, entity_type_enums, limit)
            
            entity_list = []
            for entity in entities:
                entity_list.append({
                    'id': entity.id,
                    'name': entity.name,
                    'entity_type': entity.entity_type.value,
                    'canonical_name': entity.canonical_name,
                    'description': entity.description,
                    'aliases': entity.aliases,
                    'mention_count': entity.mention_count,
                    'degree_centrality': entity.degree_centrality,
                    'pagerank_score': entity.pagerank_score,
                    'extraction_confidence': entity.extraction_confidence
                })
            
            return jsonify({
                'success': True,
                'entities': entity_list,
                'total': len(entity_list),
                'query': query,
                'entity_types': entity_types
            })
            
        except Exception as e:
            logger.error(f"Error in entity search: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def get_entity(self, entity_id: str):
        """Get detailed information about an entity"""
        try:
            entity = graphrag_service.entity_repo.get_by_id(entity_id)
            if not entity:
                return jsonify({'error': 'Entity not found'}), 404
            
            return jsonify({
                'success': True,
                'entity': {
                    'id': entity.id,
                    'name': entity.name,
                    'entity_type': entity.entity_type.value,
                    'canonical_name': entity.canonical_name,
                    'description': entity.description,
                    'aliases': entity.aliases,
                    'properties': entity.properties,
                    'source_documents': entity.source_documents,
                    'mention_count': entity.mention_count,
                    'first_mentioned_at': entity.first_mentioned_at,
                    'last_mentioned_at': entity.last_mentioned_at,
                    'degree_centrality': entity.degree_centrality,
                    'betweenness_centrality': entity.betweenness_centrality,
                    'pagerank_score': entity.pagerank_score,
                    'extraction_confidence': entity.extraction_confidence,
                    'type_confidence': entity.type_confidence,
                    'created_at': entity.created_at,
                    'updated_at': entity.updated_at
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting entity: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def get_entity_context(self, entity_id: str):
        """Get comprehensive context for an entity including relationships"""
        try:
            depth = int(request.args.get('depth', 2))
            
            context = asyncio.run(graphrag_service.get_entity_context(entity_id, depth))
            if not context:
                return jsonify({'error': 'Entity not found or no context available'}), 404
            
            return jsonify({
                'success': True,
                'entity_context': context
            })
            
        except Exception as e:
            logger.error(f"Error getting entity context: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def find_entity_path(self, source_entity_id: str, target_entity_id: str):
        """Find connection paths between two entities"""
        try:
            max_depth = int(request.args.get('max_depth', 3))
            
            paths = asyncio.run(graphrag_service.find_entity_path(
                source_entity_id, target_entity_id, max_depth
            ))
            
            return jsonify({
                'success': True,
                'source_entity_id': source_entity_id,
                'target_entity_id': target_entity_id,
                'paths': paths,
                'max_depth': max_depth
            })
            
        except Exception as e:
            logger.error(f"Error finding entity path: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    # Analytics and Insights Endpoints
    
    def get_collection_insights(self, collection_id: str):
        """Get insights and analytics for a knowledge collection"""
        try:
            insights = asyncio.run(graphrag_service.get_collection_insights(collection_id))
            if not insights:
                return jsonify({'error': 'Collection not found'}), 404
            
            return jsonify({
                'success': True,
                'insights': insights
            })
            
        except Exception as e:
            logger.error(f"Error getting collection insights: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def get_analytics_summary(self):
        """Get overall analytics summary"""
        try:
            user_id = request.args.get('user_id')
            if not user_id:
                return jsonify({'error': 'user_id parameter is required'}), 400
            
            # Get summary statistics
            collections = graphrag_service.collection_repo.get_by_user(user_id)
            documents = graphrag_service.source_repo.get_by_user(user_id)
            
            # Calculate statistics
            total_collections = len(collections)
            total_documents = len(documents)
            completed_documents = len([d for d in documents if d.processing_status == ProcessingStatus.COMPLETED])
            failed_documents = len([d for d in documents if d.processing_status == ProcessingStatus.FAILED])
            
            total_entities = sum(c.total_entities for c in collections)
            total_relationships = sum(c.total_relationships for c in collections)
            total_chunks = sum(c.total_chunks for c in collections)
            
            return jsonify({
                'success': True,
                'summary': {
                    'total_collections': total_collections,
                    'total_documents': total_documents,
                    'completed_documents': completed_documents,
                    'failed_documents': failed_documents,
                    'processing_rate': completed_documents / total_documents if total_documents > 0 else 0,
                    'total_entities': total_entities,
                    'total_relationships': total_relationships,
                    'total_chunks': total_chunks,
                    'avg_entities_per_document': total_entities / completed_documents if completed_documents > 0 else 0,
                    'avg_relationships_per_document': total_relationships / completed_documents if completed_documents > 0 else 0
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    # Configuration Endpoints
    
    def get_config(self):
        """Get current GraphRAG configuration"""
        try:
            config = graphrag_service.config
            
            return jsonify({
                'success': True,
                'config': {
                    'chunk_size': config.chunk_size,
                    'chunk_overlap': config.chunk_overlap,
                    'chunking_strategy': config.chunking_strategy,
                    'embedding_model': config.embedding_model,
                    'embedding_dimension': config.embedding_dimension,
                    'batch_size': config.batch_size,
                    'entity_extraction_model': config.entity_extraction_model,
                    'entity_confidence_threshold': config.entity_confidence_threshold,
                    'max_entities_per_chunk': config.max_entities_per_chunk,
                    'relationship_extraction_model': config.relationship_extraction_model,
                    'relationship_confidence_threshold': config.relationship_confidence_threshold,
                    'max_relationships_per_chunk': config.max_relationships_per_chunk,
                    'vector_search_limit': config.vector_search_limit,
                    'graph_expansion_depth': config.graph_expansion_depth,
                    'similarity_threshold': config.similarity_threshold,
                    'graph_weight': config.graph_weight,
                    'async_processing': config.async_processing,
                    'max_concurrent_jobs': config.max_concurrent_jobs,
                    'enable_caching': config.enable_caching,
                    'cache_ttl_hours': config.cache_ttl_hours
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def update_config(self):
        """Update GraphRAG configuration"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body is required'}), 400
            
            # Create new config with updated values
            current_config = graphrag_service.config
            new_config = GraphRAGConfig(
                chunk_size=data.get('chunk_size', current_config.chunk_size),
                chunk_overlap=data.get('chunk_overlap', current_config.chunk_overlap),
                chunking_strategy=data.get('chunking_strategy', current_config.chunking_strategy),
                embedding_model=data.get('embedding_model', current_config.embedding_model),
                embedding_dimension=data.get('embedding_dimension', current_config.embedding_dimension),
                batch_size=data.get('batch_size', current_config.batch_size),
                entity_extraction_model=data.get('entity_extraction_model', current_config.entity_extraction_model),
                entity_confidence_threshold=data.get('entity_confidence_threshold', current_config.entity_confidence_threshold),
                max_entities_per_chunk=data.get('max_entities_per_chunk', current_config.max_entities_per_chunk),
                relationship_extraction_model=data.get('relationship_extraction_model', current_config.relationship_extraction_model),
                relationship_confidence_threshold=data.get('relationship_confidence_threshold', current_config.relationship_confidence_threshold),
                max_relationships_per_chunk=data.get('max_relationships_per_chunk', current_config.max_relationships_per_chunk),
                vector_search_limit=data.get('vector_search_limit', current_config.vector_search_limit),
                graph_expansion_depth=data.get('graph_expansion_depth', current_config.graph_expansion_depth),
                similarity_threshold=data.get('similarity_threshold', current_config.similarity_threshold),
                graph_weight=data.get('graph_weight', current_config.graph_weight),
                async_processing=data.get('async_processing', current_config.async_processing),
                max_concurrent_jobs=data.get('max_concurrent_jobs', current_config.max_concurrent_jobs),
                enable_caching=data.get('enable_caching', current_config.enable_caching),
                cache_ttl_hours=data.get('cache_ttl_hours', current_config.cache_ttl_hours)
            )
            
            # Update service config
            graphrag_service.config = new_config
            
            return jsonify({
                'success': True,
                'message': 'Configuration updated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    # Helper Methods
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _detect_document_type(self, filename: str) -> DocumentType:
        """Detect document type from filename"""
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


# Global API instance
knowledge_api = KnowledgeManagementAPI()


def init_knowledge_api(app: Flask):
    """Initialize knowledge management API with Flask app"""
    knowledge_api.init_app(app)
    return knowledge_api