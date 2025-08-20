# OpenWebUI AI Assistant Platform

A containerized personal AI assistant platform built on OpenWebUI and LightLLM, designed for prompt engineering, assistant development, and multi-model evaluation. The system supports both local and hosted AI models with advanced features including GraphRAG knowledge enhancement and MCP (Model Context Protocol) integration.

## 🚀 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd openwebui

# Start development environment
docker-compose up -d

# Access the application
open http://localhost:3000
```

### 🌐 Service Access Points

Once the platform is running, you can access all services through these URLs:

| Service | URL | Description |
|---------|-----|-------------|
| **OpenWebUI** | [http://localhost:3000](http://localhost:3000) | Main AI assistant interface |
| **Ollama API** | [http://localhost:11434](http://localhost:11434) | Local model serving API |
| **PostgreSQL** | `localhost:5432` | Primary database (admin tools required) |
| **Redis** | `localhost:6379` | Cache and session storage |
| **Qdrant Dashboard** | [http://localhost:6333/dashboard](http://localhost:6333/dashboard) | Vector database interface |
| **Neo4j Browser** | [http://localhost:7474](http://localhost:7474) | Graph database interface |
| **Nginx Proxy** | [http://localhost:8081](http://localhost:8081) | Load balancer and SSL termination |

### 🔐 Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| **OpenWebUI** | *Your registration* | *Your password* |
| **Neo4j** | `neo4j` | `password` |
| **PostgreSQL** | `postgres` | `postgres` |

### 📊 Production Services (docker-compose.prod.yml)

Additional services available in production mode:

| Service | URL | Description |
|---------|-----|-------------|
| **Grafana** | [http://localhost:3001](http://localhost:3001) | Analytics dashboards (`admin`/`admin123`) |
| **Prometheus** | [http://localhost:9090](http://localhost:9090) | Metrics collection |
| **LightLLM** | [http://localhost:8000](http://localhost:8000) | High-performance model serving |
| **GraphRAG Processor** | [http://localhost:8001](http://localhost:8001) | Document processing service |
| **MCP Server** | [http://localhost:9000](http://localhost:9000) | Model Context Protocol server |

### ⚡ Health Checks

Verify all services are running:

```bash
# Check service status
docker-compose ps

# Test main application
curl http://localhost:3000/health

# Test database connectivity
docker-compose exec postgres pg_isready -U postgres -d openwebui

# Test vector database
curl http://localhost:6333/health
```

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)
- [Production Deployment](#production-deployment)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)

## ✨ Features

### Core Capabilities
- **Multi-Model Support**: Seamlessly switch between local (LightLLM/Ollama) and hosted AI models
- **Prompt Engineering Laboratory**: Create, version, and test prompts with A/B testing
- **Assistant Development**: Build and deploy specialized AI assistants for various domains
- **GraphRAG Integration**: Enhanced knowledge retrieval with graph-based RAG
- **MCP Protocol Support**: Custom tools and external system connectivity
- **Real-time Analytics**: Performance metrics and model comparison dashboards

### Advanced Features
- **Conversation Management**: Persistent chat history with threading
- **Knowledge Base**: Document ingestion and vector/graph-based retrieval
- **Performance Monitoring**: Comprehensive metrics and alerting
- **Kubernetes Ready**: Production-grade deployment with Helm charts
- **High Availability**: Redis clustering, PostgreSQL replication, auto-scaling

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   OpenWebUI     │    │    LightLLM     │    │   GraphRAG      │
│   Frontend      │◄──►│  Model Server   │◄──►│   Processor     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │    │    Qdrant       │
│   Database      │    │     Cache       │    │  Vector Store   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────┐
                    │     Neo4j       │
                    │  Graph Store    │
                    └─────────────────┘
```

### Container Services

