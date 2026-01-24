# Kubernetes Deployment Guide

## Prerequisites
- Kubernetes cluster (GKE, EKS, AKS, minikube, or any other)
- kubectl configured to access your cluster
- Docker image pushed to Docker Hub (done via CI/CD)

## Quick Start

### Option 1: Using Deployment Script (Recommended)

```bash
# Make script executable (if not already)
chmod +x k8s/deploy.sh

# Deploy with your OpenAI API key
./k8s/deploy.sh YOUR_OPENAI_API_KEY
```

The script will:
- Create Kubernetes secret with your API key
- Deploy all resources
- Wait for deployment to be ready
- Show you how to access the application

### Option 2: Manual Deployment

#### Step 1: Create Secret
```bash
kubectl create secret generic newssummariser-secrets \
  --from-literal=openai-api-key=YOUR_OPENAI_API_KEY_HERE
```

Or edit `secret.yaml` and apply:
```bash
# Edit secret.yaml with your API key
kubectl apply -f k8s/secret.yaml
```

#### Step 2: Deploy Application
```bash
# Apply all manifests
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Optional: Enable auto-scaling
kubectl apply -f k8s/hpa.yaml
```

#### Step 3: Check Status
```bash
# Check deployment status
kubectl get deployment newssummariser

# Check pods
kubectl get pods -l app=newssummariser

# Check services
kubectl get svc newssummariser-service

# View logs
kubectl logs -f deployment/newssummariser
```

## Accessing the Application

### LoadBalancer (Cloud Providers)
```bash
# Get external IP
kubectl get svc newssummariser-service

# Access at:
# Streamlit UI: http://<EXTERNAL_IP>
# API: http://<EXTERNAL_IP>:8000
```

### Port Forwarding (Local/Testing)
```bash
# Forward Streamlit port
kubectl port-forward svc/newssummariser-service 8501:8501

# Access at: http://localhost:8501
```

### Ingress (Production)
1. Install an Ingress Controller (e.g., NGINX Ingress)
2. Update `k8s/ingress.yaml` with your domain
3. Apply: `kubectl apply -f k8s/ingress.yaml`

## Scaling

### Manual Scaling
```bash
# Scale to 3 replicas
kubectl scale deployment newssummariser --replicas=3
```

### Auto-Scaling (HPA)
```bash
# Apply Horizontal Pod Autoscaler
kubectl apply -f k8s/hpa.yaml

# Check HPA status
kubectl get hpa newssummariser-hpa
```

## Updating Deployment

### Update Image
```bash
# Trigger rolling update
kubectl rollout restart deployment/newssummariser

# Or update image tag in deployment.yaml and apply
kubectl apply -f k8s/deployment.yaml
```

### Update Configuration
```bash
# Edit configmap
kubectl edit configmap newssummariser-config

# Restart pods to pick up changes
kubectl rollout restart deployment/newssummariser
```

## Monitoring

### View Logs
```bash
# All pods
kubectl logs -f -l app=newssummariser

# Specific pod
kubectl logs -f <pod-name>

# Previous container (if crashed)
kubectl logs -f <pod-name> --previous
```

### Check Resource Usage
```bash
# Pod resource usage
kubectl top pods -l app=newssummariser

# Node resource usage
kubectl top nodes
```

### Describe Resources
```bash
# Describe deployment
kubectl describe deployment newssummariser

# Describe pod
kubectl describe pod <pod-name>

# Describe service
kubectl describe svc newssummariser-service
```

## Troubleshooting

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

# Check service details
kubectl describe svc newssummariser-service

# Verify pods are running
kubectl get pods -l app=newssummariser
```

### Secret Issues
```bash
# Verify secret exists
kubectl get secret newssummariser-secrets

# Check secret (base64 encoded)
kubectl get secret newssummariser-secrets -o yaml

# Recreate if needed
kubectl delete secret newssummariser-secrets
kubectl create secret generic newssummariser-secrets \
  --from-literal=openai-api-key=YOUR_API_KEY
```

## Cleanup

### Delete All Resources
```bash
kubectl delete -f k8s/
```

### Delete Specific Resource
```bash
kubectl delete -f k8s/deployment.yaml
kubectl delete -f k8s/service.yaml
```

## Production Considerations

1. **Resource Limits**: Adjust in `deployment.yaml` based on your needs
2. **Replicas**: Start with 2-3 replicas for high availability
3. **Health Checks**: Already configured in deployment
4. **Secrets Management**: Consider using external secret management (e.g., AWS Secrets Manager, Azure Key Vault)
5. **Monitoring**: Set up Prometheus/Grafana for monitoring
6. **Logging**: Consider centralized logging (e.g., ELK stack, CloudWatch)
7. **SSL/TLS**: Use Ingress with cert-manager for HTTPS
8. **Backup**: Regular backups of configurations and secrets

## Environment-Specific Configurations

### Development (minikube)
```bash
# Use NodePort instead of LoadBalancer
kubectl patch svc newssummariser-service -p '{"spec":{"type":"NodePort"}}'
```

### Production (Cloud)
- Use LoadBalancer or Ingress
- Enable HPA for auto-scaling
- Set appropriate resource limits
- Enable monitoring and alerting
