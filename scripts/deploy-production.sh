#!/bin/bash

# OpenWebUI Platform Production Deployment Script
# Comprehensive deployment for Kubernetes and Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="openwebui-platform"
NAMESPACE="openwebui-prod"
HELM_RELEASE="openwebui"
ENV_FILE=".env.prod"
KUBECONFIG_DEFAULT="~/.kube/config"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    local deps=("kubectl" "helm" "docker" "docker-compose")
    local missing_deps=()
    
    for dep in "${deps[@]}"; do
        if ! command -v $dep &> /dev/null; then
            missing_deps+=("$dep")
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Please install the missing dependencies and try again."
        exit 1
    fi
    
    log_success "All dependencies are installed."
}

check_environment() {
    log_info "Checking environment configuration..."
    
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "Environment file $ENV_FILE not found. Creating from template..."
        create_env_template
    fi
    
    # Source environment variables
    source "$ENV_FILE"
    
    # Check required variables
    local required_vars=("WEBUI_SECRET_KEY" "DB_PASSWORD" "REDIS_PASSWORD" "NEO4J_PASSWORD" "GRAFANA_ADMIN_PASSWORD")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "Missing environment variables: ${missing_vars[*]}"
        log_info "Please update $ENV_FILE with the required values."
        exit 1
    fi
    
    log_success "Environment configuration is valid."
}

create_env_template() {
    cat > "$ENV_FILE" << EOF
# OpenWebUI Platform Production Environment Configuration

# Application Secrets
WEBUI_SECRET_KEY=your-super-secret-key-change-this-in-production
SENTRY_DSN=

# Database Configuration
DB_NAME=openwebui
DB_USER=postgres
DB_PASSWORD=change-this-strong-password

# Redis Configuration
REDIS_PASSWORD=change-this-redis-password

# Neo4j Configuration
NEO4J_PASSWORD=change-this-neo4j-password

# Monitoring
GRAFANA_ADMIN_PASSWORD=change-this-grafana-password

# External APIs (Optional)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
COHERE_API_KEY=

# Domain Configuration
DOMAIN=ai-assistant.yourdomain.com
LETS_ENCRYPT_EMAIL=admin@yourdomain.com

# Resource Limits
OPENWEBUI_CPU_LIMIT=2
OPENWEBUI_MEMORY_LIMIT=4Gi
LIGHTLLM_CPU_LIMIT=8
LIGHTLLM_MEMORY_LIMIT=32Gi

# Scaling Configuration
MIN_REPLICAS=2
MAX_REPLICAS=10
EOF
    
    log_warning "Environment template created at $ENV_FILE. Please update with your values."
    exit 1
}

validate_kubernetes() {
    log_info "Validating Kubernetes connection..."
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    log_success "Kubernetes cluster connection validated."
}

create_namespace() {
    log_info "Creating namespace $NAMESPACE..."
    
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Label namespace for monitoring
    kubectl label namespace "$NAMESPACE" monitoring=enabled --overwrite
    
    log_success "Namespace $NAMESPACE created/updated."
}

install_cert_manager() {
    log_info "Installing cert-manager for SSL certificates..."
    
    # Add Jetstack Helm repository
    helm repo add jetstack https://charts.jetstack.io
    helm repo update
    
    # Install cert-manager
    helm upgrade --install cert-manager jetstack/cert-manager \
        --namespace cert-manager \
        --create-namespace \
        --version v1.13.0 \
        --set installCRDs=true \
        --wait
    
    # Create ClusterIssuer for Let's Encrypt
    cat << EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: $LETS_ENCRYPT_EMAIL
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
    
    log_success "Cert-manager installed and configured."
}

install_ingress_controller() {
    log_info "Installing NGINX Ingress Controller..."
    
    # Add ingress-nginx repository
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo update
    
    # Install ingress controller
    helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        --set controller.metrics.enabled=true \
        --set controller.podAnnotations."prometheus\.io/scrape"=true \
        --set controller.podAnnotations."prometheus\.io/port"=10254 \
        --wait
    
    log_success "NGINX Ingress Controller installed."
}

install_monitoring_stack() {
    log_info "Installing monitoring stack (Prometheus & Grafana)..."
    
    # Add Prometheus community repository
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo update
    
    # Install kube-prometheus-stack
    helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --create-namespace \
        --set prometheus.prometheusSpec.retention=30d \
        --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=50Gi \
        --set grafana.adminPassword="$GRAFANA_ADMIN_PASSWORD" \
        --set grafana.persistence.enabled=true \
        --set grafana.persistence.size=10Gi \
        --wait
    
    log_success "Monitoring stack installed."
}

deploy_helm_chart() {
    log_info "Deploying OpenWebUI Platform using Helm..."
    
    # Update Helm dependencies
    helm dependency update ./helm/
    
    # Create values override file
    cat > values-prod.yaml << EOF
global:
  imageRegistry: ""
  
openwebui:
  env:
    WEBUI_SECRET_KEY: "$WEBUI_SECRET_KEY"
    
postgresql:
  auth:
    postgresPassword: "$DB_PASSWORD"
    
redis:
  auth:
    password: "$REDIS_PASSWORD"
    
neo4j:
  neo4j:
    password: "$NEO4J_PASSWORD"
    
ingress:
  enabled: true
  hosts:
    - host: "$DOMAIN"
      paths:
        - path: /
          pathType: Prefix
          service:
            name: openwebui
            port: 8080
  tls:
    - secretName: "$PROJECT_NAME-tls"
      hosts:
        - "$DOMAIN"
        
monitoring:
  enabled: true
  grafana:
    adminPassword: "$GRAFANA_ADMIN_PASSWORD"
EOF
    
    # Deploy the Helm chart
    helm upgrade --install "$HELM_RELEASE" ./helm/ \
        --namespace "$NAMESPACE" \
        --values values-prod.yaml \
        --wait \
        --timeout 20m
    
    log_success "OpenWebUI Platform deployed successfully."
}

