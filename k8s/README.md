# Kubernetes Deployment Guide

## Prerequisites
- Kubernetes cluster (minikube, GKE, EKS, AKS, etc.)
- kubectl configured to access your cluster
- Docker image pushed to Docker Hub

## Setup Steps

### 1. Create Secret
First, create the secret with your OpenAI API key:

```bash
kubectl create secret generic newssummariser-secrets \
  --from-literal=openai-api-key=YOUR_OPENAI_API_KEY_HERE
```

Or edit `secret.yaml` and apply:
```bash
kubectl apply -f k8s/secret.yaml
```

### 2. Deploy Application
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### 3. Check Status
```bash
kubectl get pods
kubectl get services
kubectl get deployments
```

### 4. Access the Application
- If using LoadBalancer: Get external IP with `kubectl get svc`
- If using Ingress: Configure DNS and apply `k8s/ingress.yaml`

### 5. View Logs
```bash
kubectl logs -f deployment/newssummariser
```

### 6. Scale Deployment
```bash
kubectl scale deployment newssummariser --replicas=3
```

## Cleanup
```bash
kubectl delete -f k8s/
```

