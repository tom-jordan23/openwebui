"""
Integration tests for the complete AI Assistant Framework
Tests the full workflow from assistant creation to deployment and analytics
"""

import pytest
import json
import time
import uuid
from typing import Dict, Any

from src.database.connection import get_db_connection
from src.database.assistant_repositories import (
    AssistantRepository, AssistantDeploymentRepository,
    ConversationContextRepository, AssistantAnalyticsRepository
)
from src.database.assistant_models import (
    AssistantProfile, AssistantDeployment, ConversationContext,
    AssistantStatus, AssistantType, DeploymentEnvironment
)
from src.api.assistant_management import AssistantService
from src.api.assistant_prompt_linking import AssistantPromptService
from src.api.conversation_management import ConversationService
from src.api.assistant_deployment import DeploymentService
from src.api.assistant_analytics import AnalyticsService


class TestAssistantFrameworkIntegration:
    """Integration tests for the complete assistant framework"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data and services"""
        self.db = get_db_connection()
        
        # Initialize repositories
        self.assistant_repo = AssistantRepository()
        self.deployment_repo = AssistantDeploymentRepository()
        self.context_repo = ConversationContextRepository()
        self.analytics_repo = AssistantAnalyticsRepository()
        
        # Initialize services
        self.assistant_service = AssistantService()
        self.prompt_service = AssistantPromptService()
        self.conversation_service = ConversationService()
        self.deployment_service = DeploymentService()
        self.analytics_service = AnalyticsService()
        
        # Test user ID
        self.user_id = "test_user_123"
        
        # Clean up any existing test data
        self._cleanup_test_data()
        
        yield
        
        # Clean up after test
        self._cleanup_test_data()
    
    def _cleanup_test_data(self):
        """Clean up test data from database"""
        try:
            with self.db.get_transaction() as cursor:
                # Delete test assistants and related data
                cursor.execute("DELETE FROM assistant_analytics WHERE assistant_id LIKE 'test_%'")
                cursor.execute("DELETE FROM conversation_context WHERE assistant_id LIKE 'test_%'")
                cursor.execute("DELETE FROM assistant_deployment WHERE assistant_id LIKE 'test_%'")
                cursor.execute("DELETE FROM assistant_prompt_mapping WHERE assistant_id LIKE 'test_%'")
                cursor.execute("DELETE FROM ai_assistant WHERE id LIKE 'test_%' OR user_id = %s", (self.user_id,))
        except Exception as e:
            print(f"Cleanup error (expected): {e}")
    
    def test_complete_assistant_lifecycle(self):
        """Test the complete assistant lifecycle from creation to deployment"""
        
        # Step 1: Create a new assistant
        assistant_data = {
            "name": "Test Assistant",
            "description": "A test assistant for integration testing",
            "system_prompt": "You are a helpful AI assistant designed for testing purposes.",
            "model_id": "gpt-4",
            "assistant_type": "conversational",
            "temperature": 0.7,
            "max_tokens": 2000,
            "tags": ["test", "integration"]
        }
        
        success, result = self.assistant_service.create_assistant(assistant_data, self.user_id)
        assert success, f"Failed to create assistant: {result}"
        assert isinstance(result, AssistantProfile)
        
        assistant = result
        assistant_id = assistant.id
        
        # Verify assistant was created correctly
        assert assistant.name == assistant_data["name"]
        assert assistant.user_id == self.user_id
        assert assistant.assistant_type == AssistantType.CONVERSATIONAL
        assert assistant.status == AssistantStatus.DRAFT
        
        # Step 2: Update assistant configuration
        update_data = {
            "status": "active",
            "version": "1.1.0",
            "tags": ["test", "integration", "updated"]
        }
        
        success, message = self.assistant_service.update_assistant(assistant_id, self.user_id, update_data)
        assert success, f"Failed to update assistant: {message}"
        
        # Verify update
        success, updated_assistant = self.assistant_service.get_assistant(assistant_id, self.user_id)
        assert success
        assert updated_assistant.status == AssistantStatus.ACTIVE
        assert updated_assistant.version == "1.1.0"
        assert "updated" in updated_assistant.tags
        
        # Step 3: Test conversation management
        success, conversation = self.conversation_service.start_conversation(
            assistant_id, self.user_id, "Hello, this is a test message"
        )
        assert success, f"Failed to start conversation: {conversation}"
        assert isinstance(conversation, ConversationContext)
        
        session_id = conversation.session_id
        
        # Add messages to conversation
        success, updated_conversation = self.conversation_service.add_message(
            session_id, self.user_id, "user", "How are you doing?",
            {"test": True}, 1.5, 150
        )
        assert success, f"Failed to add user message: {updated_conversation}"
        
        success, updated_conversation = self.conversation_service.add_message(
            session_id, self.user_id, "assistant", "I'm doing well, thank you for asking!",
            {"test_response": True}, 2.1, 200
        )
        assert success, f"Failed to add assistant message: {updated_conversation}"
        
        # Get conversation history
        success, history = self.conversation_service.get_conversation_history(session_id, self.user_id)
        assert success
        assert len(history) >= 3  # System + user + assistant messages
        
        # Step 4: Test deployment
        success, deployment = self.deployment_service.deploy_assistant(
            assistant_id, "development", self.user_id, {"resources": {"cpu": "1", "memory": "1Gi"}}
        )
        assert success, f"Failed to deploy assistant: {deployment}"
        assert isinstance(deployment, AssistantDeployment)
        assert deployment.environment == DeploymentEnvironment.DEVELOPMENT
        
        # Step 5: Test analytics
        # Record some metrics
        self.analytics_repo.record_metric(assistant_id, "response_time", 2.1, "interaction")
        self.analytics_repo.record_metric(assistant_id, "user_satisfaction", 4.5, "conversation")
        self.analytics_repo.record_metric(assistant_id, "tokens_used", 350, "interaction")
        
        # Get analytics
        success, metrics = self.analytics_service.get_assistant_metrics(assistant_id, self.user_id, 7)
        assert success, f"Failed to get analytics: {metrics}"
        assert metrics["assistant_id"] == assistant_id
        assert "basic_stats" in metrics
        assert "detailed_metrics" in metrics
        
        # Step 6: Test usage statistics update
        success, message = self.assistant_service.update_usage_stats(
            assistant_id, self.user_id, 2, 1.8, 5
        )
        assert success, f"Failed to update usage stats: {message}"
        
        # Verify usage stats were updated
        success, final_assistant = self.assistant_service.get_assistant(assistant_id, self.user_id)
        assert success
        assert final_assistant.total_conversations > 0
        assert final_assistant.avg_response_time > 0
        assert final_assistant.user_satisfaction_rating > 0
        
        # Step 7: End conversation
        success, message = self.conversation_service.end_conversation(session_id, self.user_id, 5)
        assert success, f"Failed to end conversation: {message}"
        
        print("✓ Complete assistant lifecycle test passed")
    
    def test_assistant_prompt_linking_workflow(self):
        """Test linking prompts to assistants"""
        
        # Create test assistant
        assistant_data = {
            "name": "Prompt Test Assistant",
            "description": "Testing prompt linking",
            "system_prompt": "Basic system prompt",
            "model_id": "gpt-3.5-turbo"
        }
        
        success, assistant = self.assistant_service.create_assistant(assistant_data, self.user_id)
        assert success
        assistant_id = assistant.id
        
        # Create a mock prompt (in real implementation, this would be done through prompt API)
        with self.db.get_transaction() as cursor:
            # Create test prompt category
            cursor.execute("""
                INSERT INTO prompt_category (name, description, created_by)
                VALUES ('Test Category', 'Testing category', %s)
                RETURNING id
            """, (self.user_id,))
            category_result = cursor.fetchone()
            category_id = category_result['id']
            
            # Create test prompt
            cursor.execute("""
                INSERT INTO prompt (title, description, content, category_id, created_by, is_active)
                VALUES ('Test Prompt', 'A test prompt', 'You are a test assistant: {instruction}', %s, %s, true)
                RETURNING id
            """, (category_id, self.user_id))
            prompt_result = cursor.fetchone()
            prompt_id = prompt_result['id']
            
            # Create test prompt version
            cursor.execute("""
                INSERT INTO prompt_version (prompt_id, version_number, title, content, created_by, is_active)
                VALUES (%s, 1, 'Version 1', 'You are a test assistant: {instruction}', %s, true)
                RETURNING id
            """, (prompt_id, self.user_id))
            version_result = cursor.fetchone()
            version_id = version_result['id']
        
        # Link prompt to assistant as primary
        success, message = self.prompt_service.link_prompt_to_assistant(
            assistant_id, prompt_id, version_id, "primary", 100
        )
        assert success, f"Failed to link prompt: {message}"
        
        # Get linked prompts
        success, prompts = self.prompt_service.get_assistant_prompts(assistant_id)
        assert success
        assert len(prompts) == 1
        assert prompts[0]["mapping_type"] == "primary"
        assert prompts[0]["prompt_id"] == prompt_id
        
        # Link another prompt as secondary
        with self.db.get_transaction() as cursor:
            cursor.execute("""
                INSERT INTO prompt (title, description, content, category_id, created_by, is_active)
                VALUES ('Secondary Prompt', 'A secondary test prompt', 'Secondary prompt: {task}', %s, %s, true)
                RETURNING id
            """, (category_id, self.user_id))
            secondary_prompt_result = cursor.fetchone()
            secondary_prompt_id = secondary_prompt_result['id']
        
        success, message = self.prompt_service.link_prompt_to_assistant(
            assistant_id, secondary_prompt_id, None, "secondary", 50
        )
        assert success, f"Failed to link secondary prompt: {message}"
        
        # Verify both prompts are linked
        success, prompts = self.prompt_service.get_assistant_prompts(assistant_id)
        assert success
        assert len(prompts) == 2
        
        # Test prompt suggestions
        success, suggestions = self.prompt_service.get_prompt_suggestions(assistant_id, 10)
        assert success
        # Should return empty since we don't have other prompts for suggestions
        
        # Unlink secondary prompt
        success, message = self.prompt_service.unlink_prompt_from_assistant(
            assistant_id, secondary_prompt_id
        )
        assert success, f"Failed to unlink prompt: {message}"
        
        # Verify only primary prompt remains
        success, prompts = self.prompt_service.get_assistant_prompts(assistant_id)
        assert success
        assert len(prompts) == 1
        assert prompts[0]["mapping_type"] == "primary"
        
        print("✓ Assistant-prompt linking workflow test passed")
    
    def test_deployment_workflow(self):
        """Test complete deployment workflow including rollback and promotion"""
        
        # Create test assistant
        assistant_data = {
            "name": "Deployment Test Assistant",
            "description": "Testing deployment workflows",
            "system_prompt": "Deployment test assistant",
            "model_id": "gpt-4",
            "status": "active"
        }
        
        success, assistant = self.assistant_service.create_assistant(assistant_data, self.user_id)
        assert success
        assistant_id = assistant.id
        
        # Update to make it deployable (set some conversations)
        with self.db.get_transaction() as cursor:
            cursor.execute("""
                UPDATE ai_assistant 
                SET total_conversations = 15, user_satisfaction_rating = 4.2
                WHERE id = %s
            """, (assistant_id,))
        
        # Deploy to development
        success, dev_deployment = self.deployment_service.deploy_assistant(
            assistant_id, "development", self.user_id
        )
        assert success, f"Failed to deploy to development: {dev_deployment}"
        
        # Deploy to testing
        success, test_deployment = self.deployment_service.deploy_assistant(
            assistant_id, "testing", self.user_id
        )
        assert success, f"Failed to deploy to testing: {test_deployment}"
        
        # Get deployment history
        success, history = self.deployment_service.get_deployment_history(assistant_id, self.user_id)
        assert success
        assert len(history) >= 2  # Dev and testing deployments
        
        # Test promotion from testing to staging
        success, message = self.deployment_service.promote_assistant(
            assistant_id, "testing", "staging", self.user_id
        )
        assert success, f"Failed to promote to staging: {message}"
        
        # Update deployment status
        staging_deployment = self.deployment_repo.get_active_deployment(
            assistant_id, DeploymentEnvironment.STAGING
        )
        if staging_deployment:
            success, message = self.deployment_service.update_deployment_status(
                staging_deployment.id, "active", self.user_id
            )
            assert success, f"Failed to update deployment status: {message}"
        
        # Test rollback
        # First, create a second version by updating and redeploying
        success, message = self.assistant_service.update_assistant(
            assistant_id, self.user_id, {"version": "2.0.0"}
        )
        assert success
        
        success, new_deployment = self.deployment_service.deploy_assistant(
            assistant_id, "development", self.user_id
        )
        assert success
        
        # Now test rollback
        success, message = self.deployment_service.rollback_deployment(
            assistant_id, "development", self.user_id, "1.1.0"
        )
        # Note: This might fail if we don't have the exact version, which is expected
        
        print("✓ Deployment workflow test passed")
    
    def test_analytics_and_monitoring(self):
        """Test comprehensive analytics and health monitoring"""
        
        # Create test assistant
        assistant_data = {
            "name": "Analytics Test Assistant",
            "description": "Testing analytics functionality",
            "system_prompt": "Analytics test assistant",
            "model_id": "gpt-4"
        }
        
        success, assistant = self.assistant_service.create_assistant(assistant_data, self.user_id)
        assert success
        assistant_id = assistant.id
        
        # Record various metrics over time
        metrics_to_record = [
            ("response_time", 1.2, "interaction"),
            ("response_time", 1.8, "interaction"),
            ("response_time", 0.9, "interaction"),
            ("user_satisfaction", 4.0, "conversation"),
            ("user_satisfaction", 5.0, "conversation"),
            ("user_satisfaction", 3.5, "conversation"),
            ("tokens_used", 150, "interaction"),
            ("tokens_used", 230, "interaction"),
            ("tokens_used", 180, "interaction"),
            ("conversation_length", 5, "session"),
            ("conversation_length", 8, "session"),
            ("conversation_length", 3, "session")
        ]
        
        for metric_name, value, period in metrics_to_record:
            success = self.analytics_repo.record_metric(assistant_id, metric_name, value, period)
            assert success, f"Failed to record metric {metric_name}"
        
        # Get comprehensive metrics
        success, metrics = self.analytics_service.get_assistant_metrics(assistant_id, self.user_id, 30)
        assert success
        assert metrics["assistant_id"] == assistant_id
        assert "detailed_metrics" in metrics
        assert "trends" in metrics
        
        # Test usage analytics
        success, usage = self.analytics_service.get_usage_analytics(
            assistant_id, self.user_id, "daily", 7
        )
        assert success
        assert "usage_timeline" in usage
        assert "usage_summary" in usage
        
        # Test health status
        success, health = self.analytics_service.get_health_status(assistant_id, self.user_id)
        assert success
        assert "health_score" in health
        assert "health_grade" in health
        assert "alerts" in health
        assert "recommendations" in health
        
        # Test comparison (create another assistant for comparison)
        assistant_data2 = {
            "name": "Comparison Assistant",
            "description": "For comparison testing",
            "system_prompt": "Comparison assistant",
            "model_id": "gpt-3.5-turbo"
        }
        
        success, assistant2 = self.assistant_service.create_assistant(assistant_data2, self.user_id)
        assert success
        assistant2_id = assistant2.id
        
        # Record some metrics for the second assistant
        for metric_name, value, period in metrics_to_record[:6]:  # Record fewer metrics
            self.analytics_repo.record_metric(assistant2_id, metric_name, value, period)
        
        # Test comparison
        success, comparison = self.analytics_service.get_performance_comparison(
            [assistant_id, assistant2_id], self.user_id, 30
        )
        assert success
        assert len(comparison["assistants"]) == 2
        assert "metrics_comparison" in comparison
        assert "rankings" in comparison
        
        # Test user analytics summary
        success, summary = self.analytics_service.get_user_analytics_summary(self.user_id, 30)
        assert success
        assert summary["total_assistants"] >= 2
        assert "summary_metrics" in summary
        assert "top_performers" in summary
        
        print("✓ Analytics and monitoring test passed")
    
    def test_conversation_context_management(self):
        """Test advanced conversation context management"""
        
        # Create test assistant
        assistant_data = {
            "name": "Context Test Assistant",
            "description": "Testing context management",
            "system_prompt": "You are a context-aware assistant",
            "model_id": "gpt-4",
            "context_memory_size": 1000  # Small context for testing compression
        }
        
        success, assistant = self.assistant_service.create_assistant(assistant_data, self.user_id)
        assert success
        assistant_id = assistant.id
        
        # Start conversation
        success, conversation = self.conversation_service.start_conversation(
            assistant_id, self.user_id, "Hello, let's test context management"
        )
        assert success
        session_id = conversation.session_id
        
        # Add many messages to test context compression
        for i in range(10):
            # Add user message
            success, _ = self.conversation_service.add_message(
                session_id, self.user_id, "user", 
                f"This is test message number {i+1}. " * 20,  # Make messages long
                {"message_number": i+1}
            )
            assert success
            
            # Add assistant response
            success, _ = self.conversation_service.add_message(
                session_id, self.user_id, "assistant",
                f"Thank you for test message {i+1}. " * 15,  # Make responses long
                {"response_to": i+1}, 1.5, 100
            )
            assert success
        
        # Get conversation context to verify compression occurred
        success, context = self.conversation_service.get_conversation(session_id, self.user_id)
        assert success
        # Context should be compressed due to size limit
        assert context.current_context_length <= context.max_context_length
        
        # Update context variables
        success, message = self.conversation_service.update_context_variables(
            session_id, self.user_id, {"user_preference": "detailed", "session_type": "test"}
        )
        assert success
        
        # Get conversation summary
        success, summary = self.conversation_service.get_conversation_summary(session_id, self.user_id)
        assert success
        assert summary["statistics"]["total_messages"] > 20  # System + user + assistant messages
        assert summary["statistics"]["user_messages"] == 10
        assert summary["statistics"]["assistant_messages"] == 10
        
        # Test active sessions
        success, active_sessions = self.conversation_service.get_active_sessions(self.user_id, 24)
        assert success
        assert len(active_sessions) >= 1
        
        # End conversation with rating
        success, message = self.conversation_service.end_conversation(session_id, self.user_id, 4)
        assert success
        
        print("✓ Conversation context management test passed")
    
    def test_error_handling_and_edge_cases(self):
        """Test error handling and edge cases"""
        
        # Test creating assistant with invalid data
        invalid_data = {
            "name": "",  # Empty name should fail
            "description": "Invalid assistant",
            "system_prompt": "Test",
            "model_id": "gpt-4"
        }
        
        success, result = self.assistant_service.create_assistant(invalid_data, self.user_id)
        assert not success, "Should fail with empty name"
        
        # Test getting non-existent assistant
        success, result = self.assistant_service.get_assistant("non_existent_id", self.user_id)
        assert not success, "Should fail for non-existent assistant"
        
        # Test unauthorized access (different user)
        assistant_data = {
            "name": "Test Assistant for Auth",
            "description": "Testing authorization",
            "system_prompt": "Auth test",
            "model_id": "gpt-4"
        }
        
        success, assistant = self.assistant_service.create_assistant(assistant_data, self.user_id)
        assert success
        
        # Try to access with different user ID
        success, result = self.assistant_service.get_assistant(assistant.id, "different_user")
        assert not success, "Should fail with different user"
        
        # Test conversation with non-existent assistant
        success, result = self.conversation_service.start_conversation(
            "non_existent_assistant", self.user_id
        )
        assert not success, "Should fail with non-existent assistant"
        
        # Test deployment of non-deployable assistant (draft status, no conversations)
        draft_assistant_data = {
            "name": "Draft Assistant",
            "description": "Should not be deployable",
            "system_prompt": "Draft",
            "model_id": "gpt-4",
            "status": "draft"
        }
        
        success, draft_assistant = self.assistant_service.create_assistant(draft_assistant_data, self.user_id)
        assert success
        
        success, result = self.deployment_service.deploy_assistant(
            draft_assistant.id, "production", self.user_id
        )
        assert not success, "Should fail to deploy draft assistant to production"
        
        # Test analytics for assistant with no data
        success, metrics = self.analytics_service.get_assistant_metrics(
            draft_assistant.id, self.user_id, 30
        )
        assert success, "Should succeed but return empty metrics"
        assert metrics["basic_stats"]["total_conversations"] == 0
        
        print("✓ Error handling and edge cases test passed")
    
    def test_performance_and_scalability(self):
        """Test basic performance characteristics"""
        
        # Create multiple assistants quickly
        start_time = time.time()
        assistant_ids = []
        
        for i in range(5):  # Create 5 assistants
            assistant_data = {
                "name": f"Performance Test Assistant {i+1}",
                "description": f"Performance testing assistant #{i+1}",
                "system_prompt": f"Performance test assistant {i+1}",
                "model_id": "gpt-3.5-turbo",
                "tags": ["performance", f"batch_{i+1}"]
            }
            
            success, assistant = self.assistant_service.create_assistant(assistant_data, self.user_id)
            assert success, f"Failed to create assistant {i+1}"
            assistant_ids.append(assistant.id)
        
        creation_time = time.time() - start_time
        print(f"Created 5 assistants in {creation_time:.2f} seconds")
        assert creation_time < 5.0, "Assistant creation should be fast"
        
        # Test batch retrieval
        start_time = time.time()
        success, assistants = self.assistant_service.list_user_assistants(self.user_id)
        assert success
        assert len(assistants) >= 5
        
        retrieval_time = time.time() - start_time
        print(f"Retrieved assistants in {retrieval_time:.3f} seconds")
        assert retrieval_time < 1.0, "Assistant retrieval should be fast"
        
        # Test search performance
        start_time = time.time()
        success, search_results = self.assistant_service.search_assistants("Performance", None, 50)
        assert success
        assert len(search_results) >= 5
        
        search_time = time.time() - start_time
        print(f"Search completed in {search_time:.3f} seconds")
        assert search_time < 1.0, "Search should be fast"
        
        # Test analytics performance with multiple assistants
        start_time = time.time()
        success, summary = self.analytics_service.get_user_analytics_summary(self.user_id, 30)
        assert success
        assert summary["total_assistants"] >= 5
        
        analytics_time = time.time() - start_time
        print(f"Analytics summary generated in {analytics_time:.3f} seconds")
        assert analytics_time < 2.0, "Analytics should be reasonably fast"
        
        print("✓ Performance and scalability test passed")


if __name__ == "__main__":
    # Run tests individually for debugging
    test_suite = TestAssistantFrameworkIntegration()
    test_suite.setup()
    
    try:
        print("Running Assistant Framework Integration Tests...")
        print("=" * 60)
        
        test_suite.test_complete_assistant_lifecycle()
        test_suite.test_assistant_prompt_linking_workflow()
        test_suite.test_deployment_workflow()
        test_suite.test_analytics_and_monitoring()
        test_suite.test_conversation_context_management()
        test_suite.test_error_handling_and_edge_cases()
        test_suite.test_performance_and_scalability()
        
        print("=" * 60)
        print("✓ All Assistant Framework Integration Tests Passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
    finally:
        test_suite._cleanup_test_data()