deploy_docker_compose() {
    log_info "Deploying OpenWebUI Platform using Docker Compose..."
    
    # Validate Docker Compose file
    docker-compose -f "$DOCKER_COMPOSE_FILE" config > /dev/null
    
    # Pull latest images
    docker-compose -f "$DOCKER_COMPOSE_FILE" pull
    
    # Start services
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    log_success "OpenWebUI Platform deployed with Docker Compose."
}

run_health_checks() {
    log_info "Running health checks..."
    
    if [ "$DEPLOYMENT_TYPE" == "kubernetes" ]; then
        # Wait for pods to be ready
        kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance="$HELM_RELEASE" -n "$NAMESPACE" --timeout=300s
        
        # Check service endpoints
        kubectl get endpoints -n "$NAMESPACE"
        
    elif [ "$DEPLOYMENT_TYPE" == "docker-compose" ]; then
        # Wait for services to be healthy
        local max_attempts=30
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up (healthy)"; then
                break
            fi
            
            log_info "Waiting for services to be healthy... (Attempt $attempt/$max_attempts)"
            sleep 10
            ((attempt++))
        done
        
        # Show service status
        docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    fi
    
    log_success "Health checks completed."
}

show_access_info() {
    log_info "Deployment completed! Access information:"
    
    if [ "$DEPLOYMENT_TYPE" == "kubernetes" ]; then
        echo -e "${GREEN}OpenWebUI Platform:${NC} https://$DOMAIN"
        echo -e "${GREEN}Grafana Dashboard:${NC} https://$DOMAIN/grafana"
        
        # Get service IPs if using NodePort or LoadBalancer
        kubectl get svc -n "$NAMESPACE"
        
    elif [ "$DEPLOYMENT_TYPE" == "docker-compose" ]; then
        echo -e "${GREEN}OpenWebUI Platform:${NC} http://localhost:8080 (or https://localhost if using nginx)"
        echo -e "${GREEN}Grafana Dashboard:${NC} http://localhost:3000"
        echo -e "${GREEN}Prometheus:${NC} http://localhost:9090"
        echo -e "${GREEN}LightLLM API:${NC} http://localhost:8000"
        echo -e "${GREEN}MCP Server:${NC} http://localhost:9000"
    fi
    
    echo -e "${YELLOW}Default Credentials:${NC}"
    echo -e "  Grafana: admin / $GRAFANA_ADMIN_PASSWORD"
    echo -e "  Neo4j: neo4j / $NEO4J_PASSWORD"
}

cleanup_failed_deployment() {
    log_warning "Cleaning up failed deployment..."
    
    if [ "$DEPLOYMENT_TYPE" == "kubernetes" ]; then
        helm uninstall "$HELM_RELEASE" -n "$NAMESPACE" 2>/dev/null || true
        kubectl delete namespace "$NAMESPACE" 2>/dev/null || true
    elif [ "$DEPLOYMENT_TYPE" == "docker-compose" ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" down -v 2>/dev/null || true
    fi
}

# Main execution
main() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}  OpenWebUI Platform Deployment Script   ${NC}"
    echo -e "${BLUE}===========================================${NC}"
    echo
    
    # Parse command line arguments
    DEPLOYMENT_TYPE="kubernetes"
    SKIP_CHECKS=false
    CLEANUP_ON_FAILURE=true
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                DEPLOYMENT_TYPE="$2"
                shift 2
                ;;
            --docker-compose)
                DEPLOYMENT_TYPE="docker-compose"
                shift
                ;;
            --skip-checks)
                SKIP_CHECKS=true
                shift
                ;;
            --no-cleanup)
                CLEANUP_ON_FAILURE=false
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  -t, --type TYPE          Deployment type: kubernetes (default) or docker-compose"
                echo "  --docker-compose         Shorthand for --type docker-compose"
                echo "  --skip-checks           Skip dependency and environment checks"
                echo "  --no-cleanup            Don't cleanup on deployment failure"
                echo "  -h, --help              Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    log_info "Starting deployment with type: $DEPLOYMENT_TYPE"
    
    # Set error trap
    if [ "$CLEANUP_ON_FAILURE" == "true" ]; then
        trap cleanup_failed_deployment ERR
    fi
    
    # Pre-deployment checks
    if [ "$SKIP_CHECKS" == "false" ]; then
        check_dependencies
        check_environment
    fi
    
    # Deployment specific steps
    if [ "$DEPLOYMENT_TYPE" == "kubernetes" ]; then
        validate_kubernetes
        create_namespace
        install_cert_manager
        install_ingress_controller
        install_monitoring_stack
        deploy_helm_chart
    elif [ "$DEPLOYMENT_TYPE" == "docker-compose" ]; then
        deploy_docker_compose
    else
        log_error "Invalid deployment type: $DEPLOYMENT_TYPE"
        exit 1
    fi
    
    # Post-deployment steps
    run_health_checks
    show_access_info
    
    echo
    log_success "OpenWebUI Platform deployment completed successfully!"
    
    # Clean up temporary files
    rm -f values-prod.yaml
}

# Execute main function with all arguments
main "$@"