| Service | Purpose | Port | Dependencies |
|---------|---------|------|-------------|
| `openwebui` | Web interface | 3000 | postgres, redis |
| `lightllm` | Model inference | 8000 | - |
| `postgres` | Primary database | 5432 | - |
| `redis` | Cache & sessions | 6379 | - |
| `qdrant` | Vector database | 6333 | - |
| `neo4j` | Graph database | 7474, 7687 | - |
| `graphrag-processor` | Document processing | 8001 | postgres, qdrant, neo4j |
| `mcp-server` | Tool integration | 9000 | postgres, redis |
| `nginx` | Load balancer | 8081, 9443 | openwebui |

### Key Components

#### 1. Frontend Layer (OpenWebUI)
- Modern React-based web interface
- Real-time chat with model switching
- Prompt management and versioning
- Assistant configuration dashboard
- Analytics and monitoring views

#### 2. Model Serving Layer
- **LightLLM**: High-performance GPU-accelerated inference
- **Ollama**: Simple CPU-based local models (development)
- Dynamic model routing and load balancing
- Resource monitoring and auto-scaling

#### 3. Knowledge Layer
- **GraphRAG**: Advanced retrieval with entity relationships
- **Vector Search**: Semantic similarity via embeddings
- **Document Processing**: Automated chunking and indexing
- **Knowledge Graphs**: Entity extraction and linking

#### 4. Integration Layer
- **MCP Server**: Custom tools and external APIs
- **API Gateway**: Unified interface for all services
- **Event Bus**: Async processing via Celery/Redis
- **Monitoring**: Prometheus metrics and Grafana dashboards

## 🔧 Prerequisites

### System Requirements

#### Development Environment
- **OS**: Linux, macOS, or Windows with WSL2
- **CPU**: 4+ cores recommended
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 50GB+ available space
- **GPU**: Optional (NVIDIA with CUDA for LightLLM)

#### Production Environment
- **Kubernetes**: v1.24+ with GPU support (optional)
- **CPU**: 8+ cores per node
- **RAM**: 64GB+ per node
- **Storage**: High-performance SSD with 500GB+
- **GPU**: NVIDIA V100/A100 for optimal performance

### Software Dependencies

#### Required
- **Docker**: v20.10+ with Compose v2.0+
- **Git**: v2.30+
- **Python**: v3.9+ (for local development)

#### Optional
- **Kubernetes**: v1.24+ (production deployment)
- **Helm**: v3.8+ (Kubernetes package manager)
- **NVIDIA Docker**: For GPU acceleration
- **kubectl**: Kubernetes command-line tool

### Installation Commands

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git python3 python3-pip

# macOS
brew install docker docker-compose git python3

# Enable Docker service
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

## 📦 Installation

### Development Setup

#### 1. Clone Repository
```bash
git clone <repository-url>
cd openwebui
```

#### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

#### 3. Basic Development Deployment
```bash
# Start core services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f openwebui
```

#### 4. Initialize Database
```bash
# Run database migrations
docker-compose exec postgres psql -U postgres -d openwebui -f /migrations/001_ai_assistant_platform_extensions.sql
docker-compose exec postgres psql -U postgres -d openwebui -f /migrations/002_assistant_framework_extensions.sql
docker-compose exec postgres psql -U postgres -d openwebui -f /migrations/003_graphrag_knowledge_system.sql
```

### Production Setup

#### 1. Environment Variables
Create production environment file:

```bash
# .env.prod
WEBUI_SECRET_KEY=your-secure-secret-key-here
DB_NAME=openwebui_prod
DB_USER=openwebui_user  
DB_PASSWORD=secure-database-password
REDIS_PASSWORD=secure-redis-password
NEO4J_PASSWORD=secure-neo4j-password
GRAFANA_ADMIN_PASSWORD=secure-grafana-password
```

#### 2. Production Docker Deployment
```bash
# Production with monitoring
docker-compose -f docker-compose.prod.yml up -d

# High-availability setup
docker-compose -f docker-compose.ha.yml up -d
```

#### 3. Kubernetes Deployment
```bash
# Add Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install the platform
helm install openwebui-platform ./helm \
  --set global.storageClass=fast-ssd \
  --set postgresql.auth.postgresPassword=your-password \
  --set monitoring.enabled=true
```

## 🎯 Usage

### Basic Operations

