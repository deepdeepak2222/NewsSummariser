#!/bin/bash

# Deploy News Summarizer with Ollama (Mistral 7B) to Minikube - REDUCED MEMORY VERSION
# For laptops with 8GB total RAM
# Usage: ./k8s/deploy-local-ollama-reduced.sh [your-openai-api-key]

set -e

echo "🚀 Deploying News Summarizer with Ollama (Mistral 7B) - Reduced Memory"
echo "======================================================================"
echo "⚠️  This uses reduced memory settings for 8GB laptops"
echo ""

# Check if OpenAI API key is provided
if [ -z "$1" ]; then
    echo "⚠️  Warning: OpenAI API key not provided"
    echo "   Ollama will be primary, but OpenAI fallback won't work"
    echo "   Usage: ./k8s/deploy-local-ollama-reduced.sh YOUR_OPENAI_API_KEY"
    OPENAI_KEY=""
else
    OPENAI_KEY=$1
fi

# Check if minikube is running
if ! minikube status &> /dev/null; then
    echo "❌ Error: Minikube is not running"
    echo "Start minikube with: minikube start --memory=6144 --cpus=3"
    exit 1
fi

echo "✅ Minikube is running"
echo ""

# Set kubectl context to minikube
kubectl config use-context minikube

# Step 1: Create secret (if OpenAI key provided)
if [ -n "$OPENAI_KEY" ]; then
    echo "📝 Creating Kubernetes secret..."
    kubectl create secret generic newssummariser-secrets \
        --from-literal=openai-api-key="$OPENAI_KEY" \
        --dry-run=client -o yaml | kubectl apply -f -
fi

# Step 2: Apply ConfigMap
echo "📝 Applying ConfigMap..."
kubectl apply -f k8s/configmap.yaml

# Step 3: Deploy Ollama (reduced memory version)
echo "📦 Deploying Ollama (reduced memory - 3GB)..."
kubectl apply -f k8s/ollama-deployment-local.yaml

echo "⏳ Waiting for Ollama to be ready..."
kubectl wait --for=condition=available deployment/ollama --timeout=300s || {
    echo "⚠️  Ollama taking longer than expected, continuing..."
}

# Step 4: Pull Mistral model (using init job)
echo "📥 Pulling Mistral 7B model (this may take 5-10 minutes)..."
kubectl apply -f k8s/init-ollama-model.yaml

echo "⏳ Waiting for model to download..."
kubectl wait --for=condition=complete job/ollama-init-mistral --timeout=600s || {
    echo "⚠️  Model download taking longer, check logs:"
    echo "   kubectl logs job/ollama-init-mistral"
}

# Step 5: Deploy News Summarizer with Ollama config
echo "📦 Deploying News Summarizer..."
kubectl apply -f k8s/deployment-with-ollama.yaml

# Step 6: Apply Service (NodePort for minikube)
echo "📦 Applying Service (NodePort)..."
kubectl apply -f k8s/service-minikube.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/newssummariser --timeout=300s

# Get status
echo ""
echo "✅ Deployment completed!"
echo ""
echo "📊 Status:"
echo ""
echo "Ollama Pods:"
kubectl get pods -l app=ollama
echo ""
echo "News Summarizer Pods:"
kubectl get pods -l app=newssummariser
echo ""
echo "Services:"
kubectl get svc | grep -E "ollama|newssummariser"
echo ""

# Show access information
MINIKUBE_IP=$(minikube ip)
echo "🌐 Access Information:"
echo ""
echo "Ollama API (internal): http://ollama-service:11434"
echo "News Summarizer:"
echo "   Streamlit UI: http://$MINIKUBE_IP:30080"
echo "   API: http://$MINIKUBE_IP:30081"
echo ""
echo "Or use port-forwarding:"
echo "   kubectl port-forward svc/newssummariser-service 8501:8501 8000:8000"
echo "   Then access: http://localhost:8501"
echo ""
echo "📝 Useful Commands:"
echo "   View Ollama logs: kubectl logs -f deployment/ollama"
echo "   View app logs: kubectl logs -f deployment/newssummariser"
echo "   Check memory usage: kubectl top pods"
echo ""

