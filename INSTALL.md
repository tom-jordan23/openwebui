# Installation Guide

This guide provides step-by-step instructions for installing and configuring the OpenWebUI AI Assistant Platform across different environments.

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Development Environment](#development-environment)
- [Production Environment](#production-environment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Configuration](#configuration)
- [Verification](#verification)
- [Post-Installation Setup](#post-installation-setup)

## 🖥️ System Requirements

### Minimum Requirements

#### Development Environment
- **OS**: Linux (Ubuntu 20.04+), macOS (12+), Windows 10/11 with WSL2
- **CPU**: 4 cores (x86_64 or ARM64)
- **RAM**: 16GB
- **Storage**: 50GB available space
- **Network**: Broadband internet connection

#### Production Environment
- **OS**: Linux (Ubuntu 20.04+ LTS recommended)
- **CPU**: 8+ cores per node
- **RAM**: 32GB+ per node (64GB recommended)
- **Storage**: 500GB+ NVMe SSD
- **Network**: 1Gbps+ network connection
- **GPU**: Optional - NVIDIA GPU with CUDA 11.8+ for LightLLM acceleration

### Recommended Specifications

#### High-Performance Setup
- **CPU**: 16+ cores (Intel Xeon, AMD EPYC, or Apple M1/M2)
- **RAM**: 128GB+
- **Storage**: 2TB+ NVMe SSD
- **GPU**: NVIDIA A100, V100, or RTX 4090 for optimal performance
- **Network**: 10Gbps+ for multi-user environments

## ⚡ Quick Start

### Option 1: One-Command Setup (Recommended for Testing)

```bash
# Download and run the installation script
curl -fsSL https://raw.githubusercontent.com/your-repo/openwebui/main/scripts/install.sh | bash
```

### Option 2: Manual Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-repo/openwebui.git
cd openwebui

# 2. Run setup script
./scripts/setup.sh

# 3. Start the platform
docker-compose up -d

# 4. Access the web interface
open http://localhost:3000
```

## 🛠️ Development Environment

### Step 1: Install Prerequisites

#### Ubuntu/Debian
```bash
# Update package index
sudo apt update

# Install Docker
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install additional tools
sudo apt install -y git python3 python3-pip python3-venv

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### CentOS/RHEL/Fedora
```bash
# Install Docker
sudo dnf install -y dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install additional tools
sudo dnf install -y git python3 python3-pip

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

#### macOS
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker Desktop
brew install --cask docker

# Install additional tools
brew install git python3

# Start Docker Desktop (GUI application)
open -a Docker
```

#### Windows (WSL2)
```powershell
# Install WSL2 and Ubuntu
wsl --install -d Ubuntu

# Restart and complete Ubuntu setup
# Then follow Ubuntu instructions above
```

### Step 2: Clone and Setup Repository

```bash
# Clone the repository
git clone https://github.com/your-repo/openwebui.git
cd openwebui

# Create and configure environment file
cp .env.example .env

# Edit environment variables (see Configuration section)
nano .env
```

### Step 3: Initialize Development Environment

```bash
# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements/dev.txt

# Install pre-commit hooks
pre-commit install

# Start development services
docker-compose up -d

# Wait for services to be ready (check health)
./scripts/wait-for-services.sh
```

### Step 4: Initialize Database

```bash
# Run database migrations
docker-compose exec postgres psql -U postgres -d openwebui -f /migrations/001_ai_assistant_platform_extensions.sql
docker-compose exec postgres psql -U postgres -d openwebui -f /migrations/002_assistant_framework_extensions.sql
docker-compose exec postgres psql -U postgres -d openwebui -f /migrations/003_graphrag_knowledge_system.sql
docker-compose exec postgres psql -U postgres -d openwebui -f /migrations/004_enhance_graphrag_schema.sql

# Verify database setup
python scripts/validate_database.py
```

### Step 5: Verify Installation

```bash
# Check service status
docker-compose ps

# Test API endpoints
curl http://localhost:3000/health
curl http://localhost:8000/health  # LightLLM (if using)

# Run system validation
python scripts/validate_system.py

# Access web interface
open http://localhost:3000
```

## 🏭 Production Environment

### Step 1: Server Preparation

#### System Updates and Security
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Configure firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 3000  # OpenWebUI
sudo ufw allow 8000  # LightLLM
```

#### Install NVIDIA Drivers (for GPU acceleration)
```bash
# Install NVIDIA drivers
sudo apt install -y nvidia-driver-525

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update
sudo apt install -y nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker

# Test GPU access
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
```

### Step 2: Production Configuration

#### Environment Variables
```bash
# Create production environment file
sudo mkdir -p /opt/openwebui
sudo chown $USER:$USER /opt/openwebui
cd /opt/openwebui

# Create secure environment file
cat > .env.prod << EOF
# Core Configuration
ENVIRONMENT=production
WEBUI_SECRET_KEY=$(openssl rand -hex 32)
DEBUG=false

# Database Configuration
DB_NAME=openwebui_prod
DB_USER=openwebui_user
DB_PASSWORD=$(openssl rand -base64 32)
DATABASE_URL=postgresql://\${DB_USER}:\${DB_PASSWORD}@postgres-primary:5432/\${DB_NAME}

# Redis Configuration
REDIS_PASSWORD=$(openssl rand -base64 32)
REDIS_URL=redis://:\${REDIS_PASSWORD}@redis-master:6379

# Neo4j Configuration
NEO4J_PASSWORD=$(openssl rand -base64 32)
NEO4J_USER=neo4j

# Monitoring
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32)
PROMETHEUS_RETENTION_TIME=30d

# Security
SENTRY_DSN=your-sentry-dsn
SSL_CERT_PATH=/etc/ssl/certs/platform.crt
SSL_KEY_PATH=/etc/ssl/private/platform.key
EOF

# Secure the environment file
chmod 600 .env.prod
```

#### SSL/TLS Certificates
```bash
# Option 1: Self-signed certificates (development/testing)
sudo mkdir -p /etc/ssl/private /etc/ssl/certs
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/platform.key \
    -out /etc/ssl/certs/platform.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"

# Option 2: Let's Encrypt certificates (production)
sudo apt install -y certbot
sudo certbot certonly --standalone -d your-domain.com
sudo ln -s /etc/letsencrypt/live/your-domain.com/fullchain.pem /etc/ssl/certs/platform.crt
sudo ln -s /etc/letsencrypt/live/your-domain.com/privkey.pem /etc/ssl/private/platform.key
```

### Step 3: Deploy Production Stack

```bash
# Clone repository to production directory
git clone https://github.com/your-repo/openwebui.git .

# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to start
./scripts/wait-for-services.sh

# Run health checks
./scripts/health-check.sh
```

### Step 4: Configure Monitoring

```bash
# Set up log rotation
sudo tee /etc/logrotate.d/openwebui << EOF
/var/lib/docker/containers/*/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF

# Configure system monitoring
sudo systemctl enable --now prometheus-node-exporter
sudo systemctl enable --now grafana-server
```

### Step 5: Backup Configuration

```bash
# Create backup script
sudo tee /usr/local/bin/backup-openwebui.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/openwebui"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker-compose exec -T postgres-primary pg_dump -U postgres openwebui_prod | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

# Backup Redis
docker-compose exec -T redis-master redis-cli --rdb /tmp/dump.rdb
docker cp $(docker-compose ps -q redis-master):/tmp/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Backup application data
tar czf $BACKUP_DIR/data_$DATE.tar.gz data/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +30 -delete
EOF

sudo chmod +x /usr/local/bin/backup-openwebui.sh

# Schedule daily backups
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-openwebui.sh
```

## ☸️ Kubernetes Deployment

### Step 1: Kubernetes Cluster Setup

#### Option 1: Local Development with Kind
```bash
# Install Kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.18.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Create cluster
kind create cluster --config config/kind-cluster.yaml
```

#### Option 2: Production Cluster
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Step 2: Install Required Operators

#### GPU Operator (for NVIDIA GPUs)
```bash
# Add NVIDIA Helm repository
helm repo add nvidia https://nvidia.github.io/gpu-operator
helm repo update

# Install GPU operator
helm install --wait gpu-operator nvidia/gpu-operator \
    --namespace gpu-operator \
    --create-namespace
```

#### Cert-Manager (for SSL certificates)
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.11.0/cert-manager.yaml

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s deployment/cert-manager -n cert-manager
```

#### Prometheus Operator
```bash
# Add Prometheus community repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
helm install monitoring prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --create-namespace \
    --set grafana.adminPassword=admin123
```

### Step 3: Configure Storage

#### Create Storage Classes
```bash
# Apply storage configuration
kubectl apply -f - << EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/gce-pd  # Adjust for your cloud provider
parameters:
  type: pd-ssd
  replication-type: regional-pd
reclaimPolicy: Delete
allowVolumeExpansion: true
EOF
```

### Step 4: Deploy Platform

#### Install Dependencies
```bash
# Add Bitnami repository for PostgreSQL, Redis
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install PostgreSQL
helm install postgresql bitnami/postgresql \
    --namespace openwebui-platform \
    --create-namespace \
    --set auth.postgresPassword=secure-password \
    --set primary.persistence.size=100Gi \
    --set primary.persistence.storageClass=fast-ssd

# Install Redis
helm install redis bitnami/redis \
    --namespace openwebui-platform \
    --set auth.password=secure-password \
    --set master.persistence.size=20Gi \
    --set master.persistence.storageClass=fast-ssd
```

#### Deploy OpenWebUI Platform
```bash
# Customize values
cp helm/values.yaml values-prod.yaml

# Edit production values
nano values-prod.yaml

# Install the platform
helm install openwebui-platform ./helm \
    --namespace openwebui-platform \
    --values values-prod.yaml
```

### Step 5: Configure Ingress

```bash
# Install NGINX Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
    --namespace ingress-nginx \
    --create-namespace

# Create cluster issuer for Let's Encrypt
kubectl apply -f - << EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@your-domain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## ⚙️ Configuration

### Environment Variables

#### Core Configuration
```bash
# Application Settings
ENVIRONMENT=production|development|staging
DEBUG=true|false
LOG_LEVEL=DEBUG|INFO|WARN|ERROR
WEBUI_SECRET_KEY=your-secret-key-here

# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis Configuration
REDIS_URL=redis://password@host:port/db
REDIS_MAX_CONNECTIONS=100

# Model Configuration
LIGHTLLM_URL=http://lightllm:8000
OLLAMA_BASE_URL=http://ollama:11434
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Knowledge Systems
VECTOR_DB_URL=http://qdrant:6333
GRAPH_DB_URL=bolt://neo4j:7687
ENABLE_GRAPHRAG=true
ENABLE_MCP=true

# Security
CORS_ORIGINS=["http://localhost:3000","https://your-domain.com"]
SESSION_EXPIRE_HOURS=24
MAX_UPLOAD_SIZE=100MB
```

#### Performance Tuning
```bash
# Worker Configuration
CELERY_WORKERS=4
CELERY_MAX_TASKS_PER_CHILD=1000
CELERY_PREFETCH_MULTIPLIER=1

# Model Serving
LIGHTLLM_MAX_TOTAL_TOKEN_NUM=120000
LIGHTLLM_TP=1  # Tensor parallelism
LIGHTLLM_GPU_MEMORY_FRACTION=0.9

# Database Optimization
POSTGRES_SHARED_BUFFERS=256MB
POSTGRES_WORK_MEM=4MB
POSTGRES_MAINTENANCE_WORK_MEM=64MB
```

### Service Configuration

#### Nginx Configuration
```nginx
# /config/nginx/nginx.conf
upstream openwebui_backend {
    server openwebui:8080 max_fails=3 fail_timeout=30s;
}

upstream lightllm_backend {
    server lightllm:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/platform.crt;
    ssl_certificate_key /etc/ssl/private/platform.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    client_max_body_size 100M;
    proxy_read_timeout 300s;
    proxy_connect_timeout 75s;

    location / {
        proxy_pass http://openwebui_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/models/infer {
        proxy_pass http://lightllm_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;
    }
}
```

#### Prometheus Configuration
```yaml
# /config/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "/etc/prometheus/rules/*.yml"

scrape_configs:
  - job_name: 'openwebui'
    static_configs:
      - targets: ['openwebui:8080']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'lightllm'
    static_configs:
      - targets: ['lightllm:8000']
    metrics_path: /metrics

  - job_name: 'postgresql'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

## ✅ Verification

### Service Health Checks

```bash
# Basic service status
docker-compose ps

# Detailed health check
./scripts/health-check.sh

# API endpoint tests
curl -f http://localhost:3000/health
curl -f http://localhost:8000/health
curl -f http://localhost:6333/health
curl -f http://localhost:7474/browser/

# Database connectivity
docker-compose exec postgres pg_isready -U postgres -d openwebui
docker-compose exec redis redis-cli ping
```

### Performance Verification

```bash
# Load testing
pip install locust
locust -f tests/load/locustfile.py --host=http://localhost:3000

# Memory and CPU monitoring
docker stats

# Storage usage
df -h
docker system df
```

### Security Verification

```bash
# SSL certificate validation
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Security scan (using Docker Scout)
docker scout cves openwebui:latest

# Network security
nmap -sS -O localhost
```

## 🔄 Post-Installation Setup

### Initial Configuration

#### 1. Create Admin User
```bash
# Via web interface: http://localhost:3000/register
# Or via API:
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@your-domain.com", 
    "password": "secure-password",
    "role": "admin"
  }'
```

#### 2. Configure Models
```bash
# Add OpenAI model
curl -X POST http://localhost:3000/api/models \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "gpt-4-turbo",
    "provider": "openai",
    "api_key": "your-openai-key",
    "base_url": "https://api.openai.com/v1"
  }'

# Add local LightLLM model
curl -X POST http://localhost:3000/api/models \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "llama2-7b-local",
    "provider": "lightllm",
    "base_url": "http://lightllm:8000"
  }'
```

#### 3. Import Sample Data
```bash
# Upload sample documents
python scripts/import_sample_data.py

# Create sample prompts
python scripts/create_sample_prompts.py

# Initialize knowledge base
python scripts/initialize_knowledge_base.py
```

### Monitoring Setup

#### 1. Configure Grafana Dashboards
```bash
# Access Grafana: http://localhost:3001 (admin/admin123)
# Import dashboards:
curl -X POST http://admin:admin123@localhost:3001/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @config/grafana/dashboards/openwebui-overview.json
```

#### 2. Set Up Alerting
```bash
# Configure alert rules
kubectl apply -f config/prometheus/rules/openwebui-alerts.yml

# Set up notification channels
curl -X POST http://admin:admin123@localhost:3001/api/alert-notifications \
  -H "Content-Type: application/json" \
  -d '{
    "name": "slack-alerts",
    "type": "slack",
    "settings": {
      "url": "your-slack-webhook-url",
      "channel": "#alerts"
    }
  }'
```

### Maintenance Tasks

#### 1. Regular Updates
```bash
# Create update script
cat > update-platform.sh << 'EOF'
#!/bin/bash
# Pull latest images
docker-compose pull

# Restart services with zero downtime
docker-compose up -d --remove-orphans

# Clean up old images
docker image prune -f
EOF

chmod +x update-platform.sh
```

#### 2. Database Maintenance
```bash
# Schedule vacuum and analyze
sudo crontab -e
# Add: 0 3 * * 0 docker-compose exec postgres psql -U postgres -d openwebui -c "VACUUM ANALYZE;"
```

---

For troubleshooting and advanced configuration, see the [main README](README.md) and [troubleshooting guide](TROUBLESHOOTING.md).

Need help? Join our community support channels or contact our professional services team for enterprise assistance.