#### Starting the Platform
```bash
# Development
docker-compose up -d

# Production  
docker-compose -f docker-compose.prod.yml up -d

# View running services
docker-compose ps
```

#### Accessing Services
- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:3000/docs
- **Grafana Dashboards**: http://localhost:3001 (admin/admin123)
- **Neo4j Browser**: http://localhost:7474 (neo4j/password)
- **Qdrant Dashboard**: http://localhost:6333/dashboard

### Core Workflows

#### 1. Model Management
```bash
# Add a new model (via OpenWebUI interface)
# 1. Navigate to Settings > Models
# 2. Add model configuration:
#    - Name: gpt-4-turbo
#    - API Base: https://api.openai.com/v1
#    - API Key: your-openai-key

# Or configure LightLLM models
# 1. Place model files in ./models/ directory
# 2. Update lightllm service configuration
# 3. Restart container: docker-compose restart lightllm
```

#### 2. Prompt Engineering
```bash
# Create prompt via API
curl -X POST http://localhost:3000/api/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Code Review Assistant",
    "category": "development", 
    "template": "Review this code for best practices:\n\n{code}",
    "parameters": {"code": {"type": "text", "required": true}}
  }'

# Test prompt variations
curl -X POST http://localhost:3000/api/prompts/test \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_id": "prompt-uuid",
    "model": "gpt-4-turbo",
    "parameters": {"code": "def hello():\n    print('world')"}
  }'
```

#### 3. Document Ingestion (GraphRAG)
```bash
# Upload documents via API
curl -X POST http://localhost:3000/api/knowledge/upload \
  -F "file=@document.pdf" \
  -F "collection=technical-docs"

# Query knowledge base
curl -X POST http://localhost:3000/api/knowledge/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I configure authentication?",
    "collection": "technical-docs",
    "top_k": 5
  }'
```

#### 4. Assistant Deployment
```bash
# Create specialized assistant
curl -X POST http://localhost:3000/api/assistants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DevOps Helper",
    "description": "Kubernetes and Docker expert",
    "base_prompt": "You are a DevOps expert specializing in Kubernetes...",
    "model": "gpt-4-turbo",
    "tools": ["kubectl", "docker", "terraform"]
  }'
```

### Advanced Features

#### GraphRAG Knowledge Enhancement
The platform automatically enhances responses using GraphRAG:

1. **Document Processing**: Uploaded documents are chunked and processed
2. **Entity Extraction**: Entities and relationships are identified
3. **Graph Construction**: Knowledge graph built in Neo4j
4. **Query Enhancement**: User queries enriched with graph context
5. **Response Generation**: LLM generates responses with enhanced context

#### MCP Tool Integration
Custom tools can be added via MCP protocol:

```python
# Example MCP tool registration
from src.mcp.mcp_server import register_tool

@register_tool("weather")
def get_weather(location: str) -> str:
    """Get current weather for a location."""
    # Implementation here
    return f"Weather in {location}: 72°F, sunny"
```

### Monitoring and Analytics

#### Key Metrics Dashboard
Access Grafana at http://localhost:3001 to view:

- **Response Times**: Model inference latency
- **Throughput**: Requests per second
- **Resource Usage**: CPU, memory, GPU utilization  
- **Quality Metrics**: User ratings, conversation length
- **System Health**: Service availability, error rates

#### Performance Optimization
```bash
# Scale services based on load
docker-compose up -d --scale openwebui=3
docker-compose up -d --scale celery-worker=5

# Monitor resource usage
docker stats

# Check service logs
docker-compose logs -f --tail=100 openwebui
```

## 🛠️ Development

### Local Development Setup

#### 1. Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements/graphrag.txt
pip install -r requirements/mcp.txt
```

#### 2. Development Services
```bash
# Start infrastructure only
docker-compose up -d postgres redis qdrant neo4j

# Run application locally
cd src
python -m uvicorn api.main:app --reload --port 8000
```

#### 3. Database Migrations
```bash
# Create new migration
python scripts/create_migration.py "add_new_feature"

# Run migrations
python scripts/run_migrations.py

