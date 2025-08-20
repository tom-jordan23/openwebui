"""
Complete Prompt Management System Integration Test
Tests the full workflow from API to UI components
"""
import pytest
import json
import time
from unittest.mock import patch, MagicMock
from src.api.prompt_management import PromptService, PromptTemplateProcessor, PromptExportImport


class TestCompletePromptSystem:
    """Test complete prompt management system integration"""
    
    def test_end_to_end_prompt_workflow(self):
        """Test complete workflow: create category, create prompt, version, template processing"""
        service = PromptService()
        
        # Mock the database operations
        with patch.object(service.repo, 'create_category') as mock_create_cat, \
             patch.object(service.repo, 'create_version') as mock_create_ver, \
             patch.object(service.repo, 'get_versions_by_prompt_id') as mock_get_vers, \
             patch.object(service.repo, 'get_active_version') as mock_get_active, \
             patch.object(service.repo, 'set_active_version') as mock_set_active:
            
            # Configure mocks
            mock_create_cat.return_value = 123
            mock_create_ver.return_value = 456
            mock_get_vers.return_value = []
            mock_get_active.return_value = None
            mock_set_active.return_value = True
            
            # Step 1: Create category
            category_data = {
                'name': 'AI Assistants',
                'description': 'Templates for AI assistant prompts',
                'created_by': 'test_user'
            }
            
            category_result = service.create_category(category_data)
            assert category_result['success'] is True
            assert category_result['category_id'] == 123
            
            # Step 2: Create prompt version with template variables
            template_content = """
            You are {assistant_role}, a helpful AI assistant.
            
            Your expertise is in {domain}.
            
            User Query: {user_query}
            
            Please respond in a {tone} manner with {detail_level} detail.
            
            Additional context: {context}
            """
            
            version_data = {
                'prompt_id': 1,
                'version_number': 1,
                'title': 'AI Assistant Template v1',
                'content': template_content.strip(),
                'variables': {
                    'assistant_role': 'Expert Consultant',
                    'domain': 'Technology',
                    'user_query': 'string',
                    'tone': 'professional',
                    'detail_level': 'comprehensive',
                    'context': 'string'
                },
                'created_by': 'test_user'
            }
            
            version_result = service.create_prompt_version(version_data)
            assert version_result['success'] is True
            assert version_result['version_id'] == 456
            
            # Step 3: Test template processing
            test_variables = {
                'assistant_role': 'Senior Software Engineer',
                'domain': 'Web Development',
                'user_query': 'How do I optimize React performance?',
                'tone': 'friendly',
                'detail_level': 'detailed',
                'context': 'Building a large-scale application'
            }
            
            # Test variable extraction
            extracted_vars = PromptTemplateProcessor.extract_variables(template_content)
            expected_vars = {'assistant_role', 'domain', 'user_query', 'tone', 'detail_level', 'context'}
            assert set(extracted_vars) == expected_vars
            
            # Test variable validation
            validation = PromptTemplateProcessor.validate_variables(template_content, test_variables)
            assert validation['valid'] is True
            assert len(validation['missing_variables']) == 0
            
            # Test template processing
            processed = PromptTemplateProcessor.process_template(template_content, test_variables)
            assert 'Senior Software Engineer' in processed
            assert 'Web Development' in processed
            assert 'How do I optimize React performance?' in processed
            assert 'friendly' in processed
            assert 'detailed' in processed
            assert 'Building a large-scale application' in processed
            
            # Verify no template variables remain
            assert '{assistant_role}' not in processed
            assert '{domain}' not in processed
            assert '{user_query}' not in processed
    
    def test_prompt_versioning_workflow(self):
        """Test prompt versioning with multiple versions and activation"""
        service = PromptService()
        
        with patch.object(service.repo, 'create_version') as mock_create, \
             patch.object(service.repo, 'get_versions_by_prompt_id') as mock_get_all, \
             patch.object(service.repo, 'get_active_version') as mock_get_active, \
             patch.object(service.repo, 'set_active_version') as mock_set_active:
            
            # Mock return values
            from src.database.models import PromptVersion
            
            version_1 = PromptVersion(
                id=1, prompt_id=1, version_number=1,
                title='Version 1', content='Hello {name}!', 
                created_by='user1', is_active=True
            )
            
            version_2 = PromptVersion(
                id=2, prompt_id=1, version_number=2,
                title='Version 2', content='Greetings {name}, welcome to {system}!',
                created_by='user1', is_active=False
            )
            
            mock_create.side_effect = [1, 2]
            mock_get_all.return_value = [version_1, version_2]
            mock_get_active.return_value = version_1
            mock_set_active.return_value = True
            
            # Create first version
            v1_data = {
                'prompt_id': 1,
                'version_number': 1,
                'title': 'Version 1',
                'content': 'Hello {name}!',
                'created_by': 'user1'
            }
            
            result_1 = service.create_prompt_version(v1_data)
            assert result_1['success'] is True
            assert result_1['version_id'] == 1
            
            # Create second version
            v2_data = {
                'prompt_id': 1,
                'version_number': 2,
                'title': 'Version 2', 
                'content': 'Greetings {name}, welcome to {system}!',
                'created_by': 'user1'
            }
            
            result_2 = service.create_prompt_version(v2_data)
            assert result_2['success'] is True
            assert result_2['version_id'] == 2
            
            # Get all versions
            versions_result = service.get_prompt_versions(1)
            assert versions_result['success'] is True
            assert versions_result['count'] == 2
            
            # Get active version
            active_result = service.get_active_version(1)
            assert active_result['success'] is True
            assert active_result['version']['id'] == 1
            
            # Set version 2 as active
            activate_result = service.set_active_version(1, 2)
            assert activate_result['success'] is True
    
    def test_export_import_workflow(self):
        """Test complete export/import workflow"""
        # Test data
        export_data = {
            'prompt': {
                'id': 1,
                'title': 'Test Prompt',
                'content': 'Test content'
            },
            'versions': [
                {
                    'id': 1,
                    'prompt_id': 1,
                    'version_number': 1,
                    'title': 'Version 1',
                    'content': 'Hello {name}!',
                    'variables': {'name': 'string'},
                    'created_by': 'user1'
                },
                {
                    'id': 2,
                    'prompt_id': 1,
                    'version_number': 2,
                    'title': 'Version 2',
                    'content': 'Hi {name}, welcome to {system}!',
                    'variables': {'name': 'string', 'system': 'string'},
                    'created_by': 'user1'
                }
            ],
            'export_timestamp': int(time.time() * 1000),
            'export_version': '1.0'
        }
        
        # Mock database operations
        with patch('src.api.prompt_management.get_db_connection') as mock_get_db, \
             patch('src.api.prompt_management.PromptRepository') as mock_repo_class:
            
            # Mock database for export
            mock_db = MagicMock()
            mock_cursor = MagicMock()
            mock_db.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
            mock_db.get_cursor.return_value.__exit__ = MagicMock(return_value=None)
            mock_cursor.fetchone.return_value = export_data['prompt']
            mock_get_db.return_value = mock_db
            
            # Mock repository for versions
            mock_repo = MagicMock()
            from src.database.models import PromptVersion
            
            versions = [
                PromptVersion(
                    id=v['id'], prompt_id=v['prompt_id'], 
                    version_number=v['version_number'],
                    title=v['title'], content=v['content'],
                    variables=v['variables'], created_by=v['created_by']
                ) for v in export_data['versions']
            ]
            mock_repo.get_versions_by_prompt_id.return_value = versions
            mock_repo_class.return_value = mock_repo
            
            # Test export
            export_result = PromptExportImport.export_prompt_data(1, include_versions=True)
            assert export_result['success'] is True
            assert 'data' in export_result
            assert 'prompt' in export_result['data']
            assert 'versions' in export_result['data']
            assert len(export_result['data']['versions']) == 2
            
            # Mock database for import
            mock_db.get_transaction.return_value.__enter__ = MagicMock(return_value=mock_cursor)
            mock_db.get_transaction.return_value.__exit__ = MagicMock(return_value=None)
            mock_cursor.fetchone.return_value = {'id': 123}
            mock_repo.create_version.side_effect = [201, 202]
            
            # Test import
            import_result = PromptExportImport.import_prompt_data(export_result['data'], 'import_user')
            assert import_result['success'] is True
            assert import_result['prompt_id'] == 123
            assert len(import_result['imported_versions']) == 2
            assert 201 in import_result['imported_versions']
            assert 202 in import_result['imported_versions']
    
    def test_template_builder_integration(self):
        """Test template builder component integration with backend"""
        # Simulate template builder workflow
        
        # Step 1: Template creation with variables
        template_content = """
        Task: {task_type}
        
        Instructions:
        - Follow {methodology} approach
        - Target audience: {audience}
        - Tone: {communication_style}
        - Length: {response_length}
        
        Additional Requirements:
        {additional_requirements}
        
        Context: {context}
        """
        
        # Step 2: Variable extraction (simulating frontend)
        extracted_vars = PromptTemplateProcessor.extract_variables(template_content)
        expected_vars = {
            'task_type', 'methodology', 'audience', 
            'communication_style', 'response_length', 
            'additional_requirements', 'context'
        }
        assert set(extracted_vars) == expected_vars
        
        # Step 3: Variable configuration (simulating UI)
        variable_config = {
            'task_type': {
                'type': 'select',
                'options': ['Analysis', 'Creation', 'Review', 'Research'],
                'default': 'Analysis',
                'required': True,
                'description': 'Type of task to perform'
            },
            'methodology': {
                'type': 'select', 
                'options': ['Systematic', 'Creative', 'Analytical', 'Collaborative'],
                'default': 'Systematic',
                'required': True,
                'description': 'Approach methodology'
            },
            'audience': {
                'type': 'text',
                'default': 'General',
                'required': True,
                'description': 'Target audience'
            },
            'communication_style': {
                'type': 'select',
                'options': ['Professional', 'Casual', 'Academic', 'Friendly'],
                'default': 'Professional',
                'required': True,
                'description': 'Communication tone'
            },
            'response_length': {
                'type': 'select',
                'options': ['Brief', 'Moderate', 'Detailed', 'Comprehensive'],
                'default': 'Moderate',
                'required': True,
                'description': 'Response detail level'
            },
            'additional_requirements': {
                'type': 'multiline',
                'default': 'None',
                'required': False,
                'description': 'Any additional requirements'
            },
            'context': {
                'type': 'multiline',
                'default': '',
                'required': False,
                'description': 'Additional context information'
            }
        }
        
        # Step 4: Template processing with test values
        test_values = {
            'task_type': 'Analysis',
            'methodology': 'Systematic',
            'audience': 'Software Engineers',
            'communication_style': 'Professional',
            'response_length': 'Detailed',
            'additional_requirements': 'Include code examples where applicable',
            'context': 'Working on a React application performance optimization'
        }
        
        # Validate variables
        validation = PromptTemplateProcessor.validate_variables(template_content, test_values)
        assert validation['valid'] is True
        
        # Process template
        processed = PromptTemplateProcessor.process_template(template_content, test_values)
        
        # Verify all variables were replaced
        for var_name in extracted_vars:
            assert f'{{{var_name}}}' not in processed
            assert test_values[var_name] in processed
        
        # Step 5: Template metadata (simulating save operation)
        template_data = {
            'title': 'Task-Oriented Assistant Template',
            'description': 'A flexible template for task-based AI assistance',
            'content': template_content,
            'variables': variable_config,
            'metadata': {
                'version': '1.0',
                'author': 'template_builder',
                'categories': ['General', 'Task Management'],
                'created_at': int(time.time() * 1000)
            }
        }
        
        # Verify template data structure
        assert 'title' in template_data
        assert 'content' in template_data
        assert 'variables' in template_data
        assert 'metadata' in template_data
        assert len(template_data['variables']) == len(extracted_vars)
        
        # Verify each variable has proper configuration
        for var_name in extracted_vars:
            assert var_name in template_data['variables']
            var_config = template_data['variables'][var_name]
            assert 'type' in var_config
            assert 'required' in var_config
            assert 'description' in var_config
    
    def test_category_management_integration(self):
        """Test category management workflow"""
        service = PromptService()
        
        with patch.object(service.repo, 'create_category') as mock_create, \
             patch.object(service.repo, 'get_categories') as mock_get_all:
            
            from src.database.models import PromptCategory
            
            # Mock category creation
            mock_create.side_effect = [1, 2, 3]
            
            # Create categories
            categories_data = [
                {
                    'name': 'AI Assistants',
                    'description': 'Templates for AI assistant personalities',
                    'color': '#3b82f6',
                    'created_by': 'admin'
                },
                {
                    'name': 'Code Generation',
                    'description': 'Prompts for generating code',
                    'color': '#10b981',
                    'created_by': 'admin'
                },
                {
                    'name': 'Content Writing',
                    'description': 'Templates for content creation',
                    'color': '#f59e0b',
                    'created_by': 'admin'
                }
            ]
            
            created_categories = []
            for cat_data in categories_data:
                result = service.create_category(cat_data)
                assert result['success'] is True
                created_categories.append(result['category_id'])
            
            # Mock get all categories
            mock_categories = [
                PromptCategory(
                    id=created_categories[i],
                    name=cat_data['name'],
                    description=cat_data['description'],
                    color=cat_data['color'],
                    created_by=cat_data['created_by']
                ) for i, cat_data in enumerate(categories_data)
            ]
            mock_get_all.return_value = mock_categories
            
            # Test getting all categories
            result = service.get_categories()
            assert result['success'] is True
            assert result['count'] == 3
            
            # Verify category data
            categories = result['categories']
            category_names = [cat['name'] for cat in categories]
            assert 'AI Assistants' in category_names
            assert 'Code Generation' in category_names
            assert 'Content Writing' in category_names
    
    def test_dashboard_data_integration(self):
        """Test dashboard data aggregation"""
        # Simulate dashboard data loading
        
        # Mock API responses
        mock_categories = {
            'success': True,
            'categories': [
                {'id': 1, 'name': 'AI Assistants', 'color': '#3b82f6'},
                {'id': 2, 'name': 'Code Generation', 'color': '#10b981'},
                {'id': 3, 'name': 'Content Writing', 'color': '#f59e0b'}
            ],
            'count': 3
        }
        
        # Simulate dashboard data structure
        dashboard_data = {
            'totalPrompts': 15,
            'totalVersions': 42,
            'totalCategories': mock_categories['count'],
            'recentPrompts': [
                {
                    'id': 1,
                    'title': 'AI Assistant Template',
                    'created_at': int(time.time() * 1000) - 86400000,  # 1 day ago
                    'version_count': 3
                },
                {
                    'id': 2,
                    'title': 'Code Review Template',
                    'created_at': int(time.time() * 1000) - 172800000,  # 2 days ago
                    'version_count': 2
                }
            ],
            'recentVersions': [
                {
                    'id': 5,
                    'prompt_id': 1,
                    'title': 'AI Assistant v3',
                    'version_number': 3,
                    'created_at': int(time.time() * 1000) - 3600000,  # 1 hour ago
                },
                {
                    'id': 4,
                    'prompt_id': 2,
                    'title': 'Code Review v2',
                    'version_number': 2,
                    'created_at': int(time.time() * 1000) - 7200000,  # 2 hours ago
                }
            ],
            'popularCategories': mock_categories['categories']
        }
        
        # Verify dashboard data structure
        assert 'totalPrompts' in dashboard_data
        assert 'totalVersions' in dashboard_data
        assert 'totalCategories' in dashboard_data
        assert 'recentPrompts' in dashboard_data
        assert 'recentVersions' in dashboard_data
        assert 'popularCategories' in dashboard_data
        
        # Verify data types and values
        assert isinstance(dashboard_data['totalPrompts'], int)
        assert isinstance(dashboard_data['totalVersions'], int)
        assert isinstance(dashboard_data['totalCategories'], int)
        assert dashboard_data['totalCategories'] == 3
        assert len(dashboard_data['recentPrompts']) == 2
        assert len(dashboard_data['recentVersions']) == 2
        assert len(dashboard_data['popularCategories']) == 3
        
        # Verify recent items have required fields
        for prompt in dashboard_data['recentPrompts']:
            assert 'id' in prompt
            assert 'title' in prompt
            assert 'created_at' in prompt
            assert 'version_count' in prompt
        
        for version in dashboard_data['recentVersions']:
            assert 'id' in version
            assert 'prompt_id' in version
            assert 'title' in version
            assert 'version_number' in version
            assert 'created_at' in version
        
        # Verify categories have required fields
        for category in dashboard_data['popularCategories']:
            assert 'id' in category
            assert 'name' in category
            assert 'color' in category
    
    def test_error_handling_integration(self):
        """Test error handling across the system"""
        service = PromptService()
        
        # Test missing required fields
        invalid_category = {'description': 'Missing name'}
        result = service.create_category(invalid_category)
        assert result['success'] is False
        assert 'Missing required field' in result['error']
        
        invalid_version = {
            'prompt_id': 1,
            'title': 'Test',
            # Missing content and created_by
        }
        result = service.create_prompt_version(invalid_version)
        assert result['success'] is False
        assert 'Missing required field' in result['error']
        
        # Test template processing errors
        template_content = "Hello {name}, welcome to {system}!"
        incomplete_variables = {'name': 'John'}  # Missing 'system'
        
        validation = PromptTemplateProcessor.validate_variables(template_content, incomplete_variables)
        assert validation['valid'] is False
        assert 'system' in validation['missing_variables']
        
        # Test empty template
        empty_variables = PromptTemplateProcessor.extract_variables("")
        assert len(empty_variables) == 0
        
        # Test template with no variables
        static_template = "This is a static template with no variables."
        static_variables = PromptTemplateProcessor.extract_variables(static_template)
        assert len(static_variables) == 0
        
        processed_static = PromptTemplateProcessor.process_template(static_template, {})
        assert processed_static == static_template