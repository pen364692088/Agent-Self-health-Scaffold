#!/bin/bash

# OpenEmotion MCP Kubernetes Deployment Script
# This script deploys the OpenEmotion MCP API to Kubernetes

set -euo pipefail

# Configuration
NAMESPACE="openemotion"
ENVIRONMENT="${1:-production}"
IMAGE_TAG="${2:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot access Kubernetes cluster"
        exit 1
    fi
    
    # Check if we can create namespaces
    if ! kubectl auth can-i create namespaces &> /dev/null; then
        print_warning "Cannot create namespaces - they must exist already"
    fi
    
    print_status "Prerequisites check passed"
}

# Create namespace if it doesn't exist
create_namespace() {
    local ns="$1"
    if ! kubectl get namespace "$ns" &> /dev/null; then
        print_status "Creating namespace: $ns"
        kubectl apply -f namespace.yaml
    else
        print_status "Namespace $ns already exists"
    fi
}

# Apply manifests in order
apply_manifests() {
    local ns="$1"
    
    print_status "Applying manifests to namespace: $ns"
    
    # Apply ConfigMaps
    print_status "Applying ConfigMaps..."
    kubectl apply -f configmap.yaml -n "$ns"
    
    # Apply Secrets (if they exist)
    if [ -f "secrets.yaml" ]; then
        print_status "Applying Secrets..."
        kubectl apply -f secret.yaml -n "$ns"
    else
        print_warning "secret.yaml not found - secrets must be created manually"
    fi
    
    # Apply Deployments
    print_status "Applying Deployments..."
    kubectl apply -f deployment.yaml -n "$ns"
    
    # Apply Services
    print_status "Applying Services..."
    kubectl apply -f service.yaml -n "$ns"
    
    # Apply NetworkPolicies
    print_status "Applying NetworkPolicies..."
    kubectl apply -f networkpolicy.yaml -n "$ns"
    
    # Apply HPAs
    print_status "Applying HorizontalPodAutoscalers..."
    kubectl apply -f hpa.yaml -n "$ns"
    
    # Apply ServiceMonitors (if Prometheus is installed)
    if kubectl get crd servicemonitors.monitoring.coreos.com &> /dev/null; then
        print_status "Applying ServiceMonitors..."
        kubectl apply -f servicemonitor.yaml -n "$ns"
    else
        print_warning "Prometheus Operator not found - skipping ServiceMonitors"
    fi
    
    # Apply Ingress (if Ingress controller is available)
    if kubectl get ingressclass nginx &> /dev/null; then
        print_status "Applying Ingress..."
        kubectl apply -f ingress.yaml -n "$ns"
    else
        print_warning "NGINX Ingress Controller not found - skipping Ingress"
    fi
}

# Wait for deployment to be ready
wait_for_deployment() {
    local ns="$1"
    local deployment="openemotion-api"
    
    print_status "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/"$deployment" -n "$ns"
    
    print_status "Deployment is ready!"
}

# Show deployment status
show_status() {
    local ns="$1"
    
    print_status "Deployment status:"
    kubectl get pods -n "$ns" -l app=openemotion
    kubectl get services -n "$ns" -l app=openemotion
    kubectl get ingress -n "$ns" -l app=openemotion 2>/dev/null || true
    kubectl get hpa -n "$ns" -l app=openemotion
}

# Main deployment function
deploy() {
    local ns="$1"
    
    print_status "Starting deployment to $ns..."
    
    create_namespace "$ns"
    apply_manifests "$ns"
    wait_for_deployment "$ns"
    show_status "$ns"
    
    print_status "Deployment completed successfully!"
}

# Rollback function
rollback() {
    local ns="$1"
    local deployment="openemotion-api"
    
    print_warning "Rolling back deployment in namespace: $ns"
    kubectl rollout undo deployment/"$deployment" -n "$ns"
    kubectl rollout status deployment/"$deployment" -n "$ns"
    
    print_status "Rollback completed"
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        check_prerequisites
        
        if [ "$ENVIRONMENT" = "production" ]; then
            deploy "openemotion"
        elif [ "$ENVIRONMENT" = "staging" ]; then
            deploy "openemotion-staging"
        else
            print_error "Invalid environment: $ENVIRONMENT"
            echo "Usage: $0 [deploy|rollback] [production|staging] [image-tag]"
            exit 1
        fi
        ;;
    "rollback")
        if [ "$ENVIRONMENT" = "production" ]; then
            rollback "openemotion"
        elif [ "$ENVIRONMENT" = "staging" ]; then
            rollback "openemotion-staging"
        else
            print_error "Invalid environment: $ENVIRONMENT"
            echo "Usage: $0 [deploy|rollback] [production|staging] [image-tag]"
            exit 1
        fi
        ;;
    "status")
        if [ "$ENVIRONMENT" = "production" ]; then
            show_status "openemotion"
        elif [ "$ENVIRONMENT" = "staging" ]; then
            show_status "openemotion-staging"
        else
            print_error "Invalid environment: $ENVIRONMENT"
            echo "Usage: $0 [deploy|rollback|status] [production|staging] [image-tag]"
            exit 1
        fi
        ;;
    *)
        print_error "Invalid command: $1"
        echo "Usage: $0 [deploy|rollback|status] [production|staging] [image-tag]"
        exit 1
        ;;
esac