#!/bin/bash

# Deploy News Summarizer with Ollama running locally (not in Kubernetes)
# This is better for laptop deployments with limited resources

set -e

echo "🚀 Deploying News Summarizer with Local Ollama"
echo "=============================================="

# Check if OpenAI API key is provided
if [ -z "$1" ]; then
    echo "❌ Error: OpenAI API key is required (for fallback)"
    echo "Usage: ./k8s/deploy-local-ollama.sh YOUR_OPENAI_API_KEY"
    exit 1
fi

OPENAI_KEY=$1

# Check if minikube is running
if ! minikube status &> /dev/null; then
    echo "❌ Error: Minikube is not running"
    echo "Start minikube with: minikube start"
    exit 1
fi

echo "✅ Minikube is running"
echo ""

# Check if Ollama is installed locally
if ! command -v ollama &> /dev/null; then
    echo "❌ Error: Ollama is not installed locally"
    echo "   Install with: brew install ollama"
    echo "   Or run: ./install-ollama.sh"
    exit 1
fi

echo "✅ Ollama is installed"
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama server is not running"
    echo "   Starting Ollama server..."
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    sleep 5
    
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "❌ Failed to start Ollama server"
        echo "   Try manually: ollama serve"
        exit 1
    fi
fi

echo "✅ Ollama server is running"
echo ""

# Check if Mistral model is installed
if ! ollama list | grep -q "mistral:7b"; then
    echo "📥 Mistral 7B model not found. Downloading (~4GB, may take 5-10 minutes)..."
    ollama pull mistral:7b
    echo "✅ Mistral 7B downloaded"
else
    echo "✅ Mistral 7B model is already installed"
fi

echo ""

# Set kubectl context
kubectl config use-context minikube

# Create secret
echo "📝 Creating Kubernetes secret..."
kubectl create secret generic newssummariser-secrets \
    --from-literal=openai-api-key="$OPENAI_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -

# Apply ConfigMap
echo "📝 Applying ConfigMap..."
kubectl apply -f k8s/configmap.yaml

# Deploy News Summarizer (configured to use local Ollama)
echo "📦 Deploying News Summarizer..."
kubectl apply -f k8s/deployment-with-local-ollama.yaml

# Apply Service
echo "📦 Applying Service..."
kubectl apply -f k8s/service-minikube.yaml

# Wait for deployment
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/newssummariser --timeout=300s

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📊 Status:"
kubectl get pods -l app=newssummariser
echo ""
echo "🌐 Access:"
MINIKUBE_IP=$(minikube ip)
echo "   Streamlit UI: http://$MINIKUBE_IP:30080"
echo "   API: http://$MINIKUBE_IP:30081"
echo ""
echo "📝 Notes:"
echo "   - Ollama is running locally on your laptop (port 11434)"
echo "   - Kubernetes pods connect to it via host.docker.internal"
echo "   - Keep 'ollama serve' running in background"
echo ""

