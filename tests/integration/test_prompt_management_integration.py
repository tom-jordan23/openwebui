"""
Integration tests for Prompt Management API with database
"""
import pytest
import json
import time
from src.api.prompt_management import PromptService, prompt_bp
from src.database.models import PromptVersion, PromptCategory


@pytest.mark.integration
class TestPromptManagementIntegration:
    """Test prompt management API with real database connections"""
    
    def test_full_prompt_version_workflow(self, postgres_connection):
        """Test complete prompt version workflow: create, retrieve, activate"""
        service = PromptService()
        
        # Create test user first
        with service.repo.db.get_transaction() as cursor:
            current_time = int(time.time() * 1000)
            cursor.execute("""
                INSERT INTO "user" (id, name, email, role, profile_image_url, created_at, updated_at, last_active_at, api_key, settings, info)
                VALUES ('integration-user', 'Integration User', 'integration@test.com', 'user', '', %s, %s, %s, %s, '{}', '{}')
                ON CONFLICT (id) DO NOTHING
            """, (current_time, current_time, current_time, f'integration-api-{current_time}'))
        
        # Create a basic prompt to work with
        with service.repo.db.get_transaction() as cursor:
            current_time = int(time.time() * 1000)
            cursor.execute("""
                INSERT INTO prompt (command, user_id, title, content, timestamp)
                VALUES (%s, 'integration-user', 'Integration Test Prompt', 'Base content', %s)
                RETURNING id
            """, (f'test-integration-{current_time}', current_time))
            
            result = cursor.fetchone()
            prompt_id = result['id']
        
        # Test creating multiple versions
        version_1_data = {
            'prompt_id': prompt_id,
            'version_number': 1,
            'title': 'First Version',
            'content': 'Hello {name}, this is version 1 of {system}.',
            'variables': {'name': 'User', 'system': 'OpenWebUI'},
            'created_by': 'integration-user'
        }
        
        result_1 = service.create_prompt_version(version_1_data)
        assert result_1['success'] is True
        version_1_id = result_1['version_id']
        
        version_2_data = {
            'prompt_id': prompt_id,
            'version_number': 2,
            'title': 'Second Version',
            'content': 'Greetings {name}, welcome to {system} version 2!',
            'variables': {'name': 'User', 'system': 'OpenWebUI'},
            'created_by': 'integration-user'
        }
        
        result_2 = service.create_prompt_version(version_2_data)
        assert result_2['success'] is True
        version_2_id = result_2['version_id']
        
        # Test getting all versions
        versions_result = service.get_prompt_versions(prompt_id)
        assert versions_result['success'] is True
        assert versions_result['count'] >= 2
        
        version_titles = [v['title'] for v in versions_result['versions']]
        assert 'First Version' in version_titles
        assert 'Second Version' in version_titles
        
        # Test getting active version (should be the latest)
        active_result = service.get_active_version(prompt_id)
        assert active_result['success'] is True
        
        # Test setting a specific version as active
        set_active_result = service.set_active_version(prompt_id, version_1_id)
        assert set_active_result['success'] is True
        
        # Verify the active version changed
        new_active_result = service.get_active_version(prompt_id)
        assert new_active_result['success'] is True
        assert new_active_result['version']['id'] == version_1_id
    
    def test_category_management_workflow(self, postgres_connection):
        """Test complete category management workflow"""
        service = PromptService()
        
        # Create test user first
        with service.repo.db.get_transaction() as cursor:
            current_time = int(time.time() * 1000)
            cursor.execute("""
                INSERT INTO "user" (id, name, email, role, profile_image_url, created_at, updated_at, last_active_at, api_key, settings, info)
                VALUES ('integration-user-cat', 'Integration User Cat', 'integration-cat@test.com', 'user', '', %s, %s, %s, %s, '{}', '{}')
                ON CONFLICT (id) DO NOTHING
            """, (current_time, current_time, current_time, f'integration-cat-api-{current_time}'))
        
        # Create test categories
        category_1_data = {
            'name': 'Integration Test Category 1',
            'description': 'First test category',
            'color': '#FF0000',
            'created_by': 'integration-user-cat'
        }
        
        result_1 = service.create_category(category_1_data)
        assert result_1['success'] is True
        category_1_id = result_1['category_id']
        
        category_2_data = {
            'name': 'Integration Test Category 2',
            'description': 'Second test category',
            'color': '#00FF00',
            'created_by': 'integration-user-cat'
        }
        
        result_2 = service.create_category(category_2_data)
        assert result_2['success'] is True
        category_2_id = result_2['category_id']
        
        # Test getting all categories
        categories_result = service.get_categories()
        assert categories_result['success'] is True
        assert categories_result['count'] >= 2
        
        category_names = [c['name'] for c in categories_result['categories']]
        assert 'Integration Test Category 1' in category_names
        assert 'Integration Test Category 2' in category_names
        
        # Test duplicate name prevention
        duplicate_result = service.create_category(category_1_data)
        assert duplicate_result['success'] is False  # Should fail due to unique constraint
    
    def test_template_processing_integration(self, postgres_connection):
        """Test template processing with database-stored prompts"""
        service = PromptService()
        
        # Create test user first
        with service.repo.db.get_transaction() as cursor:
            current_time = int(time.time() * 1000)
            cursor.execute("""
                INSERT INTO "user" (id, name, email, role, profile_image_url, created_at, updated_at, last_active_at, api_key, settings, info)
                VALUES ('integration-user-tpl', 'Integration User Tpl', 'integration-tpl@test.com', 'user', '', %s, %s, %s, %s, '{}', '{}')
                ON CONFLICT (id) DO NOTHING
            """, (current_time, current_time, current_time, f'integration-tpl-api-{current_time}'))
        
        # Create a prompt with template variables
        with service.repo.db.get_transaction() as cursor:
            current_time = int(time.time() * 1000)
            cursor.execute("""
                INSERT INTO prompt (command, user_id, title, content, timestamp)
                VALUES (%s, 'integration-user-tpl', 'Template Test', 'Base content', %s)
                RETURNING id
            """, (f'template-test-{current_time}', current_time))
            
            result = cursor.fetchone()
            prompt_id = result['id']
        
        # Create a version with template variables
        template_content = """
        Hello {name},
        
        You have {message_count} new messages waiting in {system}.
        
        Your last login was {last_login}.
        
        Best regards,
        {assistant_name}
        """
        
        version_data = {
            'prompt_id': prompt_id,
            'version_number': 1,
            'title': 'Template Version',
            'content': template_content.strip(),
            'variables': {
                'name': 'string',
                'message_count': 'integer', 
                'system': 'string',
                'last_login': 'string',
                'assistant_name': 'string'
            },
            'created_by': 'integration-user-tpl'
        }
        
        create_result = service.create_prompt_version(version_data)
        assert create_result['success'] is True
        
        # Test template processing with the stored version
        from src.api.prompt_management import PromptTemplateProcessor
        
        test_variables = {
            'name': 'Alice',
            'message_count': '42',
            'system': 'OpenWebUI',
            'last_login': '2025-01-15',
            'assistant_name': 'Claude'
        }
        
        processed_content = PromptTemplateProcessor.process_template(
            template_content.strip(), 
            test_variables
        )
        
        assert 'Alice' in processed_content
        assert '42' in processed_content
        assert 'OpenWebUI' in processed_content
        assert '2025-01-15' in processed_content
        assert 'Claude' in processed_content
        
        # Verify variable extraction
        extracted_variables = PromptTemplateProcessor.extract_variables(template_content)
        expected_variables = {'name', 'message_count', 'system', 'last_login', 'assistant_name'}
        assert set(extracted_variables) == expected_variables
        
        # Test validation
        validation = PromptTemplateProcessor.validate_variables(template_content, test_variables)
        assert validation['valid'] is True
        assert len(validation['missing_variables']) == 0
    
    def test_export_import_integration(self, postgres_connection):
        """Test export/import functionality with real data"""
        service = PromptService()
        
        # Create test users first
        with service.repo.db.get_transaction() as cursor:
            for user_id in ['export-user', 'import-user']:
                current_time = int(time.time() * 1000)
                cursor.execute("""
                    INSERT INTO "user" (id, name, email, role, profile_image_url, created_at, updated_at, last_active_at, api_key, settings, info)
                    VALUES (%s, %s, %s, 'user', '', %s, %s, %s, %s, '{}', '{}')
                    ON CONFLICT (id) DO NOTHING
                """, (user_id, f'{user_id.title().replace("-", " ")}', f'{user_id}@test.com', current_time, current_time, current_time, f'{user_id}-api-{current_time}'))
        
        # Create test data
        with service.repo.db.get_transaction() as cursor:
            current_time = int(time.time() * 1000)
            cursor.execute("""
                INSERT INTO prompt (command, user_id, title, content, timestamp)
                VALUES (%s, 'export-user', 'Export Test Prompt', 'Export content', %s)
                RETURNING id
            """, (f'export-test-{current_time}', current_time))
            
            result = cursor.fetchone()
            prompt_id = result['id']
        
        # Create versions for the prompt
        for i in range(1, 4):
            version_data = {
                'prompt_id': prompt_id,
                'version_number': i,
                'title': f'Export Version {i}',
                'content': f'This is export test content version {i}',
                'created_by': 'export-user'
            }
            
            create_result = service.create_prompt_version(version_data)
            assert create_result['success'] is True
        
        # Test export
        from src.api.prompt_management import PromptExportImport
        
        export_result = PromptExportImport.export_prompt_data(prompt_id, include_versions=True)
        assert export_result['success'] is True
        assert 'data' in export_result
        
        export_data = export_result['data']
        assert 'prompt' in export_data
        assert 'versions' in export_data
        assert len(export_data['versions']) == 3
        
        # Test import
        import_result = PromptExportImport.import_prompt_data(export_data, 'import-user')
        assert import_result['success'] is True
        assert 'prompt_id' in import_result
        assert len(import_result['imported_versions']) == 3
        
        imported_prompt_id = import_result['prompt_id']
        
        # Verify imported data
        imported_versions_result = service.get_prompt_versions(imported_prompt_id)
        assert imported_versions_result['success'] is True
        assert imported_versions_result['count'] == 3
        
        imported_titles = [v['title'] for v in imported_versions_result['versions']]
        for i in range(1, 4):
            assert f'Export Version {i}' in imported_titles
    
    def test_error_handling_integration(self, postgres_connection):
        """Test error handling with real database constraints"""
        service = PromptService()
        
        # Test creating version with non-existent prompt_id
        invalid_version_data = {
            'prompt_id': 999999,  # Non-existent ID
            'version_number': 1,
            'title': 'Invalid Version',
            'content': 'This should fail',
            'created_by': 'test-user'
        }
        
        result = service.create_prompt_version(invalid_version_data)
        assert result['success'] is False
        # The error should be related to foreign key constraint
        
        # Test getting versions for non-existent prompt
        versions_result = service.get_prompt_versions(999999)
        assert versions_result['success'] is True
        assert versions_result['count'] == 0  # Empty result, not error
        
        # Test getting active version for non-existent prompt
        active_result = service.get_active_version(999999)
        assert active_result['success'] is False
        assert 'No active version found' in active_result['error']
    
    def test_concurrent_access_simulation(self, postgres_connection):
        """Test behavior under concurrent access (simulated sequentially)"""
        service = PromptService()
        
        # Create test users first
        with service.repo.db.get_transaction() as cursor:
            for i in range(5):
                user_id = f'user-{i + 1}'
                current_time = int(time.time() * 1000)
                cursor.execute("""
                    INSERT INTO "user" (id, name, email, role, profile_image_url, created_at, updated_at, last_active_at, api_key, settings, info)
                    VALUES (%s, %s, %s, 'user', '', %s, %s, %s, %s, '{}', '{}')
                    ON CONFLICT (id) DO NOTHING
                """, (user_id, f'User {i + 1}', f'{user_id}@test.com', current_time, current_time, current_time, f'{user_id}-api-{current_time}'))
            current_time = int(time.time() * 1000)
            cursor.execute("""
                INSERT INTO "user" (id, name, email, role, profile_image_url, created_at, updated_at, last_active_at, api_key, settings, info)
                VALUES ('concurrent-user', 'Concurrent User', 'concurrent-user@test.com', 'user', '', %s, %s, %s, %s, '{}', '{}')
                ON CONFLICT (id) DO NOTHING
            """, (current_time, current_time, current_time, f'concurrent-api-{current_time}'))
        
        # Create base prompt
        with service.repo.db.get_transaction() as cursor:
            current_time = int(time.time() * 1000)
            cursor.execute("""
                INSERT INTO prompt (command, user_id, title, content, timestamp)
                VALUES (%s, 'concurrent-user', 'Concurrent Test', 'Base content', %s)
                RETURNING id
            """, (f'concurrent-test-{current_time}', current_time))
            
            result = cursor.fetchone()
            prompt_id = result['id']
        
        # Simulate concurrent version creation
        version_ids = []
        for i in range(5):
            version_data = {
                'prompt_id': prompt_id,
                'version_number': i + 1,
                'title': f'Concurrent Version {i + 1}',
                'content': f'Concurrent content {i + 1}',
                'created_by': f'user-{i + 1}'
            }
            
            result = service.create_prompt_version(version_data)
            assert result['success'] is True
            version_ids.append(result['version_id'])
        
        # Verify all versions were created
        versions_result = service.get_prompt_versions(prompt_id)
        assert versions_result['success'] is True
        assert versions_result['count'] == 5
        
        # Test concurrent active version setting
        for version_id in version_ids[:3]:
            set_result = service.set_active_version(prompt_id, version_id)
            assert set_result['success'] is True
        
        # Verify final active version
        active_result = service.get_active_version(prompt_id)
        assert active_result['success'] is True
        # Should be the last one set as active
        assert active_result['version']['id'] == version_ids[2]