# Rollback migration
python scripts/rollback_migration.py
```

### Testing

#### Running Tests
```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests  
python -m pytest tests/integration/ -v

# End-to-end tests
python -m pytest tests/e2e/ -v

# With coverage
python -m pytest --cov=src --cov-report=html
```

#### Test Categories
- **Unit Tests**: Individual component functionality
- **Integration Tests**: Service-to-service communication
- **API Tests**: REST API endpoints
- **Performance Tests**: Load testing and benchmarks
- **Security Tests**: Vulnerability scanning

### Code Quality

#### Linting and Formatting
```bash
# Python code formatting
black src/ tests/
isort src/ tests/

# Linting
flake8 src/ tests/
pylint src/

# Type checking
mypy src/
```

#### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run on all files
pre-commit run --all-files
```

## 🚀 Production Deployment

### Docker Swarm Deployment

#### 1. Initialize Swarm
```bash
# On manager node
docker swarm init --advertise-addr <manager-ip>

# Join worker nodes
docker swarm join --token <token> <manager-ip>:2377
```

#### 2. Deploy Stack
```bash
# Create overlay networks
docker network create -d overlay ai-assistant
docker network create -d overlay monitoring

# Deploy production stack
docker stack deploy -c docker-compose.prod.yml openwebui-platform
```

### Kubernetes Deployment

#### 1. Cluster Prerequisites
```bash
# Install required operators
kubectl apply -f https://github.com/prometheus-operator/prometheus-operator/releases/latest/download/bundle.yaml

# Install NVIDIA GPU operator (if using GPUs)
helm repo add nvidia https://nvidia.github.io/gpu-operator
helm install --wait gpu-operator nvidia/gpu-operator --namespace gpu-operator --create-namespace
```

#### 2. Platform Deployment
```bash
# Create namespace
kubectl create namespace openwebui-platform

# Install with custom values
helm install openwebui-platform ./helm \
  --namespace openwebui-platform \
  --values values.prod.yaml
```

#### 3. Monitoring Setup
```bash
# Install Prometheus stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

### SSL/TLS Configuration

#### Let's Encrypt with Cert-Manager
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml

# Create cluster issuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@domain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Backup and Disaster Recovery

#### Automated Backups
```bash
# PostgreSQL backup
kubectl create job --from=cronjob/postgres-backup postgres-backup-manual

# Volume snapshots
kubectl apply -f backup/volume-snapshots.yaml

# Application data backup
kubectl exec deployment/openwebui-platform -- tar czf - /app/data | \
  aws s3 cp - s3://your-backup-bucket/openwebui-$(date +%Y%m%d).tar.gz
```

## 📖 API Reference

### Authentication
```bash
# Get API token
curl -X POST http://localhost:3000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Use token in subsequent requests
curl -H "Authorization: Bearer <token>" http://localhost:3000/api/models
```

### Core Endpoints

#### Models API
```bash
# List available models
GET /api/models

# Add new model
POST /api/models
{
  "name": "gpt-4-turbo",
  "provider": "openai", 
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1"
}

# Test model
POST /api/models/{model_id}/test
{
  "prompt": "Hello, world!",
  "max_tokens": 100
}
```

#### Prompts API
```bash
# Create prompt template
POST /api/prompts
{
  "name": "Code Reviewer",
  "template": "Review this code:\n\n{code}",
  "category": "development"
}

# List prompts
GET /api/prompts?category=development

# Execute prompt
POST /api/prompts/{prompt_id}/execute
{
  "model": "gpt-4-turbo",
  "parameters": {"code": "def hello(): pass"}
}
```

#### Knowledge API
```bash
# Upload document
POST /api/knowledge/upload
Content-Type: multipart/form-data
file: document.pdf
collection: technical-docs

# Query knowledge base
POST /api/knowledge/query
{
  "query": "How to configure SSL?",
  "collection": "technical-docs",
  "top_k": 5,
  "use_graphrag": true
}
```

#### Assistants API
```bash
# Create assistant
POST /api/assistants
{
  "name": "DevOps Expert",
  "description": "Kubernetes and Docker specialist",
  "base_prompt": "You are a DevOps expert...",
  "model": "gpt-4-turbo",
  "tools": ["kubectl", "docker"]
}

