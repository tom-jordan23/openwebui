"""
Tests for Prompt Management API
"""
import pytest
import json
import time
from unittest.mock import patch, MagicMock
from src.api.prompt_management import (
    PromptService, 
    PromptTemplateProcessor, 
    PromptExportImport,
    prompt_bp
)
from src.database.models import PromptVersion, PromptCategory


class TestPromptService:
    """Test PromptService business logic"""
    
    def test_create_prompt_version_success(self):
        """Test successful prompt version creation"""
        service = PromptService()
        
        # Mock the repository
        with patch.object(service.repo, 'create_version') as mock_create:
            mock_create.return_value = 123
            
            prompt_data = {
                'prompt_id': 1,
                'title': 'Test Version',
                'content': 'This is test content',
                'created_by': 'test_user',
                'variables': {'param1': 'value1'}
            }
            
            result = service.create_prompt_version(prompt_data)
            
            assert result['success'] is True
            assert result['version_id'] == 123
            assert 'version' in result
            mock_create.assert_called_once()
    
    def test_create_prompt_version_missing_fields(self):
        """Test prompt version creation with missing required fields"""
        service = PromptService()
        
        prompt_data = {
            'title': 'Test Version',
            # Missing prompt_id, content, created_by
        }
        
        result = service.create_prompt_version(prompt_data)
        
        assert result['success'] is False
        assert 'Missing required field' in result['error']
    
    def test_create_prompt_version_db_failure(self):
        """Test prompt version creation with database failure"""
        service = PromptService()
        
        with patch.object(service.repo, 'create_version') as mock_create:
            mock_create.return_value = None  # Simulate DB failure
            
            prompt_data = {
                'prompt_id': 1,
                'title': 'Test Version',
                'content': 'This is test content',
                'created_by': 'test_user'
            }
            
            result = service.create_prompt_version(prompt_data)
            
            assert result['success'] is False
            assert result['error'] == 'Failed to create prompt version'
    
    def test_get_prompt_versions(self):
        """Test getting versions for a prompt"""
        service = PromptService()
        
        mock_versions = [
            PromptVersion(
                id=1, prompt_id=1, version_number=1, 
                title='Version 1', content='Content 1', created_by='user1'
            ),
            PromptVersion(
                id=2, prompt_id=1, version_number=2,
                title='Version 2', content='Content 2', created_by='user1'
            )
        ]
        
        with patch.object(service.repo, 'get_versions_by_prompt_id') as mock_get:
            mock_get.return_value = mock_versions
            
            result = service.get_prompt_versions(1)
            
            assert result['success'] is True
            assert result['count'] == 2
            assert len(result['versions']) == 2
    
    def test_get_active_version_success(self):
        """Test getting active version successfully"""
        service = PromptService()
        
        mock_version = PromptVersion(
            id=1, prompt_id=1, version_number=1,
            title='Active Version', content='Content', created_by='user1',
            is_active=True
        )
        
        with patch.object(service.repo, 'get_active_version') as mock_get:
            mock_get.return_value = mock_version
            
            result = service.get_active_version(1)
            
            assert result['success'] is True
            assert 'version' in result
    
    def test_get_active_version_not_found(self):
        """Test getting active version when none exists"""
        service = PromptService()
        
        with patch.object(service.repo, 'get_active_version') as mock_get:
            mock_get.return_value = None
            
            result = service.get_active_version(1)
            
            assert result['success'] is False
            assert result['error'] == 'No active version found'
    
    def test_set_active_version_success(self):
        """Test setting active version successfully"""
        service = PromptService()
        
        with patch.object(service.repo, 'set_active_version') as mock_set:
            mock_set.return_value = True
            
            result = service.set_active_version(1, 2)
            
            assert result['success'] is True
            assert 'Version 2 set as active' in result['message']
    
    def test_create_category_success(self):
        """Test successful category creation"""
        service = PromptService()
        
        with patch.object(service.repo, 'create_category') as mock_create:
            mock_create.return_value = 456
            
            category_data = {
                'name': 'Test Category',
                'description': 'A test category',
                'created_by': 'test_user'
            }
            
            result = service.create_category(category_data)
            
            assert result['success'] is True
            assert result['category_id'] == 456
    
    def test_get_categories(self):
        """Test getting all categories"""
        service = PromptService()
        
        mock_categories = [
            PromptCategory(id=1, name='Category 1', created_by='user1'),
            PromptCategory(id=2, name='Category 2', created_by='user1')
        ]
        
        with patch.object(service.repo, 'get_categories') as mock_get:
            mock_get.return_value = mock_categories
            
            result = service.get_categories()
            
            assert result['success'] is True
            assert result['count'] == 2


