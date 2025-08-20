"""
Model Context Protocol (MCP) Server
Implements MCP server for providing tools and context to AI assistants
"""

import logging
import json
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import os
import uuid

# MCP Protocol Messages
from enum import Enum


class MCPMessageType(Enum):
    """MCP message types"""
    INITIALIZE = "initialize"
    LIST_TOOLS = "list_tools"
    CALL_TOOL = "call_tool"
    LIST_RESOURCES = "list_resources"
    READ_RESOURCE = "read_resource"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class MCPMessage:
    """Base MCP message structure"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


@dataclass
class MCPTool:
    """MCP tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    category: str = "general"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class MCPResource:
    """MCP resource definition"""
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"
    annotations: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.annotations is None:
            self.annotations = {}


@dataclass
class MCPToolResult:
    """Result of tool execution"""
    success: bool
    content: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


logger = logging.getLogger(__name__)


class MCPServer:
    """Model Context Protocol server implementation"""
    
    def __init__(self, name: str = "OpenWebUI-MCP-Server", version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: Dict[str, MCPTool] = {}
        self.tool_handlers: Dict[str, Callable] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.resource_handlers: Dict[str, Callable] = {}
        self.clients: Dict[str, Dict[str, Any]] = {}
        self.subscriptions: Dict[str, List[str]] = {}
        
        # Initialize built-in tools
        self._register_builtin_tools()
        self._register_builtin_resources()
    
    def _register_builtin_tools(self):
        """Register built-in tools"""
        
        # Knowledge search tool
        self.register_tool(
            MCPTool(
                name="knowledge_search",
                description="Search knowledge base using GraphRAG hybrid search",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "collection_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Knowledge collection IDs to search in"
                        },
                        "max_results": {"type": "integer", "default": 10, "description": "Maximum number of results"},
                        "use_graph_expansion": {"type": "boolean", "default": True, "description": "Use graph expansion"},
                        "entity_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Entity types to focus on"
                        }
                    },
                    "required": ["query"]
                },
                category="knowledge",
                tags=["search", "graphrag", "knowledge"]
            ),
            self._handle_knowledge_search
        )
        
        # Entity lookup tool
        self.register_tool(
            MCPTool(
                name="entity_lookup",
                description="Look up detailed information about an entity",
                input_schema={
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string", "description": "Entity ID to look up"},
                        "include_context": {"type": "boolean", "default": True, "description": "Include related entities and relationships"},
                        "context_depth": {"type": "integer", "default": 2, "description": "Depth of context to include"}
                    },
                    "required": ["entity_id"]
                },
                category="knowledge",
                tags=["entity", "lookup", "context"]
            ),
            self._handle_entity_lookup
        )
        
        # Document processing tool
        self.register_tool(
            MCPTool(
                name="process_document",
                description="Process a document through the GraphRAG pipeline",
                input_schema={
                    "type": "object",
                    "properties": {
                        "document_path": {"type": "string", "description": "Path to document to process"},
                        "collection_id": {"type": "string", "description": "Collection to add document to"},
                        "processing_config": {
                            "type": "object",
                            "properties": {
                                "chunk_size": {"type": "integer"},
                                "chunk_overlap": {"type": "integer"},
                                "extraction_model": {"type": "string"}
                            },
                            "description": "Processing configuration overrides"
                        }
                    },
                    "required": ["document_path", "collection_id"]
                },
                category="processing",
                tags=["document", "processing", "ingestion"]
            ),
            self._handle_process_document
        )
        
        # Assistant integration tool
        self.register_tool(
            MCPTool(
                name="get_assistant_knowledge",
                description="Get knowledge associated with an assistant",
                input_schema={
                    "type": "object",
                    "properties": {
                        "assistant_id": {"type": "string", "description": "Assistant ID"},
                        "query": {"type": "string", "description": "Optional query to filter knowledge"},
                        "limit": {"type": "integer", "default": 20, "description": "Maximum number of items"}
                    },
                    "required": ["assistant_id"]
                },
                category="assistant",
                tags=["assistant", "knowledge", "integration"]
            ),
            self._handle_get_assistant_knowledge
        )
        
        # File operations tool
        self.register_tool(
            MCPTool(
                name="file_operations",
                description="Perform file operations (read, write, list)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["read", "write", "list", "delete"],
                            "description": "File operation to perform"
                        },
                        "path": {"type": "string", "description": "File or directory path"},
                        "content": {"type": "string", "description": "Content to write (for write operation)"},
                        "encoding": {"type": "string", "default": "utf-8", "description": "File encoding"}
                    },
                    "required": ["operation", "path"]
                },
                category="system",
                tags=["file", "system", "io"]
            ),
            self._handle_file_operations
        )
        
        # System information tool
        self.register_tool(
            MCPTool(
                name="system_info",
                description="Get system information and health status",
                input_schema={
                    "type": "object",
                    "properties": {
                        "component": {
                            "type": "string",
                            "enum": ["all", "knowledge", "models", "resources"],
                            "default": "all",
                            "description": "System component to get info about"
                        }
                    }
                },
                category="system",
                tags=["system", "health", "status"]
            ),
            self._handle_system_info
        )
    
    def _register_builtin_resources(self):
        """Register built-in resources"""
        
        # Configuration resource
        self.register_resource(
            MCPResource(
                uri="config://graphrag",
                name="GraphRAG Configuration",
                description="Current GraphRAG system configuration",
                mime_type="application/json"
            ),
            self._handle_config_resource
        )
        
        # Analytics resource
        self.register_resource(
            MCPResource(
                uri="analytics://summary",
                name="System Analytics",
                description="System usage and performance analytics",
                mime_type="application/json"
            ),
            self._handle_analytics_resource
        )
        
        # Logs resource
        self.register_resource(
            MCPResource(
                uri="logs://recent",
                name="Recent Logs",
                description="Recent system logs and activity",
                mime_type="text/plain"
            ),
            self._handle_logs_resource
        )
    
    def register_tool(self, tool: MCPTool, handler: Callable):
        """Register a new tool"""
        self.tools[tool.name] = tool
        self.tool_handlers[tool.name] = handler
        logger.info(f"Registered MCP tool: {tool.name}")
    
    def register_resource(self, resource: MCPResource, handler: Callable):
        """Register a new resource"""
        self.resources[resource.uri] = resource
        self.resource_handlers[resource.uri] = handler
        logger.info(f"Registered MCP resource: {resource.uri}")
    
    async def handle_message(self, message: Dict[str, Any], client_id: str = None) -> Dict[str, Any]:
        """Handle incoming MCP message"""
        try:
            msg = MCPMessage(**message)
            
            if msg.method == MCPMessageType.INITIALIZE.value:
                return await self._handle_initialize(msg, client_id)
            elif msg.method == MCPMessageType.LIST_TOOLS.value:
                return await self._handle_list_tools(msg, client_id)
            elif msg.method == MCPMessageType.CALL_TOOL.value:
                return await self._handle_call_tool(msg, client_id)
            elif msg.method == MCPMessageType.LIST_RESOURCES.value:
                return await self._handle_list_resources(msg, client_id)
            elif msg.method == MCPMessageType.READ_RESOURCE.value:
                return await self._handle_read_resource(msg, client_id)
            elif msg.method == MCPMessageType.SUBSCRIBE.value:
                return await self._handle_subscribe(msg, client_id)
            elif msg.method == MCPMessageType.UNSUBSCRIBE.value:
                return await self._handle_unsubscribe(msg, client_id)
            else:
                return self._create_error_response(msg.id, -32601, "Method not found", {"method": msg.method})
                
        except Exception as e:
            logger.error(f"Error handling MCP message: {e}")
            return self._create_error_response(message.get('id'), -32603, "Internal error", {"error": str(e)})
    
    async def _handle_initialize(self, msg: MCPMessage, client_id: str) -> Dict[str, Any]:
        """Handle initialize message"""
        params = msg.params or {}
        client_info = {
            'name': params.get('clientInfo', {}).get('name', 'Unknown'),
            'version': params.get('clientInfo', {}).get('version', '1.0.0'),
            'capabilities': params.get('capabilities', {}),
            'connected_at': int(time.time() * 1000)
        }
        
        if client_id:
            self.clients[client_id] = client_info
        
        return {
            'jsonrpc': '2.0',
            'id': msg.id,
            'result': {
                'protocolVersion': '1.0.0',
                'serverInfo': {
                    'name': self.name,
                    'version': self.version
                },
                'capabilities': {
                    'tools': True,
                    'resources': True,
                    'notifications': True,
                    'experimental': {
                        'streaming': False,
                        'batch': False
                    }
                }
            }
        }
    
    async def _handle_list_tools(self, msg: MCPMessage, client_id: str) -> Dict[str, Any]:
        """Handle list tools message"""
        tools_list = []
        for tool in self.tools.values():
            tools_list.append({
                'name': tool.name,
                'description': tool.description,
                'inputSchema': tool.input_schema,
                'category': tool.category,
                'tags': tool.tags
            })
        
        return {
            'jsonrpc': '2.0',
            'id': msg.id,
            'result': {
                'tools': tools_list
            }
        }
    
    async def _handle_call_tool(self, msg: MCPMessage, client_id: str) -> Dict[str, Any]:
        """Handle call tool message"""
        params = msg.params or {}
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        if not tool_name:
            return self._create_error_response(msg.id, -32602, "Missing tool name")
        
        if tool_name not in self.tools:
            return self._create_error_response(msg.id, -32601, f"Tool not found: {tool_name}")
        
        try:
            handler = self.tool_handlers[tool_name]
            result = await handler(arguments, client_id)
            
            return {
                'jsonrpc': '2.0',
                'id': msg.id,
                'result': {
                    'content': result.content,
                    'isError': not result.success,
                    'metadata': result.metadata
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return self._create_error_response(msg.id, -32603, f"Tool execution error: {str(e)}")
    
    async def _handle_list_resources(self, msg: MCPMessage, client_id: str) -> Dict[str, Any]:
        """Handle list resources message"""
        resources_list = []
        for resource in self.resources.values():
            resources_list.append({
                'uri': resource.uri,
                'name': resource.name,
                'description': resource.description,
                'mimeType': resource.mime_type,
                'annotations': resource.annotations
            })
        
        return {
            'jsonrpc': '2.0',
            'id': msg.id,
            'result': {
                'resources': resources_list
            }
        }
    
    async def _handle_read_resource(self, msg: MCPMessage, client_id: str) -> Dict[str, Any]:
        """Handle read resource message"""
        params = msg.params or {}
        uri = params.get('uri')
        
        if not uri:
            return self._create_error_response(msg.id, -32602, "Missing resource URI")
        
        if uri not in self.resources:
            return self._create_error_response(msg.id, -32601, f"Resource not found: {uri}")
        
        try:
            handler = self.resource_handlers[uri]
            content = await handler(params, client_id)
            
            return {
                'jsonrpc': '2.0',
                'id': msg.id,
                'result': {
                    'contents': [{
                        'uri': uri,
                        'mimeType': self.resources[uri].mime_type,
                        'text': content if isinstance(content, str) else json.dumps(content, indent=2)
                    }]
                }
            }
            
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            return self._create_error_response(msg.id, -32603, f"Resource read error: {str(e)}")
    
    async def _handle_subscribe(self, msg: MCPMessage, client_id: str) -> Dict[str, Any]:
        """Handle subscribe message"""
        params = msg.params or {}
        uri = params.get('uri')
        
        if not uri:
            return self._create_error_response(msg.id, -32602, "Missing subscription URI")
        
        if client_id:
            if uri not in self.subscriptions:
                self.subscriptions[uri] = []
            if client_id not in self.subscriptions[uri]:
                self.subscriptions[uri].append(client_id)
        
        return {
            'jsonrpc': '2.0',
            'id': msg.id,
            'result': {}
        }
    
    async def _handle_unsubscribe(self, msg: MCPMessage, client_id: str) -> Dict[str, Any]:
        """Handle unsubscribe message"""
        params = msg.params or {}
        uri = params.get('uri')
        
        if not uri:
            return self._create_error_response(msg.id, -32602, "Missing subscription URI")
        
        if client_id and uri in self.subscriptions:
            if client_id in self.subscriptions[uri]:
                self.subscriptions[uri].remove(client_id)
            if not self.subscriptions[uri]:
                del self.subscriptions[uri]
        
        return {
            'jsonrpc': '2.0',
            'id': msg.id,
            'result': {}
        }
    
    # Tool Handlers
    
    async def _handle_knowledge_search(self, args: Dict[str, Any], client_id: str) -> MCPToolResult:
        """Handle knowledge search tool"""
        try:
            from ..knowledge.graphrag_service import GraphRAGService
            
            service = GraphRAGService()
            
            query = args['query']
            collection_ids = args.get('collection_ids', [])
            max_results = args.get('max_results', 10)
            use_graph_expansion = args.get('use_graph_expansion', True)
            entity_types = args.get('entity_types', [])
            
            # Convert entity types from strings to enums
            from ..knowledge.models import EntityType
            entity_type_enums = []
            for et in entity_types:
                try:
                    entity_type_enums.append(EntityType(et))
                except ValueError:
                    continue
            
            results = await service.hybrid_search(
                query=query,
                collection_ids=collection_ids,
                user_id=client_id or "mcp_client",
                max_results=max_results,
                use_graph_expansion=use_graph_expansion,
                entity_types=entity_type_enums
            )
            
            # Format results for MCP
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'source_type': result.source_type,
                    'content': result.content,
                    'similarity_score': result.similarity_score,
                    'combined_score': result.combined_score,
                    'metadata': result.metadata
                })
            
            return MCPToolResult(
                success=True,
                content=formatted_results,
                metadata={
                    'query': query,
                    'results_count': len(results),
                    'search_config': {
                        'max_results': max_results,
                        'use_graph_expansion': use_graph_expansion,
                        'collection_ids': collection_ids
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error in knowledge search: {e}")
            return MCPToolResult(success=False, content=None, error=str(e))
    
    async def _handle_entity_lookup(self, args: Dict[str, Any], client_id: str) -> MCPToolResult:
        """Handle entity lookup tool"""
        try:
            from ..knowledge.graphrag_service import GraphRAGService
            
            service = GraphRAGService()
            
            entity_id = args['entity_id']
            include_context = args.get('include_context', True)
            context_depth = args.get('context_depth', 2)
            
            if include_context:
                context = await service.get_entity_context(entity_id, context_depth)
                return MCPToolResult(
                    success=True,
                    content=context,
                    metadata={'entity_id': entity_id, 'context_depth': context_depth}
                )
            else:
                entity = service.entity_repo.get_by_id(entity_id)
                if entity:
                    return MCPToolResult(
                        success=True,
                        content={
                            'id': entity.id,
                            'name': entity.name,
                            'type': entity.entity_type.value,
                            'description': entity.description,
                            'mention_count': entity.mention_count,
                            'pagerank_score': entity.pagerank_score
                        },
                        metadata={'entity_id': entity_id}
                    )
                else:
                    return MCPToolResult(
                        success=False,
                        content=None,
                        error=f"Entity not found: {entity_id}"
                    )
            
        except Exception as e:
            logger.error(f"Error in entity lookup: {e}")
            return MCPToolResult(success=False, content=None, error=str(e))
    
    async def _handle_process_document(self, args: Dict[str, Any], client_id: str) -> MCPToolResult:
        """Handle document processing tool"""
        try:
            from ..knowledge.graphrag_service import GraphRAGService
            
            service = GraphRAGService()
            
            document_path = args['document_path']
            collection_id = args['collection_id']
            processing_config = args.get('processing_config', {})
            
            # Check if file exists
            if not os.path.exists(document_path):
                return MCPToolResult(
                    success=False,
                    content=None,
                    error=f"Document not found: {document_path}"
                )
            
            # Add document to collection
            success, result = await service.add_document(
                collection_id=collection_id,
                file_path=document_path,
                file_name=os.path.basename(document_path),
                user_id=client_id or "mcp_client",
                custom_metadata={
                    'processed_via_mcp': True,
                    'mcp_client': client_id
                }
            )
            
            if success:
                return MCPToolResult(
                    success=True,
                    content={
                        'document_id': result.id,
                        'name': result.name,
                        'status': result.processing_status.value,
                        'message': 'Document added and processing started'
                    },
                    metadata={
                        'document_path': document_path,
                        'collection_id': collection_id,
                        'processing_config': processing_config
                    }
                )
            else:
                return MCPToolResult(
                    success=False,
                    content=None,
                    error=f"Failed to add document: {result}"
                )
            
        except Exception as e:
            logger.error(f"Error in document processing: {e}")
            return MCPToolResult(success=False, content=None, error=str(e))
    
    async def _handle_get_assistant_knowledge(self, args: Dict[str, Any], client_id: str) -> MCPToolResult:
        """Handle get assistant knowledge tool"""
        try:
            from ..database.assistant_repositories import AssistantRepository
            
            assistant_repo = AssistantRepository()
            assistant_id = args['assistant_id']
            query = args.get('query')
            limit = args.get('limit', 20)
            
            # Get assistant
            assistant = assistant_repo.get_by_id(assistant_id)
            if not assistant:
                return MCPToolResult(
                    success=False,
                    content=None,
                    error=f"Assistant not found: {assistant_id}"
                )
            
            # Get linked knowledge collections
            # This would need to be implemented in the assistant repository
            linked_collections = []  # Placeholder
            
            return MCPToolResult(
                success=True,
                content={
                    'assistant_id': assistant_id,
                    'assistant_name': assistant.name,
                    'linked_collections': linked_collections,
                    'query': query
                },
                metadata={'assistant_id': assistant_id, 'limit': limit}
            )
            
        except Exception as e:
            logger.error(f"Error getting assistant knowledge: {e}")
            return MCPToolResult(success=False, content=None, error=str(e))
    
    async def _handle_file_operations(self, args: Dict[str, Any], client_id: str) -> MCPToolResult:
        """Handle file operations tool"""
        try:
            operation = args['operation']
            path = args['path']
            content = args.get('content', '')
            encoding = args.get('encoding', 'utf-8')
            
            # Security check: restrict to certain directories
            allowed_paths = ['/tmp', '/var/tmp', './data', './uploads']
            if not any(os.path.abspath(path).startswith(os.path.abspath(allowed_path)) for allowed_path in allowed_paths):
                return MCPToolResult(
                    success=False,
                    content=None,
                    error=f"Access denied: path not in allowed directories"
                )
            
            if operation == 'read':
                if os.path.exists(path):
                    with open(path, 'r', encoding=encoding) as f:
                        file_content = f.read()
                    return MCPToolResult(
                        success=True,
                        content=file_content,
                        metadata={'path': path, 'operation': operation, 'size': len(file_content)}
                    )
                else:
                    return MCPToolResult(success=False, content=None, error=f"File not found: {path}")
            
            elif operation == 'write':
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding=encoding) as f:
                    f.write(content)
                return MCPToolResult(
                    success=True,
                    content=f"Written {len(content)} characters to {path}",
                    metadata={'path': path, 'operation': operation, 'size': len(content)}
                )
            
            elif operation == 'list':
                if os.path.exists(path):
                    items = []
                    for item in os.listdir(path):
                        item_path = os.path.join(path, item)
                        is_file = os.path.isfile(item_path)
                        size = os.path.getsize(item_path) if is_file else None
                        items.append({
                            'name': item,
                            'type': 'file' if is_file else 'directory',
                            'size': size,
                            'modified': os.path.getmtime(item_path)
                        })
                    return MCPToolResult(
                        success=True,
                        content=items,
                        metadata={'path': path, 'operation': operation, 'count': len(items)}
                    )
                else:
                    return MCPToolResult(success=False, content=None, error=f"Directory not found: {path}")
            
            elif operation == 'delete':
                if os.path.exists(path):
                    if os.path.isfile(path):
                        os.remove(path)
                        return MCPToolResult(
                            success=True,
                            content=f"File deleted: {path}",
                            metadata={'path': path, 'operation': operation}
                        )
                    else:
                        return MCPToolResult(success=False, content=None, error=f"Cannot delete directory: {path}")
                else:
                    return MCPToolResult(success=False, content=None, error=f"File not found: {path}")
            
            else:
                return MCPToolResult(success=False, content=None, error=f"Unknown operation: {operation}")
            
        except Exception as e:
            logger.error(f"Error in file operations: {e}")
            return MCPToolResult(success=False, content=None, error=str(e))
    
    async def _handle_system_info(self, args: Dict[str, Any], client_id: str) -> MCPToolResult:
        """Handle system info tool"""
        try:
            component = args.get('component', 'all')
            
            info = {
                'timestamp': int(time.time() * 1000),
                'server': {
                    'name': self.name,
                    'version': self.version,
                    'uptime': int(time.time() * 1000)  # Simplified uptime
                }
            }
            
            if component in ['all', 'knowledge']:
                from ..knowledge.graphrag_service import GraphRAGService
                service = GraphRAGService()
                
                info['knowledge'] = {
                    'config': {
                        'chunk_size': service.config.chunk_size,
                        'embedding_model': service.config.embedding_model,
                        'async_processing': service.config.async_processing
                    },
                    'processing_queue_size': service.processing_queue.qsize() if hasattr(service.processing_queue, 'qsize') else 0,
                    'active_jobs': len(service.active_jobs)
                }
            
            if component in ['all', 'models']:
                info['models'] = {
                    'available': True,  # Simplified
                    'status': 'active'
                }
            
            if component in ['all', 'resources']:
                info['resources'] = {
                    'tools_registered': len(self.tools),
                    'resources_registered': len(self.resources),
                    'active_clients': len(self.clients),
                    'subscriptions': len(self.subscriptions)
                }
            
            return MCPToolResult(
                success=True,
                content=info,
                metadata={'component': component, 'generated_at': info['timestamp']}
            )
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return MCPToolResult(success=False, content=None, error=str(e))
    
    # Resource Handlers
    
    async def _handle_config_resource(self, params: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle config resource"""
        from ..knowledge.graphrag_service import GraphRAGService
        
        service = GraphRAGService()
        config = service.config
        
        return {
            'graphrag_config': {
                'chunk_size': config.chunk_size,
                'chunk_overlap': config.chunk_overlap,
                'chunking_strategy': config.chunking_strategy,
                'embedding_model': config.embedding_model,
                'embedding_dimension': config.embedding_dimension,
                'entity_extraction_model': config.entity_extraction_model,
                'relationship_extraction_model': config.relationship_extraction_model,
                'vector_search_limit': config.vector_search_limit,
                'similarity_threshold': config.similarity_threshold,
                'async_processing': config.async_processing,
                'max_concurrent_jobs': config.max_concurrent_jobs
            },
            'mcp_server_config': {
                'name': self.name,
                'version': self.version,
                'tools_count': len(self.tools),
                'resources_count': len(self.resources)
            }
        }
    
    async def _handle_analytics_resource(self, params: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle analytics resource"""
        return {
            'server_analytics': {
                'clients_connected': len(self.clients),
                'tools_registered': len(self.tools),
                'resources_registered': len(self.resources),
                'subscriptions_active': len(self.subscriptions),
                'uptime_ms': int(time.time() * 1000)  # Simplified
            },
            'knowledge_analytics': {
                'collections_count': 0,  # Would query from database
                'documents_count': 0,
                'entities_count': 0,
                'relationships_count': 0
            }
        }
    
    async def _handle_logs_resource(self, params: Dict[str, Any], client_id: str) -> str:
        """Handle logs resource"""
        # Return simplified log output
        log_entries = [
            f"[{datetime.now().isoformat()}] INFO - MCP Server started",
            f"[{datetime.now().isoformat()}] INFO - {len(self.tools)} tools registered",
            f"[{datetime.now().isoformat()}] INFO - {len(self.resources)} resources registered",
            f"[{datetime.now().isoformat()}] INFO - {len(self.clients)} clients connected"
        ]
        
        return "\n".join(log_entries)
    
    # Utility Methods
    
    def _create_error_response(self, message_id: str, code: int, message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create an error response"""
        error = {
            'code': code,
            'message': message
        }
        if data:
            error['data'] = data
        
        return {
            'jsonrpc': '2.0',
            'id': message_id,
            'error': error
        }
    
    async def send_notification(self, uri: str, data: Dict[str, Any]):
        """Send notification to subscribed clients"""
        if uri in self.subscriptions:
            notification = {
                'jsonrpc': '2.0',
                'method': MCPMessageType.NOTIFICATION.value,
                'params': {
                    'uri': uri,
                    'data': data,
                    'timestamp': int(time.time() * 1000)
                }
            }
            
            # In a real implementation, this would send to each client
            for client_id in self.subscriptions[uri]:
                logger.info(f"Would send notification to client {client_id}: {notification}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        return {
            'name': self.name,
            'version': self.version,
            'tools': len(self.tools),
            'resources': len(self.resources),
            'clients': len(self.clients),
            'subscriptions': len(self.subscriptions),
            'uptime': int(time.time() * 1000)  # Simplified
        }


# Global MCP server instance
mcp_server = MCPServer()


def get_mcp_server() -> MCPServer:
    """Get the global MCP server instance"""
    return mcp_server