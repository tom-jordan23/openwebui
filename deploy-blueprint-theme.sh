#!/bin/bash

# Blueprint Theme Deployment Script for tojo.world
# This script rebuilds OpenWebUI with the integrated blueprint theme

set -e

echo "🎨 Deploying Blueprint Theme for OpenWebUI on tojo.world..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available. Please install Docker Compose first."
        exit 1
    fi
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

print_status "Using Docker Compose command: $DOCKER_COMPOSE"

# Check if we're in the right directory
if [[ ! -f "docker-compose.yml" ]]; then
    print_error "docker-compose.yml not found. Please run this script from the OpenWebUI project root."
    exit 1
fi

# Check if blueprint theme files exist
if [[ ! -f "src/frontend/styles/blueprint-theme.css" ]]; then
    print_error "Blueprint theme files not found. Please ensure the theme integration is complete."
    exit 1
fi

print_success "Blueprint theme files found!"

# Stop existing containers
print_status "Stopping existing containers..."
$DOCKER_COMPOSE down

# Remove old images to force rebuild
print_status "Removing old OpenWebUI image..."
docker rmi openwebui-blueprint:latest 2>/dev/null || true

# Build new image with blueprint theme
print_status "Building OpenWebUI with Blueprint Theme..."
$DOCKER_COMPOSE build --no-cache openwebui

if [[ $? -ne 0 ]]; then
    print_error "Failed to build OpenWebUI with blueprint theme"
    exit 1
fi

print_success "OpenWebUI with Blueprint Theme built successfully!"

# Start services
print_status "Starting services..."
$DOCKER_COMPOSE up -d

if [[ $? -ne 0 ]]; then
    print_error "Failed to start services"
    exit 1
fi

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 10

# Check if OpenWebUI is responding
print_status "Checking OpenWebUI status..."
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null; then
        print_success "OpenWebUI is responding!"
        break
    fi
    if [[ $i -eq 30 ]]; then
        print_warning "OpenWebUI might not be ready yet, but deployment is complete."
    fi
    sleep 2
done

# Check if nginx is working
print_status "Checking nginx proxy status..."
for i in {1..15}; do
    if curl -s http://localhost:8081 > /dev/null; then
        print_success "Nginx proxy is responding!"
        break
    fi
    if [[ $i -eq 15 ]]; then
        print_warning "Nginx proxy might not be ready yet."
    fi
    sleep 2
done

# Display deployment information
echo ""
echo "🎉 Blueprint Theme Deployment Complete!"
echo "======================================"
echo ""
echo "📍 Access Points:"
echo "   • Direct OpenWebUI: http://localhost:3000"
echo "   • Nginx Proxy:      http://localhost:8081 (with theme injection)"
echo ""
echo "🎨 Theme Features:"
echo "   • Blueprint technical drawing aesthetic"
echo "   • tojo.world branding integration"
echo "   • Compass rose navigation elements"
echo "   • Technical grid backgrounds"
echo "   • Aged paper color scheme"
echo ""
echo "🔧 Theme Files:"
echo "   • CSS: /themes/blueprint/blueprint-theme.css"
echo "   • Components: /themes/blueprint/blueprint-components.css"
echo "   • Script: /themes/blueprint/blueprint-inject.js"
echo ""
echo "📋 Container Status:"
$DOCKER_COMPOSE ps

echo ""
echo "📝 Logs (last 10 lines from openwebui):"
$DOCKER_COMPOSE logs --tail=10 openwebui

echo ""
print_success "Deployment completed! Visit http://localhost:8081 to see the blueprint theme."
print_status "The theme will automatically apply when you access OpenWebUI through the nginx proxy."

# Optional: Open browser
if command -v xdg-open &> /dev/null; then
    read -p "Would you like to open OpenWebUI in your browser? (y/N): " open_browser
    if [[ $open_browser =~ ^[Yy]$ ]]; then
        xdg-open http://localhost:8081
    fi
elif command -v open &> /dev/null; then
    read -p "Would you like to open OpenWebUI in your browser? (y/N): " open_browser
    if [[ $open_browser =~ ^[Yy]$ ]]; then
        open http://localhost:8081
    fi
fi

echo ""
print_success "Blueprint theme deployment for tojo.world is complete! 🎨✨"