# Chat with assistant
POST /api/assistants/{assistant_id}/chat
{
  "message": "How do I scale a deployment?",
  "conversation_id": "conv-123"
}
```

## 🤝 Contributing

### Development Workflow

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/openwebui-platform.git
   cd openwebui-platform
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Development Setup**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements/dev.txt
   pre-commit install
   ```

4. **Make Changes**
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation as needed

5. **Test Your Changes**
   ```bash
   python -m pytest
   python scripts/validate_system.py
   ```

6. **Submit Pull Request**
   - Describe changes and motivation
   - Link to relevant issues
   - Ensure CI passes

### Code Style Guidelines

#### Python
- Follow PEP 8 styling
- Use type hints for function signatures
- Maximum line length: 88 characters
- Use descriptive variable names
- Add docstrings for modules, classes, and functions

#### Docker
- Use multi-stage builds for optimization
- Pin base image versions
- Run containers as non-root user
- Minimize layer count

#### Documentation
- Use clear, concise language
- Provide code examples
- Keep README and API docs updated
- Include troubleshooting information

## 🔧 Troubleshooting

### Common Issues

#### 1. Services Won't Start
```bash
# Check Docker daemon
sudo systemctl status docker

# Check container logs
docker-compose logs --tail=50 <service-name>

# Verify port availability
ss -tlnp | grep <port>

# Check disk space
df -h
```

#### 2. Database Connection Errors
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U postgres -d openwebui -c "SELECT 1;"

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### 3. Model Loading Issues
```bash
# Check LightLLM logs
docker-compose logs lightllm

# Verify model files
docker-compose exec lightllm ls -la /models

# Check GPU availability
nvidia-smi  # If using GPU

# Test model endpoint
curl http://localhost:8000/health
```

#### 4. Memory Issues
```bash
# Monitor resource usage
docker stats

# Increase Docker memory limits
# Edit: Docker Desktop → Settings → Resources

# Optimize service resource limits
# Edit docker-compose.yml deploy.resources section
```

#### 5. Network Connectivity
```bash
# Test internal networking
docker network ls
docker network inspect openwebui_ai-assistant

# Check service discovery
docker-compose exec openwebui nslookup postgres

# Verify firewall rules
sudo ufw status
```

### Performance Optimization

#### 1. Database Tuning
```sql
-- PostgreSQL optimization
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

#### 2. Redis Configuration
```bash
# Optimize Redis memory
docker-compose exec redis redis-cli CONFIG SET maxmemory 2gb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### 3. Vector Database Optimization
```bash
# Qdrant optimization
curl -X PUT "http://localhost:6333/collections/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 768,
      "distance": "Cosine"
    },
    "optimizers_config": {
      "default_segment_number": 2
    }
  }'
```

### Logging and Debugging

#### Enable Debug Logging
```bash
# Set environment variables
export LOG_LEVEL=DEBUG
export PYTHONPATH=/app/src

# Restart services with debug logging
docker-compose up -d
```

#### Centralized Logging
```bash
# View aggregated logs
docker-compose logs -f

# Export logs for analysis
docker-compose logs --since 1h > platform-logs.txt

# Monitor specific service
docker-compose logs -f openwebui | grep ERROR
```

### Getting Help

#### Community Support
- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Ask questions and share experiences
- **Discord**: Real-time community chat (link in repository)

#### Enterprise Support
- **Professional Services**: Architecture consulting and custom development
- **Training**: Team training and workshops
- **SLA Support**: 24/7 support with guaranteed response times

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenWebUI](https://github.com/open-webui/open-webui) - Core web interface
- [LightLLM](https://github.com/ModelTC/lightllm) - High-performance model serving
- [Qdrant](https://qdrant.tech/) - Vector database
- [Neo4j](https://neo4j.com/) - Graph database
- [GraphRAG](https://github.com/microsoft/graphrag) - Graph-based retrieval augmentation

---

**Built with ❤️ for the AI community**