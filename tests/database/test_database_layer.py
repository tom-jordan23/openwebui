"""
Tests for database layer functionality
"""
import pytest
import time
from unittest.mock import patch
from src.database.connection import DatabaseConnection, DatabaseConfig
from src.database.models import PromptVersion, PromptCategory, AIAssistant, ConversationSession
from src.database.repositories import PromptRepository, AIAssistantRepository, ConversationRepository


class TestDatabaseConnection:
    """Test database connection functionality"""
    
    def test_database_config(self):
        """Test database configuration"""
        config = DatabaseConfig()
        assert config.host == 'localhost'
        assert config.port == 5432
        assert config.database == 'openwebui'
        assert config.user == 'postgres'
    
    def test_connection_params(self):
        """Test connection parameters generation"""
        config = DatabaseConfig()
        params = config.get_connection_params()
        
        required_keys = ['host', 'port', 'database', 'user', 'password']
        for key in required_keys:
            assert key in params
    
    def test_connection_string(self):
        """Test connection string generation"""
        config = DatabaseConfig()
        conn_str = config.connection_string
        assert 'postgresql://' in conn_str
        assert '@localhost:5432/openwebui' in conn_str
    
    @pytest.mark.integration
    def test_database_connection(self, postgres_connection):
        """Test actual database connection"""
        config = DatabaseConfig()
        db_conn = DatabaseConnection(config)
        
        # Test connection
        assert db_conn.test_connection() is True
        
        # Test cursor operations
        with db_conn.get_cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            assert result['test'] == 1


class TestDatabaseModels:
    """Test database model classes"""
    
    def test_prompt_version_model(self):
        """Test PromptVersion model"""
        version = PromptVersion(
            prompt_id=1,
            version_number=2,
            title="Test Version",
            content="This is test content",
            created_by="test_user",
            variables={"param1": "value1"}
        )
        
        # Test to_dict conversion
        data = version.to_dict()
        assert data['prompt_id'] == 1
        assert data['version_number'] == 2
        assert data['title'] == "Test Version"
        assert '"param1": "value1"' in data['variables']
        
        # Test from_db_row creation
        db_row = {
            'id': 1,
            'prompt_id': 1,
            'version_number': 2,
            'title': 'Test Version',
            'content': 'This is test content',
            'variables': '{"param1": "value1"}',
            'created_by': 'test_user',
            'created_at': int(time.time() * 1000),
            'is_active': False,
            'performance_metrics': '{}'
        }
        
        version_from_db = PromptVersion.from_db_row(db_row)
        assert version_from_db.prompt_id == 1
        assert version_from_db.variables['param1'] == "value1"
    
    def test_ai_assistant_model(self):
        """Test AIAssistant model"""
        assistant = AIAssistant(
            id="test-assistant-123",
            name="Test Assistant",
            description="A test assistant",
            system_prompt="You are a helpful assistant",
            model_id="llama3.2:1b",
            user_id="test-user",
            configuration={"temperature": 0.7},
            capabilities=["chat", "analysis"]
        )
        
        # Test to_dict conversion
        data = assistant.to_dict()
        assert data['id'] == "test-assistant-123"
        assert data['name'] == "Test Assistant"
        assert '"temperature": 0.7' in data['configuration']
        assert '"chat"' in data['capabilities']
        
        # Test from_db_row creation
        db_row = {
            'id': 'test-assistant-123',
            'name': 'Test Assistant',
            'description': 'A test assistant',
            'system_prompt': 'You are a helpful assistant',
            'model_id': 'llama3.2:1b',
            'user_id': 'test-user',
            'created_at': int(time.time() * 1000),
            'updated_at': int(time.time() * 1000),
            'is_active': True,
            'configuration': '{"temperature": 0.7}',
            'capabilities': '["chat", "analysis"]',
            'access_control': '{}',
            'performance_stats': '{}'
        }
        
        assistant_from_db = AIAssistant.from_db_row(db_row)
        assert assistant_from_db.id == "test-assistant-123"
        assert assistant_from_db.configuration['temperature'] == 0.7
        assert "chat" in assistant_from_db.capabilities
    
    def test_conversation_session_model(self):
        """Test ConversationSession model"""
        session = ConversationSession(
            id="session-123",
            chat_id="chat-456",
            assistant_id="assistant-789",
            user_id="user-abc",
            model_used="llama3.2:1b",
            message_count=5,
            total_tokens=150,
            avg_response_time=2.5,
            user_satisfaction=4,
            session_metadata={"source": "web"}
        )
        
        # Test to_dict conversion
        data = session.to_dict()
        assert data['id'] == "session-123"
        assert data['message_count'] == 5
        assert data['avg_response_time'] == 2.5
        assert '"source": "web"' in data['session_metadata']