class TestPromptTemplateProcessor:
    """Test template processing functionality"""
    
    def test_process_template_basic(self):
        """Test basic template variable substitution"""
        content = "Hello {name}, welcome to {system}!"
        variables = {"name": "John", "system": "OpenWebUI"}
        
        processed = PromptTemplateProcessor.process_template(content, variables)
        
        assert processed == "Hello John, welcome to OpenWebUI!"
    
    def test_process_template_multiple_instances(self):
        """Test template with multiple instances of same variable"""
        content = "Hello {name}! Your name {name} is great."
        variables = {"name": "Alice"}
        
        processed = PromptTemplateProcessor.process_template(content, variables)
        
        assert processed == "Hello Alice! Your name Alice is great."
    
    def test_process_template_no_variables(self):
        """Test template with no variables"""
        content = "This is a static template."
        variables = {}
        
        processed = PromptTemplateProcessor.process_template(content, variables)
        
        assert processed == "This is a static template."
    
    def test_extract_variables_basic(self):
        """Test extracting variables from template"""
        content = "Hello {name}, you have {count} messages in {system}."
        
        variables = PromptTemplateProcessor.extract_variables(content)
        
        assert set(variables) == {"name", "count", "system"}
    
    def test_extract_variables_duplicates(self):
        """Test extracting variables removes duplicates"""
        content = "Hello {name}! Your name {name} appears twice."
        
        variables = PromptTemplateProcessor.extract_variables(content)
        
        assert variables == ["name"]
    
    def test_extract_variables_none(self):
        """Test extracting variables from static content"""
        content = "This has no variables."
        
        variables = PromptTemplateProcessor.extract_variables(content)
        
        assert variables == []
    
    def test_validate_variables_valid(self):
        """Test validation with all required variables"""
        content = "Hello {name}, you have {count} messages."
        variables = {"name": "John", "count": "5"}
        
        validation = PromptTemplateProcessor.validate_variables(content, variables)
        
        assert validation['valid'] is True
        assert validation['missing_variables'] == []
        assert set(validation['required_variables']) == {"name", "count"}
    
    def test_validate_variables_missing(self):
        """Test validation with missing variables"""
        content = "Hello {name}, you have {count} messages in {system}."
        variables = {"name": "John"}  # Missing count and system
        
        validation = PromptTemplateProcessor.validate_variables(content, variables)
        
        assert validation['valid'] is False
        assert set(validation['missing_variables']) == {"count", "system"}
        assert "name" in validation['provided_variables']
    
    def test_validate_variables_extra(self):
        """Test validation with extra variables"""
        content = "Hello {name}!"
        variables = {"name": "John", "extra": "value"}
        
        validation = PromptTemplateProcessor.validate_variables(content, variables)
        
        assert validation['valid'] is True  # Extra variables don't make it invalid
        assert validation['extra_variables'] == ["extra"]


