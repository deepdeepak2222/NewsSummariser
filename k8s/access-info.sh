#!/bin/bash

# Quick access information for deployed application

MINIKUBE_IP=$(minikube ip 2>/dev/null)

if [ -z "$MINIKUBE_IP" ]; then
    echo "❌ Minikube is not running"
    exit 1
fi

echo "✅ News Summarizer is deployed and running!"
echo ""
echo "📊 Deployment Status:"
kubectl get pods -l app=newssummariser
echo ""
echo "🌐 Access the application:"
echo ""
echo "Option 1: Using minikube service (opens browser automatically)"
echo "   Run: minikube service newssummariser-service"
echo ""
echo "Option 2: Direct access via NodePort"
echo "   Streamlit UI: http://$MINIKUBE_IP:30080"
echo "   API: http://$MINIKUBE_IP:30081"
echo "   API Docs: http://$MINIKUBE_IP:30081/docs"
echo ""
echo "Option 3: Port forwarding (for localhost access)"
echo "   Run: kubectl port-forward svc/newssummariser-service 8501:8501"
echo "   Then access at: http://localhost:8501"
echo ""
echo "📝 Useful commands:"
echo "   View logs: kubectl logs -f deployment/newssummariser"
echo "   Check service: kubectl get svc newssummariser-service"
echo "   Scale: kubectl scale deployment newssummariser --replicas=3"