class TestDatabaseRepositories:
    """Test repository classes"""
    
    @pytest.mark.integration
    def test_prompt_repository(self, postgres_connection):
        """Test PromptRepository operations"""
        repo = PromptRepository()
        
        # First, we need a prompt to work with
        # Let's check if there are any existing prompts
        with repo.db.get_cursor() as cursor:
            cursor.execute("SELECT id FROM prompt LIMIT 1")
            existing_prompt = cursor.fetchone()
            
            if not existing_prompt:
                # Create a test prompt if none exists
                cursor.execute("""
                    INSERT INTO prompt (command, user_id, title, content, timestamp)
                    VALUES ('test-prompt', 'test-user', 'Test Prompt', 'Test content', %s)
                    RETURNING id
                """, (int(time.time() * 1000),))
                existing_prompt = cursor.fetchone()
                repo.db.connection.commit()
        
        prompt_id = existing_prompt['id']
        
        # Test creating a prompt version
        version = PromptVersion(
            prompt_id=prompt_id,
            version_number=1,
            title="Test Version",
            content="This is a test version",
            created_by="test-user"
        )
        
        version_id = repo.create_version(version)
        assert version_id is not None
        assert isinstance(version_id, int)
        
        # Test retrieving the version
        retrieved_version = repo.get_version_by_id(version_id)
        assert retrieved_version is not None
        assert retrieved_version.prompt_id == prompt_id
        assert retrieved_version.title == "Test Version"
        
        # Test getting active version
        active_version = repo.get_active_version(prompt_id)
        assert active_version is not None
        assert active_version.is_active is True
        
        # Test creating a category
        category = PromptCategory(
            name="Test Category",
            description="A test category",
            color="#FF0000",
            created_by="test-user"
        )
        
        category_id = repo.create_category(category)
        assert category_id is not None
        
        # Test getting categories
        categories = repo.get_categories()
        assert len(categories) > 0
        assert any(cat.name == "Test Category" for cat in categories)
    
    @pytest.mark.integration  
    def test_ai_assistant_repository(self, postgres_connection):
        """Test AIAssistantRepository operations"""
        repo = AIAssistantRepository()
        
        # Create a test assistant
        assistant = AIAssistant(
            name="Test Assistant",
            description="A test assistant for repository testing",
            system_prompt="You are a test assistant",
            model_id="llama3.2:1b",  # Assuming this model exists
            user_id="test-user",
            configuration={"temperature": 0.8}
        )
        
        # Test creation
        created = repo.create(assistant)
        assert created is True
        assert assistant.id is not None
        
        # Test retrieval by ID
        retrieved = repo.get_by_id(assistant.id)
        assert retrieved is not None
        assert retrieved.name == "Test Assistant"
        assert retrieved.configuration['temperature'] == 0.8
        
        # Test retrieval by user ID
        user_assistants = repo.get_by_user_id("test-user")
        assert len(user_assistants) >= 1
        assert any(a.id == assistant.id for a in user_assistants)
        
        # Test update
        retrieved.description = "Updated description"
        updated = repo.update(retrieved)
        assert updated is True
        
        # Verify update
        updated_assistant = repo.get_by_id(assistant.id)
        assert updated_assistant.description == "Updated description"
        
        # Test soft delete
        deleted = repo.delete(assistant.id)
        assert deleted is True
        
        # Verify soft delete (should not appear in user_assistants anymore)
        user_assistants_after_delete = repo.get_by_user_id("test-user")
        assert not any(a.id == assistant.id for a in user_assistants_after_delete)
    
    @pytest.mark.integration
    def test_conversation_repository(self, postgres_connection):
        """Test ConversationRepository operations"""
        repo = ConversationRepository()
        
        # First create a test chat record if needed
        with repo.db.get_cursor() as cursor:
            cursor.execute("SELECT id FROM chat LIMIT 1")
            existing_chat = cursor.fetchone()
            
            if not existing_chat:
                # Create a test chat
                cursor.execute("""
                    INSERT INTO chat (id, user_id, title, archived, created_at, updated_at, meta)
                    VALUES ('test-chat', 'test-user', 'Test Chat', false, %s, %s, '{}')
                """, (int(time.time() * 1000), int(time.time() * 1000)))
                repo.db.connection.commit()
                chat_id = 'test-chat'
            else:
                chat_id = existing_chat['id']
        
        # Create a test conversation session
        session = ConversationSession(
            chat_id=chat_id,
            user_id="test-user",
            model_used="llama3.2:1b",
            message_count=3,
            total_tokens=100,
            avg_response_time=1.5
        )
        
        # Test creation
        created = repo.create_session(session)
        assert created is True
        assert session.id is not None
        
        # Test update
        session.message_count = 5
        session.ended_at = int(time.time() * 1000)
        session.user_satisfaction = 5
        
        updated = repo.update_session(session)
        assert updated is True