class TestPromptExportImport:
    """Test export/import functionality"""
    
    @patch('src.api.prompt_management.get_db_connection')
    @patch('src.api.prompt_management.PromptRepository')
    def test_export_prompt_data_success(self, mock_repo_class, mock_get_db):
        """Test successful prompt data export"""
        # Mock database connection and cursor
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_db.get_cursor.return_value.__exit__ = MagicMock(return_value=None)
        mock_get_db.return_value = mock_db
        
        # Mock cursor fetchone to return prompt data
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'title': 'Test Prompt',
            'content': 'Test Content'
        }
        
        # Mock repository
        mock_repo = MagicMock()
        mock_versions = [
            PromptVersion(id=1, prompt_id=1, version_number=1, 
                         title='Version 1', content='Content 1', created_by='user1')
        ]
        mock_repo.get_versions_by_prompt_id.return_value = mock_versions
        mock_repo_class.return_value = mock_repo
        
        result = PromptExportImport.export_prompt_data(1, include_versions=True)
        
        assert result['success'] is True
        assert 'data' in result
        assert 'prompt' in result['data']
        assert 'versions' in result['data']
        assert len(result['data']['versions']) == 1
    
    @patch('src.api.prompt_management.get_db_connection')
    def test_export_prompt_data_not_found(self, mock_get_db):
        """Test export when prompt not found"""
        # Mock database connection and cursor
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_db.get_cursor.return_value.__exit__ = MagicMock(return_value=None)
        mock_get_db.return_value = mock_db
        
        # Mock cursor fetchone to return None (not found)
        mock_cursor.fetchone.return_value = None
        
        result = PromptExportImport.export_prompt_data(999)
        
        assert result['success'] is False
        assert 'not found' in result['error']
    
    @patch('src.api.prompt_management.get_db_connection')
    @patch('src.api.prompt_management.PromptRepository')
    def test_import_prompt_data_success(self, mock_repo_class, mock_get_db):
        """Test successful prompt data import"""
        # Mock database connection and transaction
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.get_transaction.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_db.get_transaction.return_value.__exit__ = MagicMock(return_value=None)
        mock_get_db.return_value = mock_db
        
        # Mock cursor fetchone to return new prompt ID
        mock_cursor.fetchone.return_value = {'id': 123}
        
        # Mock repository
        mock_repo = MagicMock()
        mock_repo.create_version.return_value = 456
        mock_repo_class.return_value = mock_repo
        
        import_data = {
            'prompt': {
                'title': 'Imported Prompt',
                'content': 'Imported content'
            },
            'versions': [
                {
                    'version_number': 1,
                    'title': 'Version 1',
                    'content': 'Version content',
                    'variables': {}
                }
            ]
        }
        
        result = PromptExportImport.import_prompt_data(import_data, 'test_user')
        
        assert result['success'] is True
        assert result['prompt_id'] == 123
        assert len(result['imported_versions']) == 1
    
    def test_import_prompt_data_missing_prompt(self):
        """Test import with missing prompt data"""
        import_data = {
            'versions': []  # Missing 'prompt' key
        }
        
        result = PromptExportImport.import_prompt_data(import_data, 'test_user')
        
        assert result['success'] is False
        assert 'Missing prompt data' in result['error']


