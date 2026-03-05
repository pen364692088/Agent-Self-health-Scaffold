# OpenEmotion MCP Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the OpenEmotion MCP API to production and staging environments.

## 📁 File Structure

```
kubernetes/
├── namespace.yaml          # Namespace definitions
├── configmap.yaml          # Application configuration
├── secret.yaml            # Secret templates (actual secrets to be injected)
├── deployment.yaml        # Main application deployments
├── service.yaml           # Service definitions
├── ingress.yaml           # Ingress configuration for external access
├── hpa.yaml              # Horizontal Pod Autoscalers
├── networkpolicy.yaml    # Network security policies
├── servicemonitor.yaml   # Prometheus monitoring
├── deploy.sh             # Deployment script
└── README.md             # This file
```

## 🚀 Quick Deploy

### Prerequisites
- Kubernetes cluster access
- kubectl configured
- NGINX Ingress Controller (for external access)
- cert-manager (for SSL certificates)
- Prometheus Operator (optional, for monitoring)

### Deploy to Staging
```bash
./deploy.sh deploy staging
```

### Deploy to Production
```bash
./deploy.sh deploy production
```

### Check Status
```bash
# Production
./deploy.sh status production

# Staging
./deploy.sh status staging
```

### Rollback
```bash
# Production
./deploy.sh rollback production

# Staging
./deploy.sh rollback staging
```

## 🔧 Manual Deployment Steps

If you prefer to deploy manually:

1. **Create namespaces**
   ```bash
   kubectl apply -f namespace.yaml
   ```

2. **Create secrets** (replace with actual values)
   ```bash
   kubectl create secret generic openemotion-secrets \
     --from-literal=JWT_SECRET_KEY=your-jwt-secret \
     --from-literal=AWS_ACCESS_KEY_ID=your-aws-key \
     --from-literal=AWS_SECRET_ACCESS_KEY=your-aws-secret \
     -n openemotion
   ```

3. **Apply configuration**
   ```bash
   kubectl apply -f configmap.yaml -n openemotion
   ```

4. **Deploy application**
   ```bash
   kubectl apply -f deployment.yaml -n openemotion
   kubectl apply -f service.yaml -n openemotion
   ```

5. **Configure networking**
   ```bash
   kubectl apply -f ingress.yaml -n openemotion
   kubectl apply -f networkpolicy.yaml -n openemotion
   ```

6. **Enable autoscaling**
   ```bash
   kubectl apply -f hpa.yaml -n openemotion
   ```

7. **Set up monitoring** (optional)
   ```bash
   kubectl apply -f servicemonitor.yaml -n openemotion
   ```

## 🔒 Security Features

- **Network Policies**: Restrict pod-to-pod communication
- **RBAC**: Non-root user, dropped capabilities
- **TLS**: Automatic SSL certificate management
- **Rate Limiting**: 100 requests/minute per IP
- **CORS**: Configured for allowed origins

## 📊 Monitoring

The deployment includes:
- **Health Checks**: `/health` and `/ready` endpoints
- **Metrics**: Prometheus metrics at `/metrics`
- **Autoscaling**: CPU and memory-based HPA
- **Alerts**: Configured in Prometheus rules

## 🌐 URLs

### Production
- API: `https://api.emotiond.ai`
- Admin: `https://emotiond.openclaw.ai`

### Staging
- API: `https://staging-api.emotiond.ai`

## ⚙️ Configuration

### Environment Variables
Key configuration options in `configmap.yaml`:

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | API bind address | `0.0.0.0` |
| `API_PORT` | API port | `8000` |
| `MODEL_NAME` | Ollama model | `qwen2.5:3b-instruct` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | Rate limit | `100` |

### Resource Limits
- **Production**: 512Mi-1Gi memory, 250m-500m CPU
- **Staging**: 256Mi-512Mi memory, 100m-250m CPU

## 🔍 Troubleshooting

### Check pod logs
```bash
kubectl logs -n openemotion -l app=openemotion -f
```

### Debug connectivity
```bash
kubectl port-forward -n openemotion svc/openemotion-api-service 8000:80
```

### Check events
```bash
kubectl get events -n openemotion --sort-by='.lastTimestamp'
```

## 📝 Notes

- The deployment uses rolling updates with zero downtime
- Secrets must be created manually before first deployment
- Ingress requires domain names to be configured in DNS
- HPA will scale between 3-10 replicas in production
- Network policies restrict traffic to essential sources only

## 🚨 Production Deployment Checklist

Before deploying to production:

- [ ] DNS records configured (`api.emotiond.ai`)
- [ ] SSL certificates ready (cert-manager will handle)
- [ ] Secrets created with production values
- [ ] Monitoring alerts configured
- [ ] Load testing completed
- [ ] Rollback plan tested
- [ ] Team notification sent