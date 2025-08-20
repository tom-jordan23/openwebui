#!/usr/bin/env python3
"""
Assistant Framework Validation Script
Comprehensive validation of the AI Assistant Framework functionality
"""

import os
import sys
import time
import json
import uuid
import asyncio
from typing import Dict, List, Any, Tuple
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from database.connection import get_db_connection
    from database.assistant_repositories import (
        AssistantRepository, AssistantDeploymentRepository,
        ConversationContextRepository, AssistantAnalyticsRepository
    )
    from database.assistant_models import (
        AssistantProfile, AssistantDeployment, ConversationContext,
        AssistantStatus, AssistantType, DeploymentEnvironment
    )
    from api.assistant_management import AssistantService
    from api.assistant_prompt_linking import AssistantPromptService
    from api.conversation_management import ConversationService
    from api.assistant_deployment import DeploymentService
    from api.assistant_analytics import AnalyticsService
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


class AssistantFrameworkValidator:
    """Comprehensive validator for the Assistant Framework"""
    
    def __init__(self):
        self.db = None
        self.test_user_id = "validator_test_user"
        self.test_assistants = []
        self.validation_results = []
        
        # Initialize repositories
        self.assistant_repo = None
        self.deployment_repo = None
        self.context_repo = None
        self.analytics_repo = None
        
        # Initialize services
        self.assistant_service = None
        self.prompt_service = None
        self.conversation_service = None
        self.deployment_service = None
        self.analytics_service = None
    
    def setup(self) -> bool:
        """Setup database connection and services"""
        try:
            print("🔧 Setting up Assistant Framework Validator...")
            
            # Initialize database connection
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
            
            print("✅ Setup completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up test data"""
        try:
            print("🧹 Cleaning up test data...")
            with self.db.get_transaction() as cursor:
                # Clean up in proper order (foreign key constraints)
                cursor.execute("DELETE FROM assistant_analytics WHERE assistant_id LIKE 'val_test_%'")
                cursor.execute("DELETE FROM conversation_context WHERE assistant_id LIKE 'val_test_%'")
                cursor.execute("DELETE FROM assistant_deployment WHERE assistant_id LIKE 'val_test_%'")
                cursor.execute("DELETE FROM assistant_prompt_mapping WHERE assistant_id LIKE 'val_test_%'")
                cursor.execute("DELETE FROM ai_assistant WHERE id LIKE 'val_test_%' OR user_id = %s", (self.test_user_id,))
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    def validate_database_schema(self) -> bool:
        """Validate that all required database tables and columns exist"""
        print("\n📊 Validating Database Schema...")
        
        required_tables = {
            'ai_assistant': [
                'id', 'name', 'description', 'system_prompt', 'model_id', 'user_id',
                'assistant_type', 'status', 'version', 'primary_prompt_id', 'temperature',
                'max_tokens', 'total_conversations', 'user_satisfaction_rating'
            ],
            'assistant_deployment': [
                'id', 'assistant_id', 'environment', 'version', 'status', 'deployed_at', 'deployed_by'
            ],
            'conversation_context': [
                'id', 'session_id', 'assistant_id', 'user_id', 'conversation_history',
                'max_context_length', 'interaction_count'
            ],
            'assistant_prompt_mapping': [
                'assistant_id', 'prompt_id', 'mapping_type', 'priority'
            ],
            'assistant_analytics': [
                'id', 'assistant_id', 'metric_name', 'metric_value', 'recorded_at'
            ]
        }
        
        try:
            with self.db.get_cursor() as cursor:
                for table_name, columns in required_tables.items():
                    # Check if table exists
                    cursor.execute("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'public' AND table_name = %s
                    """, (table_name,))
                    
                    if not cursor.fetchone():
                        print(f"❌ Table '{table_name}' not found")
                        return False
                    
                    # Check if required columns exist
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = %s
                    """, (table_name,))
                    
                    existing_columns = {row['column_name'] for row in cursor.fetchall()}
                    missing_columns = set(columns) - existing_columns
                    
                    if missing_columns:
                        print(f"❌ Table '{table_name}' missing columns: {missing_columns}")
                        return False
                    
                    print(f"✅ Table '{table_name}' schema valid")
            
            print("✅ Database schema validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Database schema validation failed: {e}")
            return False
    
    def validate_assistant_crud_operations(self) -> bool:
        """Validate basic CRUD operations for assistants"""
        print("\n🤖 Validating Assistant CRUD Operations...")
        
        try:
            # Create assistant
            assistant_data = {
                "name": "Validation Test Assistant",
                "description": "Testing CRUD operations",
                "system_prompt": "You are a validation test assistant.",
                "model_id": "gpt-4",
                "assistant_type": "general",
                "temperature": 0.7,
                "max_tokens": 2000,
                "tags": ["validation", "test"]
            }
            
            success, result = self.assistant_service.create_assistant(assistant_data, self.test_user_id)
            if not success:
                print(f"❌ Create operation failed: {result}")
                return False
            
            assistant = result
            assistant_id = assistant.id
            self.test_assistants.append(assistant_id)
            print(f"✅ Create: Assistant created with ID {assistant_id}")
            
            # Read assistant
            success, retrieved_assistant = self.assistant_service.get_assistant(assistant_id, self.test_user_id)
            if not success:
                print(f"❌ Read operation failed: {retrieved_assistant}")
                return False
            
            if retrieved_assistant.name != assistant_data["name"]:
                print("❌ Read operation: Data mismatch")
                return False
            print("✅ Read: Assistant retrieved successfully")
            
            # Update assistant
            update_data = {
                "description": "Updated description for validation",
                "status": "active",
                "version": "1.1.0"
            }
            
            success, message = self.assistant_service.update_assistant(assistant_id, self.test_user_id, update_data)
            if not success:
                print(f"❌ Update operation failed: {message}")
                return False
            
            # Verify update
            success, updated_assistant = self.assistant_service.get_assistant(assistant_id, self.test_user_id)
            if not success or updated_assistant.description != update_data["description"]:
                print("❌ Update operation: Verification failed")
                return False
            print("✅ Update: Assistant updated successfully")
            
            # List assistants
            success, assistants = self.assistant_service.list_user_assistants(self.test_user_id)
            if not success or len(assistants) == 0:
                print(f"❌ List operation failed: {assistants}")
                return False
            print(f"✅ List: Found {len(assistants)} assistants")
            
            # Search assistants
            success, search_results = self.assistant_service.search_assistants("Validation", None, 10)
            if not success:
                print(f"❌ Search operation failed: {search_results}")
                return False
            print(f"✅ Search: Found {len(search_results)} matching assistants")
            
            print("✅ Assistant CRUD operations validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Assistant CRUD validation failed: {e}")
            return False
    
    def validate_conversation_management(self) -> bool:
        """Validate conversation management functionality"""
        print("\n💬 Validating Conversation Management...")
        
        try:
            if not self.test_assistants:
                print("❌ No test assistants available")
                return False
            
            assistant_id = self.test_assistants[0]
            
            # Start conversation
            success, conversation = self.conversation_service.start_conversation(
                assistant_id, self.test_user_id, "Hello, this is a validation test"
            )
            if not success:
                print(f"❌ Start conversation failed: {conversation}")
                return False
            
            session_id = conversation.session_id
            print(f"✅ Conversation started with session ID: {session_id}")
            
            # Add messages
            test_messages = [
                ("user", "How are you doing today?"),
                ("assistant", "I'm functioning well, thank you for asking!"),
                ("user", "Can you help me with a validation test?"),
                ("assistant", "Absolutely! I'd be happy to help with your validation test.")
            ]
            
            for role, content in test_messages:
                success, updated_conversation = self.conversation_service.add_message(
                    session_id, self.test_user_id, role, content,
                    {"validation": True}, 1.2 if role == "assistant" else None, 
                    150 if role == "assistant" else 0
                )
                if not success:
                    print(f"❌ Add message failed: {updated_conversation}")
                    return False
            
            print(f"✅ Added {len(test_messages)} messages successfully")
            
            # Get conversation history
            success, history = self.conversation_service.get_conversation_history(session_id, self.test_user_id)
            if not success or len(history) < len(test_messages):
                print(f"❌ Get history failed: {history}")
                return False
            print(f"✅ Retrieved conversation history with {len(history)} messages")
            
            # Update context variables
            success, message = self.conversation_service.update_context_variables(
                session_id, self.test_user_id, {"test_mode": True, "validation_run": "active"}
            )
            if not success:
                print(f"❌ Update context failed: {message}")
                return False
            print("✅ Context variables updated")
            
            # Get conversation summary
            success, summary = self.conversation_service.get_conversation_summary(session_id, self.test_user_id)
            if not success:
                print(f"❌ Get summary failed: {summary}")
                return False
            print(f"✅ Conversation summary: {summary['statistics']['total_messages']} messages")
            
            # End conversation
            success, message = self.conversation_service.end_conversation(session_id, self.test_user_id, 5)
            if not success:
                print(f"❌ End conversation failed: {message}")
                return False
            print("✅ Conversation ended successfully")
            
            print("✅ Conversation management validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Conversation management validation failed: {e}")
            return False
    
    def validate_deployment_system(self) -> bool:
        """Validate deployment and lifecycle management"""
        print("\n🚀 Validating Deployment System...")
        
        try:
            if not self.test_assistants:
                print("❌ No test assistants available")
                return False
            
            assistant_id = self.test_assistants[0]
            
            # First, make assistant deployable
            update_data = {
                "status": "active"
            }
            success, message = self.assistant_service.update_assistant(assistant_id, self.test_user_id, update_data)
            if not success:
                print(f"❌ Failed to prepare assistant for deployment: {message}")
                return False
            
            # Update stats to make it deployable to production
            with self.db.get_transaction() as cursor:
                cursor.execute("""
                    UPDATE ai_assistant 
                    SET total_conversations = 15, user_satisfaction_rating = 4.2
                    WHERE id = %s
                """, (assistant_id,))
            
            # Deploy to development
            success, deployment = self.deployment_service.deploy_assistant(
                assistant_id, "development", self.test_user_id, {"resources": {"cpu": "0.5", "memory": "512Mi"}}
            )
            if not success:
                print(f"❌ Development deployment failed: {deployment}")
                return False
            print("✅ Deployed to development environment")
            
            # Deploy to testing
            success, test_deployment = self.deployment_service.deploy_assistant(
                assistant_id, "testing", self.test_user_id
            )
            if not success:
                print(f"❌ Testing deployment failed: {test_deployment}")
                return False
            print("✅ Deployed to testing environment")
            
            # Get deployment history
            success, history = self.deployment_service.get_deployment_history(assistant_id, self.test_user_id)
            if not success or len(history) < 2:
                print(f"❌ Get deployment history failed: {history}")
                return False
            print(f"✅ Retrieved deployment history: {len(history)} deployments")
            
            # Get deployment status
            success, status = self.deployment_service.get_deployment_status(assistant_id, self.test_user_id)
            if not success:
                print(f"❌ Get deployment status failed: {status}")
                return False
            print("✅ Retrieved deployment status")
            
            # Test promotion
            success, message = self.deployment_service.promote_assistant(
                assistant_id, "testing", "staging", self.test_user_id
            )
            if not success:
                print(f"❌ Promotion failed: {message}")
                return False
            print("✅ Promoted from testing to staging")
            
            print("✅ Deployment system validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Deployment system validation failed: {e}")
            return False
    
    def validate_analytics_system(self) -> bool:
        """Validate analytics and monitoring functionality"""
        print("\n📈 Validating Analytics System...")
        
        try:
            if not self.test_assistants:
                print("❌ No test assistants available")
                return False
            
            assistant_id = self.test_assistants[0]
            
            # Record test metrics
            test_metrics = [
                ("response_time", 1.2, "interaction", {"test": True}),
                ("response_time", 0.8, "interaction", {"test": True}),
                ("response_time", 1.5, "interaction", {"test": True}),
                ("user_satisfaction", 4.0, "conversation", {"test": True}),
                ("user_satisfaction", 5.0, "conversation", {"test": True}),
                ("tokens_used", 150, "interaction", {"test": True}),
                ("tokens_used", 200, "interaction", {"test": True}),
                ("conversation_length", 5, "session", {"test": True}),
                ("conversation_length", 8, "session", {"test": True})
            ]
            
            for metric_name, value, time_period, metadata in test_metrics:
                success = self.analytics_repo.record_metric(
                    assistant_id, metric_name, value, time_period, metadata
                )
                if not success:
                    print(f"❌ Failed to record metric: {metric_name}")
                    return False
            
            print(f"✅ Recorded {len(test_metrics)} test metrics")
            
            # Get comprehensive metrics
            success, metrics = self.analytics_service.get_assistant_metrics(assistant_id, self.test_user_id, 30)
            if not success:
                print(f"❌ Get metrics failed: {metrics}")
                return False
            
            required_keys = ["assistant_id", "basic_stats", "detailed_metrics", "trends"]
            for key in required_keys:
                if key not in metrics:
                    print(f"❌ Missing key in metrics: {key}")
                    return False
            
            print("✅ Retrieved comprehensive metrics")
            
            # Get usage analytics
            success, usage = self.analytics_service.get_usage_analytics(
                assistant_id, self.test_user_id, "daily", 7
            )
            if not success:
                print(f"❌ Get usage analytics failed: {usage}")
                return False
            print("✅ Retrieved usage analytics")
            
            # Get health status
            success, health = self.analytics_service.get_health_status(assistant_id, self.test_user_id)
            if not success:
                print(f"❌ Get health status failed: {health}")
                return False
            
            required_health_keys = ["health_score", "health_grade", "alerts", "recommendations"]
            for key in required_health_keys:
                if key not in health:
                    print(f"❌ Missing key in health status: {key}")
                    return False
            
            print(f"✅ Health status: Score {health['health_score']}, Grade {health['health_grade']}")
            
            # Update usage statistics
            success, message = self.assistant_service.update_usage_stats(
                assistant_id, self.test_user_id, 3, 1.1, 4
            )
            if not success:
                print(f"❌ Update usage stats failed: {message}")
                return False
            print("✅ Updated usage statistics")
            
            # Get user analytics summary
            success, summary = self.analytics_service.get_user_analytics_summary(self.test_user_id, 30)
            if not success:
                print(f"❌ Get user summary failed: {summary}")
                return False
            
            if summary["total_assistants"] == 0:
                print("❌ User summary shows no assistants")
                return False
            
            print(f"✅ User summary: {summary['total_assistants']} assistants")
            
            print("✅ Analytics system validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Analytics system validation failed: {e}")
            return False
    
    def validate_performance_benchmarks(self) -> bool:
        """Validate performance benchmarks"""
        print("\n⚡ Validating Performance Benchmarks...")
        
        try:
            # Test assistant creation performance
            start_time = time.time()
            
            assistant_data = {
                "name": "Performance Test Assistant",
                "description": "Testing performance",
                "system_prompt": "Performance test",
                "model_id": "gpt-3.5-turbo"
            }
            
            success, assistant = self.assistant_service.create_assistant(assistant_data, self.test_user_id)
            if not success:
                print(f"❌ Performance test assistant creation failed: {assistant}")
                return False
            
            creation_time = time.time() - start_time
            print(f"✅ Assistant creation: {creation_time:.3f}s")
            
            if creation_time > 1.0:
                print("⚠️ Warning: Assistant creation took longer than expected")
            
            assistant_id = assistant.id
            self.test_assistants.append(assistant_id)
            
            # Test retrieval performance
            start_time = time.time()
            success, retrieved = self.assistant_service.get_assistant(assistant_id, self.test_user_id)
            retrieval_time = time.time() - start_time
            
            if not success:
                print(f"❌ Performance test retrieval failed: {retrieved}")
                return False
            
            print(f"✅ Assistant retrieval: {retrieval_time:.3f}s")
            
            if retrieval_time > 0.5:
                print("⚠️ Warning: Assistant retrieval took longer than expected")
            
            # Test search performance
            start_time = time.time()
            success, results = self.assistant_service.search_assistants("Performance", None, 10)
            search_time = time.time() - start_time
            
            if not success:
                print(f"❌ Performance test search failed: {results}")
                return False
            
            print(f"✅ Assistant search: {search_time:.3f}s")
            
            if search_time > 1.0:
                print("⚠️ Warning: Assistant search took longer than expected")
            
            # Test conversation start performance
            start_time = time.time()
            success, conversation = self.conversation_service.start_conversation(
                assistant_id, self.test_user_id, "Performance test message"
            )
            conversation_start_time = time.time() - start_time
            
            if not success:
                print(f"❌ Performance test conversation start failed: {conversation}")
                return False
            
            print(f"✅ Conversation start: {conversation_start_time:.3f}s")
            
            if conversation_start_time > 1.0:
                print("⚠️ Warning: Conversation start took longer than expected")
            
            # Test analytics performance
            start_time = time.time()
            success, summary = self.analytics_service.get_user_analytics_summary(self.test_user_id, 30)
            analytics_time = time.time() - start_time
            
            if not success:
                print(f"❌ Performance test analytics failed: {summary}")
                return False
            
            print(f"✅ Analytics summary: {analytics_time:.3f}s")
            
            if analytics_time > 2.0:
                print("⚠️ Warning: Analytics took longer than expected")
            
            print("✅ Performance benchmarks validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Performance validation failed: {e}")
            return False
    
    def run_comprehensive_validation(self) -> bool:
        """Run all validation tests"""
        print("🎯 Starting Comprehensive Assistant Framework Validation")
        print("=" * 70)
        
        validation_steps = [
            ("Database Schema", self.validate_database_schema),
            ("Assistant CRUD Operations", self.validate_assistant_crud_operations),
            ("Conversation Management", self.validate_conversation_management),
            ("Deployment System", self.validate_deployment_system),
            ("Analytics System", self.validate_analytics_system),
            ("Performance Benchmarks", self.validate_performance_benchmarks),
        ]
        
        passed_tests = 0
        total_tests = len(validation_steps)
        
        for test_name, test_function in validation_steps:
            try:
                if test_function():
                    passed_tests += 1
                    self.validation_results.append((test_name, True, None))
                else:
                    self.validation_results.append((test_name, False, "Test returned False"))
            except Exception as e:
                print(f"❌ {test_name} validation threw exception: {e}")
                self.validation_results.append((test_name, False, str(e)))
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 VALIDATION SUMMARY")
        print("=" * 70)
        
        for test_name, passed, error in self.validation_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {test_name}")
            if error:
                print(f"    Error: {error}")
        
        print(f"\nTests passed: {passed_tests}/{total_tests}")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL VALIDATIONS PASSED! Assistant Framework is ready for use.")
            return True
        else:
            print(f"\n⚠️ {total_tests - passed_tests} validation(s) failed. Please review and fix issues.")
            return False
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate a detailed validation report"""
        return {
            "timestamp": time.time(),
            "total_tests": len(self.validation_results),
            "passed_tests": sum(1 for _, passed, _ in self.validation_results if passed),
            "failed_tests": sum(1 for _, passed, _ in self.validation_results if not passed),
            "test_results": [
                {
                    "test_name": name,
                    "passed": passed,
                    "error": error
                }
                for name, passed, error in self.validation_results
            ],
            "test_assistants_created": len(self.test_assistants)
        }


def main():
    """Main validation function"""
    validator = AssistantFrameworkValidator()
    
    # Setup
    if not validator.setup():
        print("❌ Setup failed. Exiting.")
        return False
    
    try:
        # Run validation
        success = validator.run_comprehensive_validation()
        
        # Generate report
        report = validator.generate_validation_report()
        
        # Save report
        report_file = Path(__file__).parent / "validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return success
        
    finally:
        # Cleanup
        validator.cleanup()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)