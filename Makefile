.PHONY: help build up down logs test-all benchmark security-scan validate-deployment test-integration clean \
         deploy-prod deploy-k8s deploy-docker validate-prod build-images push-images helm-install \
         monitoring-setup security-setup backup-create backup-restore scale-up scale-down

help:
	@echo "Personal AI Assistant - Development Commands"
	@echo ""
	@echo "Environment:"
	@echo "  build                Build all containers"
	@echo "  up                   Start development environment"
	@echo "  down                 Stop all services"
	@echo "  logs                 View logs from all services"
	@echo "  clean                Clean up containers and volumes"
	@echo ""
	@echo "Testing & Validation:"
	@echo "  test-all             Run complete test suite"
	@echo "  test-integration     Run integration tests"
	@echo "  benchmark            Run performance benchmarks"
	@echo "  security-scan        Run security vulnerability scan"
	@echo "  validate-deployment  Validate deployment health"
	@echo "  validate-phase       Validate current development phase"

build:
	docker compose build

up:
	docker compose up -d
	@echo "Waiting for services to start..."
	@sleep 30
	@make validate-deployment

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down -v
	docker system prune -f

test-all: test-setup
	@echo "Running complete test suite..."
	@mkdir -p reports
	./venv/bin/pytest tests/ -v --cov=tests --html=reports/test_report.html
	@echo "Running integration tests..."
	@make test-integration

test-setup:
	@echo "Setting up Python virtual environment for testing..."
	python3 -m venv venv || true
	@echo "Installing test dependencies..."
	./venv/bin/pip install -r tests/requirements.txt

test-unit:
	@echo "Running unit tests only..."
	@mkdir -p reports
	./venv/bin/pytest tests/unit/ -v

test-integration-pytest:
	@echo "Running integration tests with pytest..."
	@mkdir -p reports
	./venv/bin/pytest tests/integration/ -v

test-coverage:
	@echo "Running tests with coverage analysis..."
	@mkdir -p reports htmlcov
	PYTHONPATH=. ./venv/bin/pytest tests/ --cov=tests --cov-report=html:htmlcov --cov-report=term-missing --cov-fail-under=80

test-database:
	@echo "Running database layer tests..."
	@mkdir -p reports
	PYTHONPATH=. ./venv/bin/pytest tests/database/ -v

validate-database-schema:
	@echo "Validating database schema and performance..."
	@./database/migrate.sh status
	@echo "Running schema validation tests..."
	PYTHONPATH=. ./venv/bin/pytest tests/database/test_schema_validation.py -v

test-integration:
	@echo "Testing OpenWebUI health..."
	curl -f http://localhost:3000/health || exit 1
	@echo "Testing Ollama API..."
	curl -f http://localhost:11434/api/tags || exit 1
	@echo "Testing database connection..."
	docker compose exec postgres psql -U postgres -d openwebui -c "SELECT 1;" || exit 1

benchmark:
	@echo "Running performance benchmarks..."
	@echo "Response time test..."
	time curl -s http://localhost:3000/health > /dev/null
	@echo "Model inference test..."
	time curl -s -X POST http://localhost:11434/api/generate \
		-H "Content-Type: application/json" \
		-d '{"model": "llama3.2:1b", "prompt": "Hello", "stream": false}' > /dev/null

security-scan:
	@echo "Scanning containers for vulnerabilities..."
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image openwebui:latest
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image modelscope/lightllm:latest

validate-deployment:
	@echo "Validating deployment health..."
	@echo "Checking container status..."
	docker compose ps
	@echo "Testing service endpoints..."
	@sleep 5
	curl -f http://localhost:3000/health || (echo "OpenWebUI health check failed" && exit 1)
	@echo "✓ OpenWebUI is healthy"
	@echo "✓ Deployment validation passed"

validate-phase:
	@echo "Phase 1 Validation Checklist:"
	@echo "[ ] All containers start successfully"
	@make validate-deployment
	@echo "[ ] OpenWebUI accessible at http://localhost:3000"
	@echo "[ ] Database connections established"
	@echo "[ ] Health checks passing for all services"
	@echo "Phase 1 validation complete!"

# Production Deployment Commands

deploy-prod:
	@echo "Starting production deployment..."
	@./scripts/deploy-production.sh

deploy-k8s:
	@echo "Deploying to Kubernetes..."
	@./scripts/deploy-production.sh --type kubernetes

deploy-docker:
	@echo "Deploying with Docker Compose (production)..."
	@./scripts/deploy-production.sh --type docker-compose

build-images:
	@echo "Building production images..."
	docker build -f docker/Dockerfile.graphrag -t openwebui/graphrag-processor:latest .
	docker build -f docker/Dockerfile.mcp -t openwebui/mcp-server:latest .
	@echo "✓ Production images built"

helm-install:
	@echo "Installing/upgrading Helm chart..."
	helm dependency update ./helm/
	helm upgrade --install openwebui ./helm/ \
		--namespace openwebui-prod \
		--create-namespace \
		--wait
	@echo "✓ Helm chart deployed"

validate-prod:
	@echo "Validating production deployment..."
	@if command -v kubectl >/dev/null 2>&1; then \
		kubectl get pods -n openwebui-prod; \
		echo "✓ Kubernetes deployment validated"; \
	else \
		docker compose -f docker-compose.prod.yml ps; \
		echo "✓ Docker Compose deployment validated"; \
	fi

test-graphrag:
	@echo "Testing GraphRAG system..."
	PYTHONPATH=. ./venv/bin/python scripts/validate_graphrag_system.py