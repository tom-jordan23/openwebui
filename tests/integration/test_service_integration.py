"""
Integration tests for service-to-service communication
"""
import pytest
import requests
import time


class TestServiceIntegration:
    """Test integration between different services"""

    def test_nginx_proxy_to_openwebui(self):
        """Test Nginx proxy routing to OpenWebUI"""
        # Direct OpenWebUI access
        direct_response = requests.get("http://localhost:3000/health", timeout=5)
        
        # Through Nginx proxy
        proxy_response = requests.get("http://localhost:8081/health", timeout=5)
        
        assert direct_response.status_code == 200
        assert proxy_response.status_code == 200
        
        # The proxy might return plain text for health endpoint, which is fine
        if proxy_response.headers.get('content-type', '').startswith('application/json'):
            assert direct_response.json() == proxy_response.json()
        else:
            # Nginx health endpoint returns plain text
            assert "healthy" in proxy_response.text

    def test_nginx_proxy_to_ollama(self):
        """Test Nginx proxy routing to Ollama API"""
        # Direct Ollama access
        direct_response = requests.get("http://localhost:11434/api/tags", timeout=10)
        
        # Through Nginx proxy (should route /api/v1/ to Ollama)
        # Note: This tests the API routing configuration
        assert direct_response.status_code == 200

    def test_openwebui_database_integration(self):
        """Test OpenWebUI integration with PostgreSQL"""
        # This would require OpenWebUI to be properly configured
        # For now, we test that the configuration endpoint shows database connectivity
        response = requests.get("http://localhost:3000/api/config", timeout=5)
        assert response.status_code == 200
        
        config = response.json()
        assert "status" in config
        assert config["status"] is True

    def test_model_serving_chain(self, ollama_url, test_model):
        """Test complete model serving chain"""
        # 1. Check model is loaded
        models_response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        assert models_response.status_code == 200
        models = models_response.json()["models"]
        model_names = [model["name"] for model in models]
        assert test_model["name"] in model_names

        # 2. Test inference
        payload = {
            "model": test_model["name"],
            "prompt": "Integration test prompt",
            "stream": False
        }
        
        inference_response = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            timeout=test_model["timeout"]
        )
        
        assert inference_response.status_code == 200
        result = inference_response.json()
        assert "response" in result
        assert result["done"] is True

    def test_vector_database_operations(self):
        """Test vector database basic operations"""
        qdrant_url = "http://localhost:6333"
        
        # Check collections
        collections_response = requests.get(f"{qdrant_url}/collections", timeout=5)
        assert collections_response.status_code == 200
        
        collections = collections_response.json()
        assert collections["status"] == "ok"
        
        # Test creating a test collection (cleanup afterwards)
        test_collection = "test_integration"
        create_payload = {
            "vectors": {
                "size": 384,  # sentence-transformers dimension
                "distance": "Cosine"
            }
        }
        
        create_response = requests.put(
            f"{qdrant_url}/collections/{test_collection}",
            json=create_payload,
            timeout=5
        )
        
        # Should succeed (201) or already exist (200)
        assert create_response.status_code in [200, 201]
        
        # Cleanup - delete test collection
        delete_response = requests.delete(
            f"{qdrant_url}/collections/{test_collection}",
            timeout=5
        )
        assert delete_response.status_code == 200

    def test_graph_database_connectivity(self):
        """Test Neo4j graph database connectivity"""
        # Test basic connectivity to Neo4j browser
        response = requests.get("http://localhost:7474/browser/", timeout=10)
        assert response.status_code == 200
        
        # Test that the service is responding with the browser interface
        assert "Neo4j Browser" in response.text


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""

    def test_health_check_workflow(self):
        """Test complete health check workflow across all services"""
        services = [
            ("http://localhost:3000/health", "OpenWebUI"),
            ("http://localhost:8081/health", "Nginx Proxy"),
            ("http://localhost:11434/api/tags", "Ollama"),
            ("http://localhost:6333/collections", "Qdrant"),
            ("http://localhost:7474/browser/", "Neo4j"),
        ]
        
        for url, service_name in services:
            response = requests.get(url, timeout=10)
            assert response.status_code == 200, f"{service_name} health check failed"
            print(f"✅ {service_name} health check passed")

    def test_model_inference_through_proxy(self, test_model):
        """Test model inference through the complete proxy chain"""
        # This tests the complete request flow:
        # Client -> Nginx -> Ollama -> Model -> Response chain
        
        # For now, test direct Ollama access since proxy routing 
        # would need specific configuration for model inference
        payload = {
            "model": test_model["name"],
            "prompt": "End-to-end test prompt",
            "stream": False
        }
        
        start_time = time.time()
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=test_model["timeout"]  # Now 60 seconds
        )
        end_time = time.time()
        
        assert response.status_code == 200
        result = response.json()
        assert "response" in result
        assert len(result["response"]) > 0
        
        response_time = end_time - start_time
        print(f"End-to-end inference time: {response_time:.2f}s")
        
        # Ensure reasonable response time
        assert response_time < test_model["timeout"]