# Production Deployment Guide
## Emotiond API v1.0.0

### Prerequisites

1. **Kubernetes Cluster** (v1.24+)
2. **Helm 3** installed
3. **kubectl** configured
4. **Domain name** (api.emotiond.ai)
5. **SSL Certificate** (managed by cert-manager)
6. **Monitoring Stack** (Prometheus + Grafana)
7. **Secret Management** (AWS Secrets Manager or HashiCorp Vault)

### Deployment Steps

#### 1. Prepare Namespace

```bash
# Create namespace
kubectl create namespace emotiond

# Set context
kubectl config set-context --current --namespace=emotiond
```

#### 2. Install Required Operators

```bash
# Install cert-manager for SSL certificates
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Install external-secrets for secret management
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets --create-namespace

# Install ingress-nginx
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace
```

#### 3. Configure Secrets

```bash
# Create secret template (replace with actual values)
kubectl apply -f deploy/production-secrets.yaml

# Or use external secrets
# Configure AWS Secrets Manager secret: emotiond/api/production
# With keys: jwt-secret, database-url, redis-url, api-keys
```

#### 4. Deploy Application

```bash
# Option 1: Using raw Kubernetes manifests
kubectl apply -f deploy/production-deployment.yaml

# Option 2: Using Helm (recommended)
helm repo add emotiond https://charts.emotiond.ai
helm install emotiond-api emotiond/emotiond-api -f deploy/production-values.yaml -n emotiond
```

#### 5. Verify Deployment

```bash
# Check pod status
kubectl get pods -l app=emotiond-api

# Check service status
kubectl get svc emotiond-api-service

# Check ingress status
kubectl get ingress emotiond-api-ingress

# Check application health
kubectl port-forward svc/emotiond-api-service 8080:80
curl http://localhost:8080/health
```

#### 6. Configure Monitoring

```bash
# Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

# Apply ServiceMonitor
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: emotiond-api-monitor
  namespace: emotiond
spec:
  selector:
    matchLabels:
      app: emotiond-api-service
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
EOF

# Check Prometheus targets
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090
# Access http://localhost:9090/targets
```

#### 7. Setup Alerting

```bash
# Apply PrometheusRule
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: emotiond-api-rules
  namespace: emotiond
spec:
  groups:
  - name: emotiond-api
    rules:
    - alert: EmotiondAPIHighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Emotiond API high error rate"
        description: "Error rate is {{ $value }} errors per second"
EOF
```

### Configuration Details

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Deployment environment | `production` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `JWT_SECRET_KEY` | JWT signing secret | Required |
| `DATABASE_URL` | PostgreSQL connection | Required |
| `REDIS_URL` | Redis connection | Required |
| `WORKERS` | Number of worker processes | `4` |
| `MAX_CONNECTIONS` | Max concurrent connections | `1000` |

#### Resource Limits

| Resource | Request | Limit |
|----------|---------|-------|
| CPU | 250m | 500m |
| Memory | 512Mi | 1Gi |

#### Autoscaling

- **Min Replicas**: 3
- **Max Replicas**: 10
- **CPU Target**: 70%
- **Memory Target**: 80%

#### Rate Limiting

- **Requests per minute**: 100
- **Burst size**: 20
- **Concurrent connections**: 50

### Security Features

1. **Network Policies**: Restrict pod communication
2. **Pod Security Policies**: Enforce security contexts
3. **RBAC**: Role-based access control
4. **TLS Encryption**: End-to-end encryption
5. **Secret Management**: External secret store integration
6. **Image Security**: Non-root containers, read-only filesystem
7. **Ingress Security**: Rate limiting, WAF rules

### Monitoring & Observability

1. **Metrics**: Prometheus endpoints at `/metrics`
2. **Logging**: Structured JSON logs
3. **Tracing**: Jaeger integration
4. **Health Checks**: `/health` and `/status` endpoints
5. **Alerting**: Critical and warning alerts
6. **Dashboards**: Grafana dashboards available

### Backup & Disaster Recovery

1. **Database Backups**: Daily automated backups
2. **Configuration Backup**: Git-based configuration
3. **Multi-AZ Deployment**: High availability across zones
4. **Rollback Strategy**: Blue-green deployment support

### Performance Optimization

1. **Caching**: Redis for session and data caching
2. **Connection Pooling**: Database connection optimization
3. **Load Balancing**: Nginx ingress with load balancing
4. **Resource Optimization**: Right-sized containers
5. **CDN Integration**: Static content delivery

### Troubleshooting

#### Common Issues

1. **Pod Pending**: Check resource requests/limits
2. **503 Errors**: Check ingress and service configuration
3. **High Latency**: Check resource utilization and scaling
4. **Authentication Issues**: Verify JWT secret and configuration

#### Debug Commands

```bash
# Check pod logs
kubectl logs -f deployment/emotiond-api-production

# Debug pod
kubectl exec -it deployment/emotiond-api-production -- /bin/bash

# Check events
kubectl get events -n emotiond --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -l app=emotiond-api

# Port forward for debugging
kubectl port-forward svc/emotiond-api-service 8080:80
```

### Maintenance

#### Rolling Updates

```bash
# Update image
kubectl set image deployment/emotiond-api-production emotiond-api=emotiond/api:v1.0.1

# Check rollout status
kubectl rollout status deployment/emotiond-api-production

# Rollback if needed
kubectl rollout undo deployment/emotiond-api-production
```

#### Scaling

```bash
# Manual scaling
kubectl scale deployment emotiond-api-production --replicas=5

# Check HPA status
kubectl get hpa emotiond-api-hpa
```

### Production Checklist

- [ ] Namespace created
- [ ] SSL certificate configured
- [ ] Secrets configured
- [ ] Application deployed
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Alerting rules active
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Backup strategy verified
- [ ] Documentation updated
- [ ] Team training completed

### Support Contacts

- **DevOps Team**: devops@emotiond.ai
- **Security Team**: security@emotiond.ai
- **On-call Engineer**: +1-555-0123
- **Emergency Channel**: #emotiond-alerts

### Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0.0 | 2026-03-02 | Initial production release |