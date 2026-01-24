#!/bin/bash

# Kubernetes Deployment Script for News Summarizer
# Usage: ./k8s/deploy.sh [your-openai-api-key]

set -e

echo "🚀 Deploying News Summarizer to Kubernetes..."

# Check if OpenAI API key is provided
if [ -z "$1" ]; then
    echo "❌ Error: OpenAI API key is required"
    echo "Usage: ./k8s/deploy.sh YOUR_OPENAI_API_KEY"
    exit 1
fi

OPENAI_API_KEY=$1

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ Error: kubectl is not installed or not in PATH"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Error: Cannot connect to Kubernetes cluster"
    echo "Please configure kubectl to access your cluster"
    exit 1
fi

echo "✅ Kubernetes cluster is accessible"

# Create namespace (optional, comment out if you want to use default)
# kubectl create namespace newssummariser --dry-run=client -o yaml | kubectl apply -f -

# Create secret
echo "📝 Creating Kubernetes secret..."
kubectl create secret generic newssummariser-secrets \
    --from-literal=openai-api-key="$OPENAI_API_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -

# Apply ConfigMap
echo "📝 Applying ConfigMap..."
kubectl apply -f k8s/configmap.yaml

# Apply Deployment
echo "📝 Applying Deployment..."
kubectl apply -f k8s/deployment.yaml

# Apply Service
echo "📝 Applying Service..."
kubectl apply -f k8s/service.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/newssummariser --timeout=300s

# Get service information
echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📊 Deployment Status:"
kubectl get deployment newssummariser
echo ""
kubectl get pods -l app=newssummariser
echo ""
kubectl get svc newssummariser-service
echo ""

# Get external IP or instructions
SERVICE_TYPE=$(kubectl get svc newssummariser-service -o jsonpath='{.spec.type}')
if [ "$SERVICE_TYPE" = "LoadBalancer" ]; then
    echo "🌐 Getting external IP (this may take a few minutes)..."
    EXTERNAL_IP=$(kubectl get svc newssummariser-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ -z "$EXTERNAL_IP" ]; then
        EXTERNAL_IP=$(kubectl get svc newssummariser-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    fi
    if [ -n "$EXTERNAL_IP" ]; then
        echo "✅ Application is accessible at:"
        echo "   Streamlit UI: http://$EXTERNAL_IP"
        echo "   API: http://$EXTERNAL_IP:8000"
    else
        echo "⏳ External IP is being provisioned. Check with:"
        echo "   kubectl get svc newssummariser-service"
    fi
else
    echo "📝 To access the application, use port-forwarding:"
    echo "   kubectl port-forward svc/newssummariser-service 8501:8501"
    echo "   Then access at: http://localhost:8501"
fi

echo ""
echo "📝 Useful commands:"
echo "   View logs: kubectl logs -f deployment/newssummariser"
echo "   Scale: kubectl scale deployment newssummariser --replicas=3"
echo "   Delete: kubectl delete -f k8s/"

