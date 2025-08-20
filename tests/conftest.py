"""
Test configuration and fixtures for the AI Assistant Platform
"""
import pytest
import requests
import time
from typing import Generator


@pytest.fixture(scope="session")
def docker_services():
    """Ensure Docker services are running before tests"""
    services = [
        ("http://localhost:3000/health", "OpenWebUI"),
        ("http://localhost:11434/api/tags", "Ollama"),
        ("http://localhost:5432", "PostgreSQL"),  # Connection test handled separately
        ("http://localhost:6379", "Redis"),  # Connection test handled separately
        ("http://localhost:6333/collections", "Qdrant"),
        ("http://localhost:7474", "Neo4j"),
    ]
    
    # Wait for services to be ready
    for url, service_name in services:
        if not service_name in ["PostgreSQL", "Redis"]:  # Skip connection-based services
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        print(f"✅ {service_name} is ready")
                        break
                except requests.exceptions.RequestException:
                    if attempt == max_attempts - 1:
                        pytest.fail(f"❌ {service_name} failed to start after {max_attempts} attempts")
                    time.sleep(1)


@pytest.fixture
def openwebui_url():
    """OpenWebUI base URL"""
    return "http://localhost:3000"


@pytest.fixture
def ollama_url():
    """Ollama API base URL"""
    return "http://localhost:11434"


@pytest.fixture
def postgres_connection():
    """PostgreSQL connection details"""
    return {
        "host": "localhost",
        "port": 5432,
        "database": "openwebui",
        "username": "postgres",
        "password": "postgres"
    }


@pytest.fixture
def redis_connection():
    """Redis connection details"""
    return {
        "host": "localhost",
        "port": 6379,
        "db": 0
    }


@pytest.fixture
def test_model():
    """Test model configuration"""
    return {
        "name": "llama3.2:1b",
        "timeout": 60  # seconds - increased for slower 1B model
    }