# Troubleshooting Guide

This guide provides solutions to common issues encountered with the OpenWebUI AI Assistant Platform.

## 📋 Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Installation Issues](#installation-issues)
- [Service Startup Problems](#service-startup-problems)
- [Database Issues](#database-issues)
- [Model and API Problems](#model-and-api-problems)
- [Performance Issues](#performance-issues)
- [Network and Connectivity](#network-and-connectivity)
- [Authentication and Authorization](#authentication-and-authorization)
- [Knowledge Base Issues](#knowledge-base-issues)
- [Docker and Container Issues](#docker-and-container-issues)
- [Kubernetes Deployment Issues](#kubernetes-deployment-issues)
- [Monitoring and Logging](#monitoring-and-logging)
- [Getting Help](#getting-help)

## 🔍 Quick Diagnostics

### System Health Check
```bash
# Run comprehensive health check
./scripts/health-check.sh

# Quick service status
docker-compose ps

# Check system resources
docker stats --no-stream
df -h
free -m
```

### Common First Steps
1. **Check Service Logs**
   ```bash
   docker-compose logs --tail=50 openwebui
   docker-compose logs --tail=50 postgres
   docker-compose logs --tail=50 redis
   ```

2. **Verify Network Connectivity**
   ```bash
   curl -f http://localhost:3000/health
   curl -f http://localhost:8000/health
   ```

3. **Check Environment Variables**
   ```bash
   docker-compose config
   ```

4. **Restart Services**
   ```bash
   docker-compose restart
   ```

## 🛠️ Installation Issues

### Docker Installation Problems

#### Issue: Docker not starting
```bash
# Check Docker daemon status
sudo systemctl status docker

# Start Docker daemon
sudo systemctl start docker

# Enable auto-start
sudo systemctl enable docker

# Check for permission issues
sudo usermod -aG docker $USER
newgrp docker
```

#### Issue: Docker Compose command not found
```bash
# Check Docker Compose installation
docker-compose --version

# Install/update Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Alternative: Use Docker Compose plugin
docker compose --version
```

#### Issue: Permission denied errors
```bash
# Fix Docker socket permissions
sudo chmod 666 /var/run/docker.sock

# Or add user to docker group
sudo usermod -aG docker $USER
logout  # Log out and back in
```

### Disk Space Issues

#### Issue: No space left on device
```bash
# Check disk usage
df -h
docker system df

# Clean up Docker resources
docker system prune -f
docker volume prune -f
docker image prune -a -f

# Clean up logs
sudo journalctl --vacuum-time=7d
```

#### Issue: Large Docker volumes
```bash
# Find large volumes
docker volume ls -q | xargs docker volume inspect | grep -A 3 Mountpoint

# Remove unused volumes
docker volume ls -qf dangling=true | xargs docker volume rm
```

### Git and Repository Issues

#### Issue: Clone fails with SSL certificate problem
```bash
# Temporary workaround (not recommended for production)
git config --global http.sslVerify false

# Better solution: Update CA certificates
sudo apt update && sudo apt install ca-certificates
```

#### Issue: Submodule update fails
```bash
# Initialize and update submodules
git submodule init
git submodule update --recursive
```

## 🚀 Service Startup Problems

### Container Startup Failures

#### Issue: OpenWebUI container exits immediately
```bash
# Check detailed logs
docker-compose logs openwebui

# Common causes and solutions:
# 1. Database connection failed
docker-compose logs postgres
docker-compose exec postgres pg_isready -U postgres -d openwebui

# 2. Missing environment variables
docker-compose config | grep -i env

# 3. Port already in use
sudo netstat -tlnp | grep :3000
sudo lsof -i :3000

# Kill process using port
sudo kill -9 $(sudo lsof -t -i:3000)
```

#### Issue: LightLLM container fails to start
```bash
# Check GPU availability (if using GPU)
nvidia-smi
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi

# Check model files
docker-compose exec lightllm ls -la /models

# Check memory requirements
free -h
# LightLLM typically needs 8GB+ RAM for 7B models
```

#### Issue: Database container won't start
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Common issues:
# 1. Data directory permissions
sudo chown -R 999:999 ./data/postgres

# 2. Port conflict
sudo netstat -tlnp | grep :5432

# 3. Corrupted data - reset database
docker-compose down -v
docker volume rm openwebui_postgres_data
docker-compose up -d postgres
```

### Service Dependencies

#### Issue: Services start in wrong order
```bash
# Use wait script
./scripts/wait-for-services.sh

# Or restart with explicit dependencies
docker-compose down
docker-compose up -d postgres redis
sleep 30
docker-compose up -d
```

#### Issue: Health checks failing
```bash
# Test health endpoints manually
curl -f http://localhost:3000/health
curl -f http://localhost:8000/health

# Check service configuration
docker-compose exec openwebui ps aux
docker-compose exec openwebui netstat -tlnp
```

## 🗄️ Database Issues

### PostgreSQL Connection Problems

#### Issue: Connection refused
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres pg_isready -U postgres -d openwebui

# Check network connectivity
docker-compose exec openwebui ping postgres

# Verify credentials
docker-compose exec postgres psql -U postgres -d openwebui -c "SELECT 1;"
```

#### Issue: Authentication failed
```bash
# Check environment variables
docker-compose exec openwebui env | grep DATABASE

# Reset PostgreSQL password
docker-compose exec postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'new_password';"

# Update environment file
nano .env
# DATABASE_URL=postgresql://postgres:new_password@postgres:5432/openwebui
```

#### Issue: Database doesn't exist
```bash
# Create database manually
docker-compose exec postgres createdb -U postgres openwebui

# Or via SQL
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE openwebui;"
```

### Migration Issues

#### Issue: Migration failed
```bash
# Check migration status
docker-compose exec postgres psql -U postgres -d openwebui -c "SELECT * FROM alembic_version;"

# Run migrations manually
docker-compose exec postgres psql -U postgres -d openwebui -f /migrations/001_ai_assistant_platform_extensions.sql

# Reset and rerun all migrations
python scripts/reset_migrations.py
python scripts/run_migrations.py
```

#### Issue: Schema conflicts
```bash
# Backup current database
docker-compose exec postgres pg_dump -U postgres openwebui > backup.sql

# Drop and recreate database
docker-compose exec postgres dropdb -U postgres openwebui
docker-compose exec postgres createdb -U postgres openwebui

# Restore from backup (if needed)
docker-compose exec -T postgres psql -U postgres openwebui < backup.sql
```

### Performance Problems

#### Issue: Slow database queries
```bash
# Check active connections
docker-compose exec postgres psql -U postgres -d openwebui -c "SELECT * FROM pg_stat_activity;"

# Analyze slow queries
docker-compose exec postgres psql -U postgres -d openwebui -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Update database statistics
docker-compose exec postgres psql -U postgres -d openwebui -c "ANALYZE;"
```

#### Issue: Connection pool exhausted
```bash
# Check current connections
docker-compose exec postgres psql -U postgres -d openwebui -c "SELECT count(*) FROM pg_stat_activity;"

# Increase connection limits
# Edit docker-compose.yml:
# postgres:
#   command: postgres -c max_connections=200
```

## 🤖 Model and API Problems

### Model Loading Issues

#### Issue: Model not found or loading fails
```bash
# Check model files
docker-compose exec lightllm ls -la /models

# Verify model format
docker-compose exec lightllm find /models -name "*.bin" -o -name "*.safetensors"

# Test model loading manually
docker-compose exec lightllm python -c "
from transformers import AutoModel
model = AutoModel.from_pretrained('/models/llama2-7b')
print('Model loaded successfully')
"
```

#### Issue: Out of memory during model loading
```bash
# Check available memory
free -h
docker stats lightllm

# Reduce model size or use quantization
# Edit docker-compose.yml to add:
# environment:
#   - LIGHTLLM_QUANTIZATION=int8
#   - LIGHTLLM_GPU_MEMORY_FRACTION=0.8
```

#### Issue: GPU not detected
```bash
# Check NVIDIA driver
nvidia-smi

# Verify Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi

# Check container GPU access
docker-compose exec lightllm nvidia-smi
```

### API Integration Problems

#### Issue: OpenAI API key invalid
```bash
# Test API key directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-your-key-here"

# Check environment variable
docker-compose exec openwebui env | grep OPENAI

# Update API key
# Edit .env file and restart
docker-compose restart openwebui
```

#### Issue: Rate limit exceeded
```bash
# Check rate limit headers
curl -I https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer sk-your-key-here"

# Implement backoff in application
# Or switch to different model temporarily
```

#### Issue: Model response timeout
```bash
# Increase timeout values
# Edit docker-compose.yml:
# environment:
#   - MODEL_TIMEOUT=120
#   - HTTP_TIMEOUT=180
```

### Model Performance Issues

#### Issue: Slow inference times
```bash
# Monitor resource usage
docker stats lightllm

# Check model configuration
curl http://localhost:8000/v1/models

# Optimize model settings
# Edit model configuration:
# - Reduce max_tokens
# - Increase batch_size
# - Use tensor parallelism for large models
```

#### Issue: Quality degradation
```bash
# Test with different parameters
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-model",
    "messages": [{"role": "user", "content": "Test message"}],
    "temperature": 0.7,
    "top_p": 0.9
  }'

# Compare with baseline results
# Check for model drift or corruption
```

## ⚡ Performance Issues

### High Resource Usage

#### Issue: High CPU usage
```bash
# Identify resource-intensive processes
docker stats
top -p $(docker inspect --format='{{.State.Pid}}' openwebui)

# Optimize worker processes
# Edit environment variables:
# CELERY_WORKERS=2  # Reduce if CPU-bound
# GUNICORN_WORKERS=4
```

#### Issue: High memory usage
```bash
# Check memory distribution
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Identify memory leaks
docker-compose exec openwebui python -c "
import psutil
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"

# Restart high-memory services
docker-compose restart openwebui
```

#### Issue: Disk I/O bottlenecks
```bash
# Monitor disk usage
iostat -x 1

# Check database performance
docker-compose exec postgres psql -U postgres -d openwebui -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 5;
"

# Optimize database
docker-compose exec postgres psql -U postgres -d openwebui -c "VACUUM ANALYZE;"
```

### Response Time Issues

#### Issue: Slow API responses
```bash
# Test endpoint response times
time curl http://localhost:3000/api/health

# Check application logs for bottlenecks
docker-compose logs openwebui | grep -i "slow\|timeout\|error"

# Monitor database query times
docker-compose exec postgres tail -f /var/log/postgresql/postgresql-*.log
```

#### Issue: Frontend loading slowly
```bash
# Check network requests
# Use browser developer tools → Network tab

# Optimize static assets
# Check nginx configuration for caching
docker-compose exec nginx cat /etc/nginx/nginx.conf | grep -A 5 "cache"

# Enable compression
# Add to nginx.conf:
# gzip on;
# gzip_types text/css application/javascript application/json;
```

### Scaling Issues

#### Issue: Cannot handle concurrent users
```bash
# Increase worker processes
# Edit docker-compose.yml:
# openwebui:
#   environment:
#     - GUNICORN_WORKERS=8
#     - CELERY_WORKERS=4

# Scale services horizontally
docker-compose up -d --scale openwebui=3

# Add load balancer
# Configure nginx upstream with multiple backends
```

#### Issue: Queue backlog
```bash
# Check Redis queue status
docker-compose exec redis redis-cli llen celery

# Monitor Celery workers
docker-compose exec celery-worker celery inspect active

# Scale workers
docker-compose up -d --scale celery-worker=6
```

## 🌐 Network and Connectivity

### Port Conflicts

#### Issue: Port already in use
```bash
# Find process using port
sudo lsof -i :3000
sudo netstat -tlnp | grep :3000

# Kill conflicting process
sudo kill -9 <PID>

# Use different port
# Edit docker-compose.yml:
# ports:
#   - "3001:8080"  # Changed from 3000
```

#### Issue: Cannot access from external network
```bash
# Check firewall rules
sudo ufw status
sudo iptables -L

# Open required ports
sudo ufw allow 3000
sudo ufw allow 8000

# Check Docker network configuration
docker network ls
docker network inspect openwebui_ai-assistant
```

### DNS and Service Discovery

#### Issue: Services cannot communicate
```bash
# Test internal connectivity
docker-compose exec openwebui ping postgres
docker-compose exec openwebui nslookup postgres

# Check Docker network
docker network inspect openwebui_ai-assistant

# Restart networking
docker-compose down
docker network prune -f
docker-compose up -d
```

#### Issue: External API calls fail
```bash
# Test internet connectivity
docker-compose exec openwebui ping 8.8.8.8
docker-compose exec openwebui curl https://api.openai.com

# Check proxy settings
docker-compose exec openwebui env | grep -i proxy

# Configure proxy if needed
# Add to docker-compose.yml:
# environment:
#   - HTTP_PROXY=http://proxy:port
#   - HTTPS_PROXY=http://proxy:port
```

### SSL/TLS Issues

#### Issue: SSL certificate errors
```bash
# Check certificate validity
openssl x509 -in /etc/ssl/certs/platform.crt -text -noout

# Test SSL connection
openssl s_client -connect localhost:443 -servername localhost

# Regenerate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/platform.key \
  -out /etc/ssl/certs/platform.crt
```

#### Issue: Mixed content warnings
```bash
# Ensure all internal links use HTTPS
# Check nginx configuration
docker-compose exec nginx cat /etc/nginx/nginx.conf

# Add security headers
# location / {
#   add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
#   add_header X-Content-Type-Options nosniff;
#   add_header X-Frame-Options DENY;
# }
```

## 🔐 Authentication and Authorization

### Login Issues

#### Issue: Cannot create admin user
```bash
# Check if users table exists
docker-compose exec postgres psql -U postgres -d openwebui -c "\dt"

# Create user manually
docker-compose exec postgres psql -U postgres -d openwebui -c "
INSERT INTO users (username, email, password_hash, role, created_at)
VALUES ('admin', 'admin@localhost', 'hashed_password', 'admin', NOW());
"

# Or reset database and recreate
python scripts/reset_database.py
python scripts/create_admin_user.py
```

#### Issue: Password reset not working
```bash
# Check email configuration
docker-compose exec openwebui env | grep -i mail

# Reset password manually
python scripts/reset_password.py --user admin --password new_password

# Or via database
docker-compose exec postgres psql -U postgres -d openwebui -c "
UPDATE users SET password_hash = 'new_hash' WHERE username = 'admin';
"
```

### API Authentication

#### Issue: JWT token expired
```bash
# Check token expiration
python -c "
import jwt
token = 'your-token-here'
decoded = jwt.decode(token, options={'verify_signature': False})
print(decoded)
"

# Get new token
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

#### Issue: API key invalid
```bash
# Verify API key in database
docker-compose exec postgres psql -U postgres -d openwebui -c "
SELECT * FROM api_keys WHERE key_hash = 'hash_of_your_key';
"

# Generate new API key
curl -X POST http://localhost:3000/api/auth/api-keys \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{"name": "new-key", "permissions": ["read", "write"]}'
```

### Permission Issues

#### Issue: Access denied errors
```bash
# Check user roles
docker-compose exec postgres psql -U postgres -d openwebui -c "
SELECT username, role, permissions FROM users;
"

# Update user permissions
docker-compose exec postgres psql -U postgres -d openwebui -c "
UPDATE users SET role = 'admin' WHERE username = 'your-user';
"
```

## 📚 Knowledge Base Issues

### Document Upload Problems

#### Issue: Upload fails with large files
```bash
# Check file size limits
docker-compose exec nginx cat /etc/nginx/nginx.conf | grep client_max_body_size

# Increase limits
# Edit nginx.conf:
# client_max_body_size 500M;

# Also check application limits
# Edit docker-compose.yml:
# environment:
#   - MAX_UPLOAD_SIZE=500MB
```

#### Issue: Document processing stuck
```bash
# Check Celery worker status
docker-compose exec celery-worker celery inspect active

# Check processing queue
docker-compose exec redis redis-cli llen document_processing

# Restart workers
docker-compose restart celery-worker

# Process document manually
python scripts/process_document.py --document-id doc-123
```

### Vector Database Issues

#### Issue: Qdrant connection failed
```bash
# Test Qdrant connection
curl http://localhost:6333/health

# Check Qdrant logs
docker-compose logs qdrant

# Restart Qdrant
docker-compose restart qdrant

# Reset Qdrant data (if corrupted)
docker-compose down
docker volume rm openwebui_qdrant_data
docker-compose up -d qdrant
```

#### Issue: Search returns no results
```bash
# Check if collection exists
curl http://localhost:6333/collections

# Check collection info
curl http://localhost:6333/collections/documents

# Reindex documents
python scripts/reindex_documents.py --collection documents

# Test search manually
curl -X POST http://localhost:6333/collections/documents/points/search \
  -H "Content-Type: application/json" \
  -d '{"vector": [0.1, 0.2, ...], "limit": 5}'
```

### GraphRAG Issues

#### Issue: Neo4j connection failed
```bash
# Test Neo4j connection
curl http://localhost:7474/db/neo4j/tx/commit

# Check Neo4j browser
open http://localhost:7474/browser/

# Check authentication
docker-compose exec neo4j cypher-shell -u neo4j -p password "RETURN 1"

# Reset Neo4j password
docker-compose exec neo4j neo4j-admin set-initial-password new_password
```

#### Issue: Graph construction fails
```bash
# Check entity extraction
docker-compose logs graphrag-processor

# Test entity extraction manually
python scripts/test_entity_extraction.py --text "Sample text"

# Rebuild knowledge graph
python scripts/rebuild_graph.py --collection documents
```

## 🐳 Docker and Container Issues

### Container Management

#### Issue: Container keeps restarting
```bash
# Check restart policy
docker inspect openwebui | grep -A 5 RestartPolicy

# Check exit codes
docker-compose ps

# View detailed logs
docker-compose logs --tail=100 openwebui

# Disable restart temporarily
docker update --restart=no openwebui
```

#### Issue: Volume mount issues
```bash
# Check volume mounts
docker inspect openwebui | grep -A 10 Mounts

# Fix permissions
sudo chown -R $USER:$USER ./data
sudo chmod -R 755 ./data

# Recreate volumes
docker-compose down -v
docker volume prune -f
docker-compose up -d
```

### Image Issues

#### Issue: Image pull fails
```bash
# Check internet connectivity
ping docker.io

# Try pulling manually
docker pull ghcr.io/open-webui/open-webui:main

# Use different registry
# Edit docker-compose.yml:
# image: ghcr.io/open-webui/open-webui:main
```

#### Issue: Image build fails
```bash
# Check build context
docker-compose build --no-cache openwebui

# Build with verbose output
docker-compose build --progress plain openwebui

# Check Dockerfile syntax
docker build -f docker/Dockerfile.graphrag .
```

### Resource Limits

#### Issue: Container killed by OOM
```bash
# Check memory limits
docker stats --no-stream

# Increase memory limits
# Edit docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 8G

# Check system memory
free -h
cat /proc/meminfo
```

## ☸️ Kubernetes Deployment Issues

### Pod Issues

#### Issue: Pods stuck in Pending state
```bash
# Check pod status
kubectl get pods -n openwebui-platform

# Describe pod for details
kubectl describe pod openwebui-xxx -n openwebui-platform

# Check node resources
kubectl top nodes
kubectl describe nodes

# Check resource requests
kubectl get pods -n openwebui-platform -o yaml | grep -A 5 resources
```

#### Issue: Pod crashes with exit code
```bash
# Check pod logs
kubectl logs openwebui-xxx -n openwebui-platform

# Check previous logs
kubectl logs openwebui-xxx -n openwebui-platform --previous

# Debug with shell access
kubectl exec -it openwebui-xxx -n openwebui-platform -- /bin/bash
```

### Service Discovery

#### Issue: Services cannot communicate
```bash
# Test service connectivity
kubectl exec -it openwebui-xxx -n openwebui-platform -- nslookup postgresql

# Check service endpoints
kubectl get endpoints -n openwebui-platform

# Check network policies
kubectl get networkpolicies -n openwebui-platform
```

### Storage Issues

#### Issue: PVC stuck in Pending
```bash
# Check PVC status
kubectl get pvc -n openwebui-platform

# Check storage class
kubectl get storageclass

# Check available storage
kubectl get pv

# Create storage class if missing
kubectl apply -f config/storage-class.yaml
```

### Helm Issues

#### Issue: Helm release failed
```bash
# Check release status
helm status openwebui-platform -n openwebui-platform

# Check release history
helm history openwebui-platform -n openwebui-platform

# Debug installation
helm install openwebui-platform ./helm --dry-run --debug

# Rollback if needed
helm rollback openwebui-platform 1 -n openwebui-platform
```

## 📊 Monitoring and Logging

### Log Collection Issues

#### Issue: Logs not appearing
```bash
# Check log drivers
docker info | grep "Logging Driver"

# Check log file locations
docker inspect openwebui | grep LogPath

# Manually check log files
sudo cat /var/lib/docker/containers/*/container-id.log
```

#### Issue: Log rotation not working
```bash
# Check logrotate configuration
cat /etc/logrotate.d/docker

# Test logrotate manually
sudo logrotate -d /etc/logrotate.d/docker

# Force log rotation
sudo logrotate -f /etc/logrotate.d/docker
```

### Metrics Collection

#### Issue: Prometheus not scraping targets
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check service discovery
kubectl get servicemonitor -n monitoring

# Test metric endpoints
curl http://openwebui:8080/metrics
curl http://lightllm:8000/metrics
```

#### Issue: Grafana dashboards not loading
```bash
# Check Grafana data source
curl http://admin:admin@localhost:3001/api/datasources

# Test Prometheus connectivity
curl http://prometheus:9090/api/v1/query?query=up

# Import dashboards manually
curl -X POST http://admin:admin@localhost:3001/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @config/grafana/dashboards/overview.json
```

### Alerting Issues

#### Issue: Alerts not firing
```bash
# Check alert rules
curl http://localhost:9090/api/v1/rules

# Check alert manager
curl http://localhost:9093/api/v1/alerts

# Test notification channels
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{"labels": {"alertname": "test"}}]'
```

## 🆘 Getting Help

### Self-Service Resources

#### Documentation
- **Installation Guide**: [INSTALL.md](INSTALL.md)
- **Usage Guide**: [USAGE.md](USAGE.md)
- **API Documentation**: http://localhost:3000/docs
- **Architecture Overview**: [README.md](README.md)

#### Diagnostic Tools
```bash
# Run comprehensive diagnostics
./scripts/diagnose.sh

# Generate support bundle
./scripts/support-bundle.sh

# System information
./scripts/system-info.sh
```

### Community Support

#### GitHub Issues
1. Search existing issues: https://github.com/your-repo/openwebui/issues
2. Create new issue with:
   - Clear problem description
   - Steps to reproduce
   - System information
   - Relevant logs

#### Discussion Forums
- **General Questions**: GitHub Discussions
- **Feature Requests**: GitHub Issues with "enhancement" label
- **Security Issues**: security@yourdomain.com

### Enterprise Support

#### Professional Services
- **Architecture Consulting**: Design and optimization
- **Custom Development**: Feature development and integration
- **Training Services**: Team training and best practices
- **Migration Services**: From other platforms

#### Support Tiers
- **Community**: GitHub issues and forums
- **Professional**: Email support with SLA
- **Enterprise**: 24/7 phone support with dedicated engineer

#### Contact Information
- **Sales**: sales@yourdomain.com
- **Support**: support@yourdomain.com
- **Security**: security@yourdomain.com
- **General**: info@yourdomain.com

### Support Information Template

When requesting support, include:

```
**Environment Information:**
- OS: [e.g., Ubuntu 22.04]
- Docker Version: [docker --version]
- Compose Version: [docker-compose --version]
- Installation Method: [Docker Compose/Kubernetes/Other]

**Problem Description:**
[Clear description of the issue]

**Steps to Reproduce:**
1. [First step]
2. [Second step]
3. [Additional steps...]

**Expected Behavior:**
[What you expected to happen]

**Actual Behavior:**
[What actually happened]

**Logs:**
```
[Paste relevant logs here]
```

**Configuration:**
```
[Paste relevant configuration files]
```

**Additional Context:**
[Any other relevant information]
```

---

**Still having issues?** Don't hesitate to reach out through our support channels. We're here to help!