#!/bin/bash

# Kubernetes Deployment Script for News Summarizer (Minikube)
# Usage: ./k8s/deploy-minikube.sh [your-openai-api-key]

set -e

echo "🚀 Deploying News Summarizer to Minikube..."

# Check if OpenAI API key is provided
if [ -z "$1" ]; then
    echo "❌ Error: OpenAI API key is required"
    echo "Usage: ./k8s/deploy-minikube.sh YOUR_OPENAI_API_KEY"
    exit 1
fi

OPENAI_API_KEY=$1

# Check if minikube is running
if ! minikube status &> /dev/null; then
    echo "❌ Error: Minikube is not running"
    echo "Start minikube with: minikube start"
    exit 1
fi

echo "✅ Minikube is running"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ Error: kubectl is not installed or not in PATH"
    exit 1
fi

# Set kubectl context to minikube
kubectl config use-context minikube

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

# Apply Service (NodePort for minikube)
echo "📝 Applying Service (NodePort)..."
kubectl apply -f k8s/service-minikube.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/newssummariser --timeout=300s

# Get minikube IP
MINIKUBE_IP=$(minikube ip)

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

# Show access information
echo "🌐 Access the application:"
echo ""
echo "Option 1: Using minikube service (recommended)"
echo "   Streamlit UI: minikube service newssummariser-service -n default --url | grep 30080"
echo "   Or run: minikube service newssummariser-service"
echo ""
echo "Option 2: Direct access via NodePort"
echo "   Streamlit UI: http://$MINIKUBE_IP:30080"
echo "   API: http://$MINIKUBE_IP:30081"
echo ""
echo "Option 3: Port forwarding"
echo "   kubectl port-forward svc/newssummariser-service 8501:8501"
echo "   Then access at: http://localhost:8501"
echo ""

echo "📝 Useful commands:"
echo "   View logs: kubectl logs -f deployment/newssummariser"
echo "   Scale: kubectl scale deployment newssummariser --replicas=3"
echo "   Open in browser: minikube service newssummariser-service"
echo "   Delete: kubectl delete -f k8s/"