@pytest.fixture
def app():
    """Create Flask app for testing"""
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(prompt_bp)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestPromptManagementAPI:
    """Test API endpoints"""
    
    def test_create_version_endpoint_success(self, client):
        """Test POST /api/v1/prompts/versions success"""
        with patch('src.api.prompt_management.prompt_service') as mock_service:
            mock_service.create_prompt_version.return_value = {
                'success': True,
                'version_id': 123,
                'version': {'id': 123, 'title': 'Test'},
                'message': 'Created successfully'
            }
            
            response = client.post(
                '/api/v1/prompts/versions',
                json={
                    'prompt_id': 1,
                    'title': 'Test Version',
                    'content': 'Test content',
                    'created_by': 'test_user'
                },
                content_type='application/json'
            )
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['version_id'] == 123
    
    def test_create_version_endpoint_no_data(self, client):
        """Test POST /api/v1/prompts/versions with no data"""
        response = client.post(
            '/api/v1/prompts/versions',
            json=None,  # Explicitly send null JSON
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'No data provided' in data['error']
    
    def test_create_version_endpoint_failure(self, client):
        """Test POST /api/v1/prompts/versions failure"""
        with patch('src.api.prompt_management.prompt_service') as mock_service:
            mock_service.create_prompt_version.return_value = {
                'success': False,
                'error': 'Creation failed'
            }
            
            response = client.post(
                '/api/v1/prompts/versions',
                json={'prompt_id': 1},
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['success'] is False
    
    def test_get_versions_endpoint_success(self, client):
        """Test GET /api/v1/prompts/{id}/versions success"""
        with patch('src.api.prompt_management.prompt_service') as mock_service:
            mock_service.get_prompt_versions.return_value = {
                'success': True,
                'versions': [{'id': 1, 'title': 'Version 1'}],
                'count': 1
            }
            
            response = client.get('/api/v1/prompts/1/versions')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['count'] == 1
    
    def test_get_active_version_endpoint(self, client):
        """Test GET /api/v1/prompts/{id}/versions/active"""
        with patch('src.api.prompt_management.prompt_service') as mock_service:
            mock_service.get_active_version.return_value = {
                'success': True,
                'version': {'id': 1, 'is_active': True}
            }
            
            response = client.get('/api/v1/prompts/1/versions/active')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_activate_version_endpoint(self, client):
        """Test POST /api/v1/prompts/{id}/versions/{version_id}/activate"""
        with patch('src.api.prompt_management.prompt_service') as mock_service:
            mock_service.set_active_version.return_value = {
                'success': True,
                'message': 'Version activated'
            }
            
            response = client.post('/api/v1/prompts/1/versions/2/activate')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_create_category_endpoint(self, client):
        """Test POST /api/v1/prompts/categories"""
        with patch('src.api.prompt_management.prompt_service') as mock_service:
            mock_service.create_category.return_value = {
                'success': True,
                'category_id': 789,
                'category': {'id': 789, 'name': 'Test Category'}
            }
            
            response = client.post(
                '/api/v1/prompts/categories',
                json={
                    'name': 'Test Category',
                    'description': 'A test category',
                    'created_by': 'test_user'
                },
                content_type='application/json'
            )
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['category_id'] == 789
    
    def test_get_categories_endpoint(self, client):
        """Test GET /api/v1/prompts/categories"""
        with patch('src.api.prompt_management.prompt_service') as mock_service:
            mock_service.get_categories.return_value = {
                'success': True,
                'categories': [{'id': 1, 'name': 'Category 1'}],
                'count': 1
            }
            
            response = client.get('/api/v1/prompts/categories')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['count'] == 1
    
    def test_process_template_endpoint_success(self, client):
        """Test POST /api/v1/prompts/template/process success"""
        response = client.post(
            '/api/v1/prompts/template/process',
            json={
                'content': 'Hello {name}!',
                'variables': {'name': 'World'}
            },
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['processed_content'] == 'Hello World!'
    
    def test_process_template_endpoint_missing_variables(self, client):
        """Test POST /api/v1/prompts/template/process with missing variables"""
        response = client.post(
            '/api/v1/prompts/template/process',
            json={
                'content': 'Hello {name}, you have {count} messages!',
                'variables': {'name': 'John'}  # Missing 'count'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Missing required variables' in data['error']
    
    def test_extract_template_variables_endpoint(self, client):
        """Test POST /api/v1/prompts/template/variables"""
        response = client.post(
            '/api/v1/prompts/template/variables',
            json={'content': 'Hello {name}, you have {count} messages!'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert set(data['variables']) == {'name', 'count'}
        assert data['count'] == 2
    
    def test_export_prompt_endpoint(self, client):
        """Test GET /api/v1/prompts/{id}/export"""
        with patch('src.api.prompt_management.PromptExportImport') as mock_export:
            mock_export.export_prompt_data.return_value = {
                'success': True,
                'data': {'prompt': {'id': 1}, 'versions': []}
            }
            
            response = client.get('/api/v1/prompts/1/export?include_versions=true')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            mock_export.export_prompt_data.assert_called_once_with(1, True)
    
    def test_import_prompt_endpoint_success(self, client):
        """Test POST /api/v1/prompts/import success"""
        with patch('src.api.prompt_management.PromptExportImport') as mock_import:
            mock_import.import_prompt_data.return_value = {
                'success': True,
                'prompt_id': 123,
                'imported_versions': [456],
                'message': 'Imported successfully'
            }
            
            response = client.post(
                '/api/v1/prompts/import',
                json={
                    'user_id': 'test_user',
                    'data': {
                        'prompt': {'title': 'Imported', 'content': 'Content'},
                        'versions': []
                    }
                },
                content_type='application/json'
            )
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['prompt_id'] == 123
    
    def test_import_prompt_endpoint_missing_user_id(self, client):
        """Test POST /api/v1/prompts/import without user_id"""
        response = client.post(
            '/api/v1/prompts/import',
            json={
                'data': {'prompt': {}, 'versions': []}
                # Missing user_id
            },
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Missing user_id' in data['error']