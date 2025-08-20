"""
Database schema validation and performance tests
"""
import pytest
import time
from src.database.connection import get_db_connection


class TestSchemaValidation:
    """Test database schema is correctly implemented"""
    
    def test_tables_exist(self, postgres_connection):
        """Test that all expected tables exist"""
        db = get_db_connection()
        expected_tables = [
            'prompt_version',
            'prompt_category',
            'prompt_category_mapping',
            'ai_assistant',
            'assistant_capability',
            'assistant_capability_mapping',
            'conversation_session',
            'evaluation_metric',
            'performance_measurement',
            'knowledge_source',
            'knowledge_entity',
            'knowledge_relationship',
            'experiment',
            'experiment_variant',
            'experiment_assignment'
        ]
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            actual_tables = [row['table_name'] for row in cursor.fetchall()]
            
            for table in expected_tables:
                assert table in actual_tables, f"Table {table} not found"
    
    def test_views_exist(self, postgres_connection):
        """Test that all expected views exist"""
        db = get_db_connection()
        expected_views = [
            'active_assistants',
            'latest_prompt_versions',
            'knowledge_entity_summary',
            'performance_summary'
        ]
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = 'public'
            """)
            actual_views = [row['table_name'] for row in cursor.fetchall()]
            
            for view in expected_views:
                assert view in actual_views, f"View {view} not found"
    
    def test_foreign_key_constraints(self, postgres_connection):
        """Test that foreign key constraints are properly set up"""
        db = get_db_connection()
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    tc.table_name, 
                    tc.constraint_name, 
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_schema = 'public'
                AND tc.table_name LIKE '%prompt%' OR tc.table_name LIKE '%ai_assistant%'
            """)
            
            fk_constraints = cursor.fetchall()
            
            # Should have foreign key constraints
            assert len(fk_constraints) > 0, "No foreign key constraints found"
            
            # Check specific constraints exist
            constraint_tables = [fk['table_name'] for fk in fk_constraints]
            assert 'prompt_version' in constraint_tables
            assert 'ai_assistant' in constraint_tables
    
    def test_indexes_exist(self, postgres_connection):
        """Test that performance indexes exist"""
        db = get_db_connection()
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND indexname LIKE 'idx_%'
            """)
            indexes = [row['indexname'] for row in cursor.fetchall()]
            
            # Check for some key performance indexes
            expected_indexes = [
                'idx_prompt_version_prompt_id',
                'idx_ai_assistant_user',
                'idx_ai_assistant_active',
                'idx_conversation_session_chat'
            ]
            
            for index in expected_indexes:
                assert index in indexes, f"Index {index} not found"


class TestPerformanceValidation:
    """Test database performance meets requirements"""
    
    def test_simple_query_performance(self, postgres_connection):
        """Test that simple queries respond within 100ms"""
        db = get_db_connection()
        
        queries = [
            "SELECT COUNT(*) FROM prompt",
            "SELECT COUNT(*) FROM ai_assistant",
            "SELECT COUNT(*) FROM conversation_session",
            "SELECT * FROM active_assistants LIMIT 10"
        ]
        
        for query in queries:
            start_time = time.time()
            
            with db.get_cursor() as cursor:
                cursor.execute(query)
                cursor.fetchall()
            
            end_time = time.time()
            query_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            assert query_time < 100, f"Query '{query}' took {query_time:.2f}ms (should be < 100ms)"
    
    def test_complex_query_performance(self, postgres_connection):
        """Test that complex queries with joins respond within 500ms"""
        db = get_db_connection()
        
        complex_queries = [
            """
            SELECT a.*, u.name as creator_name, COUNT(cs.id) as session_count
            FROM ai_assistant a
            JOIN "user" u ON a.user_id = u.id
            LEFT JOIN conversation_session cs ON a.id = cs.assistant_id
            WHERE a.is_active = TRUE
            GROUP BY a.id, u.name
            LIMIT 50
            """,
            """
            SELECT p.title, pv.version_number, pv.title as version_title
            FROM prompt p
            JOIN prompt_version pv ON p.id = pv.prompt_id
            WHERE pv.is_active = TRUE
            ORDER BY p.id
            LIMIT 100
            """
        ]
        
        for query in complex_queries:
            start_time = time.time()
            
            with db.get_cursor() as cursor:
                cursor.execute(query)
                cursor.fetchall()
            
            end_time = time.time()
            query_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            assert query_time < 500, f"Complex query took {query_time:.2f}ms (should be < 500ms)"
    
    def test_insert_performance(self, postgres_connection):
        """Test that inserts complete within reasonable time"""
        db = get_db_connection()
        
        # Test batch insert performance
        start_time = time.time()
        
        with db.get_transaction() as cursor:
            # Insert test categories
            for i in range(10):
                cursor.execute("""
                    INSERT INTO prompt_category (name, description, created_at, created_by)
                    VALUES (%s, %s, %s, %s)
                """, (f"test_category_{i}", f"Test category {i}", int(time.time() * 1000), "test_user"))
        
        end_time = time.time()
        insert_time = (end_time - start_time) * 1000
        
        # Should complete batch insert in under 200ms
        assert insert_time < 200, f"Batch insert took {insert_time:.2f}ms (should be < 200ms)"
        
        # Clean up test data
        with db.get_transaction() as cursor:
            cursor.execute("DELETE FROM prompt_category WHERE name LIKE 'test_category_%'")
    
    def test_concurrent_read_performance(self, postgres_connection):
        """Test that concurrent reads don't significantly degrade performance"""
        db = get_db_connection()
        
        # Single read baseline
        start_time = time.time()
        with db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM active_assistants LIMIT 10")
            cursor.fetchall()
        baseline_time = time.time() - start_time
        
        # Multiple concurrent reads (simulated with sequential for simplicity)
        start_time = time.time()
        for _ in range(5):
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM active_assistants LIMIT 10")
                cursor.fetchall()
        concurrent_time = (time.time() - start_time) / 5  # Average per query
        
        # Concurrent queries shouldn't be more than 3x slower than baseline
        performance_ratio = concurrent_time / baseline_time if baseline_time > 0 else 1
        assert performance_ratio < 3, f"Concurrent performance degraded by {performance_ratio:.2f}x"
    
    def test_database_constraints_integrity(self, postgres_connection):
        """Test that database constraints maintain data integrity"""
        db = get_db_connection()
        
        # Test foreign key constraint
        with pytest.raises(Exception):  # Should fail due to foreign key constraint
            with db.get_transaction() as cursor:
                cursor.execute("""
                    INSERT INTO prompt_version (prompt_id, version_number, title, content, created_by, created_at, is_active)
                    VALUES (99999, 1, 'Test', 'Test content', 'test_user', %s, false)
                """, (int(time.time() * 1000),))
        
        # Test unique constraint
        with db.get_transaction() as cursor:
            # First insert should succeed
            cursor.execute("""
                INSERT INTO prompt_category (name, description, created_at, created_by)
                VALUES ('unique_test_category', 'Test', %s, 'test_user')
            """, (int(time.time() * 1000),))
        
        # Second insert with same name should fail
        with pytest.raises(Exception):  # Should fail due to unique constraint
            with db.get_transaction() as cursor:
                cursor.execute("""
                    INSERT INTO prompt_category (name, description, created_at, created_by)
                    VALUES ('unique_test_category', 'Test', %s, 'test_user')
                """, (int(time.time() * 1000),))
        
        # Clean up
        with db.get_transaction() as cursor:
            cursor.execute("DELETE FROM prompt_category WHERE name = 'unique_test_category'")