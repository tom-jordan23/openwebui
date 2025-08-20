"""
Database connection management for AI Assistant Platform
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '5432'))
        self.database = os.getenv('DB_NAME', 'openwebui')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'postgres')
        self.min_connections = int(os.getenv('DB_MIN_CONNECTIONS', '1'))
        self.max_connections = int(os.getenv('DB_MAX_CONNECTIONS', '10'))
    
    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def get_connection_params(self) -> Dict[str, Any]:
        """Get connection parameters for psycopg2"""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password,
            'cursor_factory': RealDictCursor
        }


class DatabaseConnection:
    """Database connection manager"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._connection = None
    
    def connect(self) -> psycopg2.extensions.connection:
        """Establish database connection"""
        try:
            self._connection = psycopg2.connect(**self.config.get_connection_params())
            self._connection.autocommit = False
            logger.info("Database connection established")
            return self._connection
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("Database connection closed")
    
    @property
    def connection(self) -> psycopg2.extensions.connection:
        """Get current connection, create if needed"""
        if not self._connection or self._connection.closed:
            self.connect()
        return self._connection
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    @contextmanager
    def get_cursor(self):
        """Get database cursor with automatic cleanup"""
        cursor = None
        try:
            cursor = self.connection.cursor()
            yield cursor
        except Exception as e:
            if self._connection:
                self._connection.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    @contextmanager
    def get_transaction(self):
        """Get database transaction with automatic commit/rollback"""
        cursor = None
        try:
            cursor = self.connection.cursor()
            yield cursor
            self._connection.commit()
        except Exception as e:
            if self._connection:
                self._connection.rollback()
            logger.error(f"Transaction failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()


# Global database connection instance
_db_connection = None

def get_db_connection() -> DatabaseConnection:
    """Get global database connection instance"""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


def init_database():
    """Initialize database connection and test connectivity"""
    db = get_db_connection()
    if not db.test_connection():
        raise RuntimeError("Database connection test failed")
    logger.info("Database initialized successfully")


def cleanup_database():
    """Cleanup database connections"""
    global _db_connection
    if _db_connection:
        _db_connection.disconnect()
        _db_connection = None