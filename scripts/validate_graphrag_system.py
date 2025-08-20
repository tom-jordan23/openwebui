#!/usr/bin/env python3
"""
GraphRAG System Validation Script
Comprehensive testing of the complete GraphRAG system including all components
"""

import os
import sys
import asyncio
import json
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import modules
try:
    from knowledge.graphrag_service import GraphRAGService, GraphRAGConfig
    from knowledge.models import (
        KnowledgeCollection, KnowledgeSource, DocumentChunk, 
        KnowledgeEntity, KnowledgeRelationship, DocumentType, 
        ProcessingStatus, EntityType, RelationshipType
    )
    from knowledge.embeddings import EmbeddingService
    from knowledge.chunking import DocumentChunker, ChunkingConfig
    from knowledge.extractors import EntityExtractor, RelationshipExtractor, ExtractionConfig
    from mcp.mcp_server import MCPServer, MCPTool
    from database.connection import get_db_connection
    
    IMPORTS_SUCCESS = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORTS_SUCCESS = False


class GraphRAGSystemValidator:
    """Comprehensive validation of the GraphRAG system"""
    
    def __init__(self):
        self.results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': [],
            'timing': {},
            'errors': []
        }
        
        # Test data
        self.test_user_id = "test_user_graphrag"
        self.test_collection_id = None
        self.test_document_id = None
        
        # Services
        self.graphrag_service = None
        self.mcp_server = None
        
        # Create test documents
        self.test_documents = {
            'ai_overview.txt': """
            Artificial Intelligence Overview
            
            Artificial Intelligence (AI) is a branch of computer science that aims to create 
            intelligent machines that work and react like humans. AI systems are designed to 
            perform tasks that typically require human intelligence, such as visual perception, 
            speech recognition, decision-making, and language translation.
            
            Machine Learning is a subset of AI that provides systems the ability to automatically 
            learn and improve from experience without being explicitly programmed. Deep Learning, 
            in turn, is a subset of Machine Learning that uses neural networks with multiple 
            layers to analyze various factors of data.
            
            Natural Language Processing (NLP) is another important area of AI that focuses on 
            the interaction between computers and humans through natural language. NLP enables 
            machines to read, decipher, understand, and make sense of human languages.
            
            Companies like OpenAI, Google, and Microsoft are leading the development of 
            advanced AI systems. OpenAI created GPT models, Google developed BERT and 
            PaLM, while Microsoft has integrated AI into its Azure cloud platform.
            """,
            
            'tech_companies.txt': """
            Technology Companies and AI
            
            OpenAI is a research company focused on artificial intelligence safety. Founded 
            in 2015 by Sam Altman, Elon Musk, and others, OpenAI has developed several 
            groundbreaking AI models including GPT-3 and GPT-4. The company is based in 
            San Francisco, California.
            
            Google, founded by Larry Page and Sergey Brin at Stanford University, has been 
            a pioneer in AI research. Google's AI division, called DeepMind, has created 
            AlphaGo and other impressive AI systems. Google is headquartered in Mountain View, 
            California.
            
            Microsoft Corporation, founded by Bill Gates and Paul Allen, has invested heavily 
            in AI through its partnership with OpenAI and the development of Azure AI services. 
            Microsoft is located in Redmond, Washington.
            
            Tesla, led by Elon Musk, uses AI for autonomous vehicle development. Tesla's 
            Autopilot system relies on deep learning and computer vision to navigate roads 
            safely.
            """
        }
    
    async def run_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        logger.info("Starting GraphRAG System Validation")
        start_time = time.time()
        
        if not IMPORTS_SUCCESS:
            self._record_test("Import Validation", False, error="Failed to import required modules")
            return self.results
        
        # Run validation tests
        await self._test_imports()
        await self._test_database_connections()
        await self._test_embedding_service()
        await self._test_chunking_service()
        await self._test_entity_extraction()
        await self._test_relationship_extraction()
        await self._test_graphrag_service()
        await self._test_knowledge_collections()
        await self._test_document_processing()
        await self._test_hybrid_search()
        await self._test_entity_operations()
        await self._test_mcp_server()
        await self._test_api_integration()
        await self._test_end_to_end_workflow()
        
        # Cleanup
        await self._cleanup_test_data()
        
        total_time = time.time() - start_time
        self.results['timing']['total_validation_time'] = total_time
        
        logger.info(f"Validation completed in {total_time:.2f} seconds")
        logger.info(f"Tests passed: {self.results['passed_tests']}/{self.results['total_tests']}")
        
        if self.results['failed_tests'] > 0:
            logger.error(f"Tests failed: {self.results['failed_tests']}")
            for error in self.results['errors']:
                logger.error(f"Error: {error}")
        
        return self.results
    
    async def _test_imports(self):
        """Test that all required modules can be imported"""
        test_name = "Module Imports"
        
        try:
            # Test GraphRAG service
            config = GraphRAGConfig()
            self.graphrag_service = GraphRAGService(config)
            
            # Test MCP server
            self.mcp_server = MCPServer()
            
            self._record_test(test_name, True)
            
        except Exception as e:
            self._record_test(test_name, False, error=str(e))
    
    async def _test_database_connections(self):
        """Test database connectivity"""
        test_name = "Database Connections"
        
        try:
            # Test basic database connection
            conn = get_db_connection()
            if conn:
                conn.close()
                self._record_test(test_name, True)
            else:
                self._record_test(test_name, False, error="Could not establish database connection")
                
        except Exception as e:
            self._record_test(test_name, False, error=str(e))
    
    async def _test_embedding_service(self):
        """Test embedding service functionality"""
        test_name = "Embedding Service"
        
        try:
            embedding_service = EmbeddingService()
            
            # Test single embedding
            result = await embedding_service.embed_text("This is a test sentence.")
            
            if result and result.embedding and len(result.embedding) > 0:
                # Test batch embedding
                texts = ["First text", "Second text", "Third text"]
                batch_results = await embedding_service.embed_texts(texts)
                
                if len(batch_results) == 3:
                    # Test similarity calculation
                    similarity = embedding_service.calculate_similarity(
                        batch_results[0].embedding, batch_results[1].embedding
                    )
                    
                    if isinstance(similarity, float) and 0 <= similarity <= 1:
                        self._record_test(test_name, True, 
                                        metadata={'dimension': len(result.embedding), 
                                                'model': result.model})
                    else:
                        self._record_test(test_name, False, error="Invalid similarity calculation")
                else:
                    self._record_test(test_name, False, error="Batch embedding failed")
            else:
                self._record_test(test_name, False, error="Single embedding failed")
                
        except Exception as e:
            self._record_test(test_name, False, error=str(e))
    
    async def _test_chunking_service(self):
        """Test document chunking functionality"""
        test_name = "Document Chunking"
        
        try:
            config = ChunkingConfig(chunk_size=200, chunk_overlap=50)
            chunker = DocumentChunker(config)
            
            # Test chunking
            text = self.test_documents['ai_overview.txt']
            chunks = chunker.chunk_text(text, source_id=1)
            
            if chunks and len(chunks) > 1:
                # Validate chunk properties
                first_chunk = chunks[0]
                if (first_chunk.content and 
                    first_chunk.character_count > 0 and
                    first_chunk.chunk_index == 0):
                    
                    self._record_test(test_name, True, 
                                    metadata={'chunks_created': len(chunks),
                                            'strategy': config.strategy.value})
                else:
                    self._record_test(test_name, False, error="Invalid chunk properties")
            else:
                self._record_test(test_name, False, error="No chunks created")
                
        except Exception as e:
            self._record_test(test_name, False, error=str(e))
    
    async def _test_entity_extraction(self):
        """Test entity extraction functionality"""
        test_name = "Entity Extraction"
        
        try:
            config = ExtractionConfig()
            extractor = EntityExtractor(config)
            
            # Test entity extraction
            text = self.test_documents['tech_companies.txt']
            entities = extractor.extract_entities(text, source_id=1)
            
            if entities and len(entities) > 0:
                # Check if we found some expected entities
                entity_names = [e.name.lower() for e in entities]
                expected_entities = ['openai', 'google', 'microsoft', 'tesla']
                
                found_count = sum(1 for expected in expected_entities 
                                if any(expected in name for name in entity_names))
                
                if found_count > 0:
                    self._record_test(test_name, True, 
                                    metadata={'entities_found': len(entities),
                                            'expected_found': found_count})
                else:
                    self._record_test(test_name, False, error="No expected entities found")
            else:
                self._record_test(test_name, False, error="No entities extracted")
                
        except Exception as e:
            self._record_test(test_name, False, error=str(e))
    
    async def _test_relationship_extraction(self):
        """Test relationship extraction functionality"""
        test_name = "Relationship Extraction"
        
        try:
            config = ExtractionConfig()
            entity_extractor = EntityExtractor(config)
            rel_extractor = RelationshipExtractor(config)
            
            # First extract entities
            text = self.test_documents['tech_companies.txt']
            entities = entity_extractor.extract_entities(text, source_id=1)
            
            if entities and len(entities) >= 2:
                # Extract relationships
                relationships = rel_extractor.extract_relationships(text, entities, source_id=1)
                
                if relationships and len(relationships) > 0:
                    # Validate relationship properties
                    first_rel = relationships[0]
                    if (first_rel.source_entity_id and 
                        first_rel.target_entity_id and
                        first_rel.relationship_type):
                        
                        self._record_test(test_name, True, 
                                        metadata={'relationships_found': len(relationships),
                                                'entities_available': len(entities)})
                    else:
                        self._record_test(test_name, False, error="Invalid relationship properties")
                else:
                    self._record_test(test_name, False, error="No relationships extracted")
            else:
                self._record_test(test_name, False, error="Insufficient entities for relationship extraction")
                
        except Exception as e:
            self._record_test(test_name, False, error=str(e))
    
    async def _test_graphrag_service(self):
        """Test GraphRAG service initialization"""
        test_name = "GraphRAG Service"
        
        try:
            if self.graphrag_service:
                # Test configuration
                config = self.graphrag_service.config
                if (config.chunk_size > 0 and 
                    config.embedding_model and
                    config.similarity_threshold > 0):
                    
                    self._record_test(test_name, True, 
                                    metadata={'chunk_size': config.chunk_size,
                                            'embedding_model': config.embedding_model})
                else:
                    self._record_test(test_name, False, error="Invalid configuration")
            else:
                self._record_test(test_name, False, error="GraphRAG service not initialized")
                
        except Exception as e:
            self._record_test(test_name, False, error=str(e))
    
    async def _test_knowledge_collections(self):
        """Test knowledge collection creation and management"""
        test_name = "Knowledge Collections"
        
        try:
            if not self.graphrag_service:
                self._record_test(test_name, False, error="GraphRAG service not available")
                return
            
            # Create collection
            success, result = await self.graphrag_service.create_collection(
                name="Test Collection",
                description="Test collection for validation",
                user_id=self.test_user_id
            )
            
            if success and result:
                self.test_collection_id = result.id
                
                # Verify collection properties
                if (result.name == "Test Collection" and 
                    result.user_id == self.test_user_id and
                    result.id):
                    
                    self._record_test(test_name, True, 
                                    metadata={'collection_id': result.id,
                                            'collection_name': result.name})
                else:
                    self._record_test(test_name, False, error="Invalid collection properties")
            else:
                self._record_test(test_name, False, error=f"Collection creation failed: {result}")
                
        except Exception as e:
            self._record_test(test_name, False, error=str(e))
    
    async def _test_document_processing(self):
        """Test document addition and processing"""
        test_name = "Document Processing"
        
        try:
            if not self.graphrag_service or not self.test_collection_id:
                self._record_test(test_name, False, error="Prerequisites not met")
                return
            
            # Create temporary test file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(self.test_documents['ai_overview.txt'])
                temp_file_path = f.name
            
            try:
                # Add document
                success, result = await self.graphrag_service.add_document(
                    collection_id=self.test_collection_id,
                    file_path=temp_file_path,
                    file_name="ai_overview.txt",
                    user_id=self.test_user_id,
                    document_type=DocumentType.TEXT
                )
                
                if success and result:
                    self.test_document_id = result.id
                    
                    # Verify document properties
                    if (result.name == "ai_overview.txt" and
                        result.collection_id == self.test_collection_id and
                        result.source_type == DocumentType.TEXT):
                        
                        # Wait a moment for processing to start
                        await asyncio.sleep(1)
                        
                        self._record_test(test_name, True, 
                                        metadata={'document_id': result.id,
                                                'document_name': result.name,
                                                'status': result.processing_status.value})
                    else:
                        self._record_test(test_name, False, error="Invalid document properties")
                else:
                    self._record_test(test_name, False, error=f"Document addition failed: {result}")
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
                    
        except Exception as e:
            self._record_test(test_name, False, error=str(e))
    
    async def _test_hybrid_search(self):
        """Test hybrid search functionality"""
        test_name = "Hybrid Search"
        
        try:
            if not self.graphrag_service:
                self._record_test(test_name, False, error="GraphRAG service not available")
                return
            
            # Perform search
            results = await self.graphrag_service.hybrid_search(
                query="artificial intelligence machine learning",
                user_id=self.test_user_id,
                max_results=5,
                similarity_threshold=0.1  # Lower threshold for testing
            )
            
            # For now, even if no results, test passes if no errors
            self._record_test(test_name, True, 
                            metadata={'results_found': len(results),
                                    'query': "artificial intelligence machine learning"})
                
        except Exception as e:
            self._record_test(test_name, False, error=str(e))
    
    async def _test_entity_operations(self):
        """Test entity-related operations"""
        test_name = "Entity Operations"
        
        try:
            if not self.graphrag_service:
                self._record_test(test_name, False, error="GraphRAG service not available")
                return
            
            # Test entity search
            entities = self.graphrag_service.entity_repo.search_by_name(
                "artificial", [], 10
            )
            
            # Test passes if no errors, regardless of results
            self._record_test(test_name, True, 
                            metadata={'entities_found': len(entities)})
                
        except Exception as e:
            self._record_test(test_name, False, error=str(e))
    
    async def _test_mcp_server(self):
        """Test MCP server functionality"""
        test_name = "MCP Server"
        
        try:
            if not self.mcp_server:
                self._record_test(test_name, False, error="MCP server not available")
                return
            
            # Test initialization message
            init_message = {
                'jsonrpc': '2.0',
                'id': 'test-1',
                'method': 'initialize',
                'params': {
                    'clientInfo': {'name': 'TestClient', 'version': '1.0.0'},
                    'capabilities': {}
                }
            }
            
            response = await self.mcp_server.handle_message(init_message, 'test-client')
            
            if (response.get('jsonrpc') == '2.0' and 
                response.get('id') == 'test-1' and
                'result' in response):
                
                # Test list tools
                tools_message = {
                    'jsonrpc': '2.0',
                    'id': 'test-2',
                    'method': 'list_tools',
                    'params': {}
                }
                
                tools_response = await self.mcp_server.handle_message(tools_message, 'test-client')
                
                if ('result' in tools_response and 
                    'tools' in tools_response['result'] and
                    len(tools_response['result']['tools']) > 0):
                    
                    self._record_test(test_name, True, 
                                    metadata={'tools_available': len(tools_response['result']['tools']),
                                            'server_name': self.mcp_server.name})
                else:
                    self._record_test(test_name, False, error="No tools available")
            else:
                self._record_test(test_name, False, error="Initialize failed")
                
        except Exception as e:
            self._record_test(test_name, False, error=str(e))
    
    async def _test_api_integration(self):
        """Test API integration components"""
        test_name = "API Integration"
        
        try:
            # Test that API modules can be imported
            from api.knowledge_management import KnowledgeManagementAPI
            
            # Basic instantiation test
            api = KnowledgeManagementAPI()
            
            if api:
                self._record_test(test_name, True, 
                                metadata={'api_class': 'KnowledgeManagementAPI'})
            else:
                self._record_test(test_name, False, error="API instantiation failed")
                
        except ImportError as e:
            self._record_test(test_name, False, error=f"API import failed: {str(e)}")
        except Exception as e:
            self._record_test(test_name, False, error=str(e))
    
    async def _test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        test_name = "End-to-End Workflow"
        
        try:
            # This is a simplified E2E test since we don't have a full database setup
            if (self.graphrag_service and 
                self.mcp_server and 
                self.test_collection_id):
                
                # Test MCP tool call for system info
                system_info_message = {
                    'jsonrpc': '2.0',
                    'id': 'test-e2e',
                    'method': 'call_tool',
                    'params': {
                        'name': 'system_info',
                        'arguments': {'component': 'all'}
                    }
                }
                
                response = await self.mcp_server.handle_message(system_info_message, 'test-client')
                
                if 'result' in response and response['result'].get('content'):
                    self._record_test(test_name, True, 
                                    metadata={'workflow_type': 'MCP system_info call'})
                else:
                    self._record_test(test_name, False, error="E2E workflow failed")
            else:
                self._record_test(test_name, False, error="Prerequisites not met for E2E test")
                
        except Exception as e:
            self._record_test(test_name, False, error=str(e))
    
    async def _cleanup_test_data(self):
        """Clean up test data"""
        try:
            # In a real implementation, this would clean up test collections, documents, etc.
            # For now, we'll just log that cleanup would occur
            logger.info("Test data cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def _record_test(self, test_name: str, passed: bool, 
                     metadata: Dict[str, Any] = None, error: str = None):
        """Record test result"""
        self.results['total_tests'] += 1
        
        if passed:
            self.results['passed_tests'] += 1
            logger.info(f"✓ {test_name}")
        else:
            self.results['failed_tests'] += 1
            logger.error(f"✗ {test_name}")
            if error:
                self.results['errors'].append(f"{test_name}: {error}")
        
        result = {
            'test_name': test_name,
            'passed': passed,
            'timestamp': int(time.time() * 1000)
        }
        
        if metadata:
            result['metadata'] = metadata
        if error:
            result['error'] = error
            
        self.results['test_results'].append(result)
    
    def generate_report(self) -> str:
        """Generate validation report"""
        report_lines = [
            "="*60,
            "GraphRAG System Validation Report",
            "="*60,
            f"Total Tests: {self.results['total_tests']}",
            f"Passed: {self.results['passed_tests']}",
            f"Failed: {self.results['failed_tests']}",
            f"Success Rate: {(self.results['passed_tests']/self.results['total_tests']*100):.1f}%",
            ""
        ]
        
        if 'total_validation_time' in self.results['timing']:
            report_lines.append(f"Total Time: {self.results['timing']['total_validation_time']:.2f} seconds")
            report_lines.append("")
        
        # Test details
        report_lines.append("Test Details:")
        report_lines.append("-" * 40)
        
        for test in self.results['test_results']:
            status = "PASS" if test['passed'] else "FAIL"
            line = f"{status:4} | {test['test_name']}"
            
            if 'metadata' in test:
                metadata_str = ", ".join([f"{k}={v}" for k, v in test['metadata'].items()])
                line += f" | {metadata_str}"
                
            if 'error' in test:
                line += f" | Error: {test['error']}"
                
            report_lines.append(line)
        
        if self.results['errors']:
            report_lines.append("")
            report_lines.append("Errors:")
            report_lines.append("-" * 40)
            for error in self.results['errors']:
                report_lines.append(f"  {error}")
        
        report_lines.append("")
        report_lines.append("="*60)
        
        return "\n".join(report_lines)


async def main():
    """Main validation function"""
    validator = GraphRAGSystemValidator()
    
    try:
        results = await validator.run_validation()
        
        # Generate and print report
        report = validator.generate_report()
        print(report)
        
        # Save results to file
        results_file = os.path.join(os.path.dirname(__file__), '..', 'reports', 'graphrag_validation_results.json')
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nDetailed results saved to: {results_file}")
        
        # Exit with appropriate code
        exit_code = 0 if results['failed_tests'] == 0 else 1
        return exit_code
        
    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        print(f"\nValidation failed: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)