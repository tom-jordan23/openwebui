"""
Unit tests for individual service components
"""
import pytest
import requests
import psycopg2
import redis
import json


class TestServiceHealth:
    """Test individual service health and basic functionality"""

    def test_openwebui_health(self, openwebui_url):
        """Test OpenWebUI health endpoint"""
        response = requests.get(f"{openwebui_url}/health", timeout=5)
        assert response.status_code == 200
        assert response.json()["status"] is True

    def test_openwebui_config(self, openwebui_url):
        """Test OpenWebUI configuration endpoint"""
        response = requests.get(f"{openwebui_url}/api/config", timeout=5)
        assert response.status_code == 200
        config = response.json()
        assert "status" in config
        assert "name" in config
        assert config["status"] is True

    def test_ollama_api_connection(self, ollama_url):
        """Test Ollama API connectivity"""
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        assert response.status_code == 200
        models = response.json()
        assert "models" in models
        assert isinstance(models["models"], list)

    def test_ollama_model_availability(self, ollama_url, test_model):
        """Test that the test model is available"""
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        assert response.status_code == 200
        models = response.json()["models"]
        model_names = [model["name"] for model in models]
        assert test_model["name"] in model_names

    def test_postgres_connection(self, postgres_connection):
        """Test PostgreSQL database connection"""
        try:
            conn = psycopg2.connect(
                host=postgres_connection["host"],
                port=postgres_connection["port"],
                database=postgres_connection["database"],
                user=postgres_connection["username"],
                password=postgres_connection["password"],
                connect_timeout=5
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            cursor.close()
            conn.close()
        except psycopg2.Error as e:
            pytest.fail(f"PostgreSQL connection failed: {e}")

    def test_redis_connection(self, redis_connection):
        """Test Redis connection"""
        try:
            r = redis.Redis(
                host=redis_connection["host"],
                port=redis_connection["port"],
                db=redis_connection["db"],
                socket_timeout=5
            )
            response = r.ping()
            assert response is True
        except redis.RedisError as e:
            pytest.fail(f"Redis connection failed: {e}")

    def test_qdrant_connection(self):
        """Test Qdrant vector database connection"""
        response = requests.get("http://localhost:6333/collections", timeout=5)
        assert response.status_code == 200
        collections = response.json()
        assert "result" in collections
        assert "status" in collections
        assert collections["status"] == "ok"

    def test_neo4j_browser_access(self):
        """Test Neo4j browser accessibility"""
        response = requests.get("http://localhost:7474/browser/", timeout=10)
        assert response.status_code == 200
        assert "Neo4j Browser" in response.text


class TestModelInference:
    """Test model inference capabilities"""

    def test_basic_model_inference(self, ollama_url, test_model):
        """Test basic model inference"""
        payload = {
            "model": test_model["name"],
            "prompt": "What is 2+2?",
            "stream": False
        }
        
        response = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            timeout=test_model["timeout"]
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "response" in result
        assert len(result["response"]) > 0
        assert "done" in result
        assert result["done"] is True

    def test_model_inference_performance(self, ollama_url, test_model):
        """Test model inference performance"""
        import time
        
        payload = {
            "model": test_model["name"],
            "prompt": "Hello",
            "stream": False
        }
        
        start_time = time.time()
        response = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            timeout=test_model["timeout"]
        )
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # Performance assertion - should respond within reasonable time
        assert response_time < test_model["timeout"]
        print(f"Model inference time: {response_time:.2f}s")

    def test_model_error_handling(self, ollama_url):
        """Test model error handling with invalid model"""
        payload = {
            "model": "nonexistent-model",
            "prompt": "Test",
            "stream": False
        }
        
        response = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            timeout=10
        )
        
        # Should return an error status
        assert response.status_code != 200 or "error" in response.json()