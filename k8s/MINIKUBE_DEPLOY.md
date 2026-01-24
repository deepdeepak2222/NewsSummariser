# Minikube Deployment Guide

## Prerequisites
- ✅ Minikube is running (`minikube status`)
- ✅ kubectl is configured (`kubectl config current-context` shows `minikube`)
- ✅ Docker image is pushed to Docker Hub (done via CI/CD)

## Quick Deployment

### Option 1: Using Deployment Script (Easiest)

```bash
# From project root
./k8s/deploy-minikube.sh YOUR_OPENAI_API_KEY
```

### Option 2: Manual Deployment

```bash
# 1. Create secret
kubectl create secret generic newssummariser-secrets \
  --from-literal=openai-api-key=YOUR_OPENAI_API_KEY

# 2. Deploy resources
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service-minikube.yaml

# 3. Check status
kubectl get pods -l app=newssummariser
kubectl get svc newssummariser-service
```

## Accessing the Application

### Method 1: Using minikube service (Opens browser automatically)
```bash
minikube service newssummariser-service
```

### Method 2: Get URL directly
```bash
# Get minikube IP
minikube ip

# Access at:
# Streamlit UI: http://$(minikube ip):30080
# API: http://$(minikube ip):30081
```

### Method 3: Port Forwarding
```bash
kubectl port-forward svc/newssummariser-service 8501:8501
# Access at: http://localhost:8501
```

## Verify Deployment

```bash
# Check pods are running
kubectl get pods -l app=newssummariser

# Check service
kubectl get svc newssummariser-service

# View logs
kubectl logs -f deployment/newssummariser

# Describe pod if issues
kubectl describe pod <pod-name>
```

## Troubleshooting

### Image Pull Errors
If minikube can't pull from Docker Hub:
```bash
# Enable minikube to use Docker Hub
eval $(minikube docker-env)

# Or pull image into minikube
minikube image pull deepdeepak2222/newssummariser:latest
```

### Pods Not Starting
```bash
# Check pod status
kubectl get pods -l app=newssummariser

# Describe pod for events
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>
```

### Service Not Accessible
```bash
# Check service endpoints
kubectl get endpoints newssummariser-service

# Verify pods are running
kubectl get pods -l app=newssummariser

# Check service details
kubectl describe svc newssummariser-service
```

## Cleanup

```bash
# Delete all resources
kubectl delete -f k8s/

# Or delete individually
kubectl delete deployment newssummariser
kubectl delete svc newssummariser-service
kubectl delete secret newssummariser-secrets
kubectl delete configmap newssummariser-config
```

