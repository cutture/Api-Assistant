# Production Readiness Checklist

Use this checklist to ensure your API Integration Assistant deployment is production-ready.

## Pre-Deployment Checklist

### ✅ Code Quality & Testing

- [ ] **All tests passing** (`pytest` shows 458+ passing tests)
  ```bash
  pytest -v
  # Expected: 458 passed
  ```

- [ ] **Code linting** (no critical issues)
  ```bash
  ruff check src/
  black --check src/
  mypy src/
  ```

- [ ] **Security audit** (no high/critical vulnerabilities)
  ```bash
  pip-audit
  # Or: safety check
  ```

- [ ] **Docker image builds successfully**
  ```bash
  docker build -t api-assistant .
  ```

- [ ] **Docker image scanned for vulnerabilities**
  ```bash
  docker scan api-assistant:latest
  # Or: trivy image api-assistant:latest
  ```

### ✅ Configuration

- [ ] **Environment variables configured** (`.env.production` created)
  - [ ] `LLM_PROVIDER=groq`
  - [ ] `GROQ_API_KEY` set and valid
  - [ ] `ENVIRONMENT=production`
  - [ ] `LOG_LEVEL=info`
  - [ ] `DEBUG=false`

- [ ] **Security settings configured**
  - [ ] `MAX_FILE_SIZE_MB` set appropriately
  - [ ] `ALLOWED_FILE_TYPES` restricted
  - [ ] `RATE_LIMIT_REQUESTS_PER_MINUTE` configured
  - [ ] `RATE_LIMIT_BURST` configured

- [ ] **Performance settings optimized**
  - [ ] `EMBEDDING_CACHE_SIZE` configured
  - [ ] `EMBEDDING_CACHE_TTL` configured
  - [ ] `QUERY_CACHE_SIZE` configured
  - [ ] `QUERY_CACHE_TTL` configured

- [ ] **Secrets management** (no secrets in code/git)
  - [ ] API keys stored in secret manager (AWS Secrets Manager, GCP Secret Manager, etc.)
  - [ ] `.env` files in `.gitignore`
  - [ ] No hardcoded credentials

### ✅ Infrastructure

- [ ] **Cloud provider account** set up and configured
  - Provider: ________________ (AWS / GCP / Azure / DigitalOcean)
  - Region: ________________

- [ ] **Container registry** created and accessible
  - Registry URL: ________________

- [ ] **Persistent storage** configured for ChromaDB
  - [ ] Volume/filesystem created
  - [ ] Backup strategy defined
  - [ ] Access permissions configured

- [ ] **Network configuration**
  - [ ] VPC/network created (if applicable)
  - [ ] Subnets configured
  - [ ] Security groups/firewall rules set up
  - [ ] Only necessary ports open (80, 443)

- [ ] **Load balancer** configured (if multi-instance)
  - [ ] Health checks enabled
  - [ ] SSL/TLS termination configured
  - [ ] Target group/backend service configured

### ✅ Domain & SSL/TLS

- [ ] **Domain name** registered and configured
  - Domain: ________________

- [ ] **DNS records** created
  - [ ] A record or CNAME pointing to deployment
  - [ ] DNS propagation verified (`nslookup`, `dig`)

- [ ] **SSL/TLS certificate** obtained and installed
  - [ ] Certificate from Let's Encrypt, ACM, or other CA
  - [ ] Certificate auto-renewal configured
  - [ ] HTTPS redirects from HTTP
  - [ ] SSL Labs test: Grade A or better (https://www.ssllabs.com/ssltest/)

- [ ] **Security headers** configured
  ```nginx
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
  add_header X-Frame-Options "SAMEORIGIN" always;
  add_header X-Content-Type-Options "nosniff" always;
  add_header X-XSS-Protection "1; mode=block" always;
  ```

### ✅ Monitoring & Logging

- [ ] **Health check endpoint** accessible
  - URL: `https://your-domain.com/_stcore/health`
  - Returns: `{"status": "ok"}`

- [ ] **Application logging** configured
  - [ ] Logs writing to persistent location
  - [ ] Log rotation enabled (10MB max, 5 backups)
  - [ ] Log level set to `info` or `warning` (not `debug`)

- [ ] **Log aggregation** set up
  - [ ] CloudWatch / Cloud Logging / Azure Monitor configured
  - [ ] OR self-hosted ELK/Loki stack running
  - [ ] Log retention policy defined

- [ ] **Monitoring dashboards** created
  - [ ] CPU usage monitoring
  - [ ] Memory usage monitoring
  - [ ] Request rate monitoring
  - [ ] Error rate monitoring
  - [ ] Response time monitoring (P50, P95, P99)

- [ ] **Alerting** configured
  - [ ] High error rate alert (> 1%)
  - [ ] High response time alert (P95 > 30s)
  - [ ] High CPU usage alert (> 80% for 5min)
  - [ ] High memory usage alert (> 90%)
  - [ ] Disk space alert (> 85%)
  - [ ] Health check failure alert
  - [ ] Alert delivery method configured (email, Slack, PagerDuty, etc.)

- [ ] **Uptime monitoring** configured
  - [ ] External uptime monitor (UptimeRobot, Pingdom, etc.)
  - [ ] Check interval: 1-5 minutes
  - [ ] Alert on downtime

### ✅ Backup & Disaster Recovery

- [ ] **Backup strategy** defined and implemented
  - [ ] ChromaDB data backed up daily
  - [ ] Backup retention: 30 days minimum
  - [ ] Backups stored in separate location (S3, GCS, Azure Blob)
  - [ ] Backup script automated (cron job or cloud scheduler)

- [ ] **Backup restoration tested**
  - [ ] Performed test restore from backup
  - [ ] Verified data integrity after restore
  - [ ] Documented restore procedure

- [ ] **Disaster recovery plan** documented
  - [ ] RTO (Recovery Time Objective) defined: ________
  - [ ] RPO (Recovery Point Objective) defined: ________
  - [ ] DR runbook created
  - [ ] Team trained on DR procedures

- [ ] **Infrastructure as Code** (recommended)
  - [ ] Terraform/CloudFormation/ARM templates created
  - [ ] IaC stored in version control
  - [ ] Can rebuild infrastructure from code

### ✅ Security

- [ ] **Application security**
  - [ ] Input validation enabled (SQL injection, XSS, command injection)
  - [ ] File upload restrictions configured
  - [ ] Rate limiting enabled (60 req/min default)
  - [ ] CORS configured appropriately
  - [ ] XSRF protection enabled

- [ ] **Network security**
  - [ ] Firewall/security groups configured (minimal open ports)
  - [ ] DDoS protection enabled (cloud provider or Cloudflare)
  - [ ] WAF (Web Application Firewall) configured (optional but recommended)

- [ ] **Container security**
  - [ ] Running as non-root user (uid 1000)
  - [ ] Read-only filesystem where possible
  - [ ] Resource limits configured (CPU, memory)
  - [ ] Security scanning enabled

- [ ] **Access control**
  - [ ] SSH access restricted to specific IPs (if applicable)
  - [ ] Cloud console access restricted (MFA enabled)
  - [ ] Principle of least privilege applied
  - [ ] Service accounts used (not personal accounts)

- [ ] **Secrets rotation**
  - [ ] API keys rotation schedule defined
  - [ ] SSL/TLS certificate renewal automated
  - [ ] Database credentials rotation (if applicable)

- [ ] **Compliance** (if applicable)
  - [ ] GDPR compliance reviewed
  - [ ] SOC 2 requirements addressed
  - [ ] Data encryption at rest and in transit
  - [ ] Audit logging enabled

### ✅ Performance

- [ ] **Load testing** performed
  - [ ] Tested with expected concurrent users
  - [ ] Identified maximum throughput
  - [ ] Response times under load acceptable (< 30s)
  - [ ] No memory leaks detected

- [ ] **Caching** configured and tested
  - [ ] Embedding cache hit rate measured (expect 70-90%)
  - [ ] Query cache hit rate measured (expect 50-80% for similar queries)
  - [ ] Cache TTLs appropriate for use case

- [ ] **Resource limits** configured
  - [ ] CPU limits set appropriately
  - [ ] Memory limits set appropriately
  - [ ] Disk space monitored

- [ ] **Auto-scaling** configured (for variable load)
  - [ ] Minimum instances: ________
  - [ ] Maximum instances: ________
  - [ ] Scaling trigger (CPU > 70%, memory > 80%, etc.)

### ✅ Cost Management

- [ ] **Budget alerts** configured
  - [ ] Monthly budget defined: $________
  - [ ] Alert at 50% of budget
  - [ ] Alert at 80% of budget
  - [ ] Alert at 100% of budget

- [ ] **Cost optimization** reviewed
  - [ ] Right-sized instances (not over-provisioned)
  - [ ] Spot/preemptible instances considered
  - [ ] Reserved instances considered (for stable workloads)
  - [ ] Auto-scaling configured to reduce costs during low traffic

- [ ] **Resource cleanup** automated
  - [ ] Old logs deleted automatically
  - [ ] Old backups deleted automatically
  - [ ] Unused resources identified and removed

### ✅ Documentation

- [ ] **Deployment documentation** complete
  - [ ] Architecture diagram created
  - [ ] Deployment steps documented
  - [ ] Configuration explained
  - [ ] Troubleshooting guide available

- [ ] **Runbooks** created
  - [ ] Deployment runbook
  - [ ] Rollback runbook
  - [ ] Disaster recovery runbook
  - [ ] Common issues and solutions

- [ ] **Team training**
  - [ ] Team trained on deployment procedures
  - [ ] On-call rotation defined
  - [ ] Escalation procedures documented
  - [ ] Contact information current

### ✅ Legal & Compliance

- [ ] **Terms of Service** (if public-facing)
- [ ] **Privacy Policy** (if collecting user data)
- [ ] **Data retention policy** defined
- [ ] **License compliance** (all dependencies reviewed)

---

## Go-Live Checklist

Complete these steps immediately before and after deployment:

### Before Deployment

- [ ] **Schedule deployment** (prefer low-traffic times)
  - Date/Time: ________________

- [ ] **Notify stakeholders** of deployment
  - [ ] Users notified of potential downtime
  - [ ] Team available for support
  - [ ] On-call engineer assigned

- [ ] **Create rollback plan**
  - [ ] Previous version tagged in git
  - [ ] Rollback steps documented
  - [ ] Rollback tested in staging

- [ ] **Final testing in staging**
  - [ ] Smoke tests passed
  - [ ] Integration tests passed
  - [ ] Performance tests passed

### During Deployment

- [ ] **Follow deployment runbook**
- [ ] **Monitor deployment progress**
  - [ ] Container startup successful
  - [ ] Health checks passing
  - [ ] No errors in logs

- [ ] **Verify DNS resolution**
  ```bash
  nslookup your-domain.com
  curl https://your-domain.com/_stcore/health
  ```

### After Deployment

- [ ] **Smoke tests** in production
  - [ ] Application loads correctly
  - [ ] File upload works
  - [ ] Query processing works
  - [ ] Agent workflow works

- [ ] **Monitor key metrics** (first 24 hours)
  - [ ] Error rate < 1%
  - [ ] Response time P95 < 30s
  - [ ] CPU usage < 70%
  - [ ] Memory usage < 80%
  - [ ] No critical errors in logs

- [ ] **Verify monitoring & alerting**
  - [ ] Alerts configured and working
  - [ ] Dashboards showing data
  - [ ] Logs being collected

- [ ] **User acceptance testing**
  - [ ] Get feedback from initial users
  - [ ] Monitor for issues
  - [ ] Address critical issues immediately

- [ ] **Update documentation**
  - [ ] Production URLs documented
  - [ ] Access instructions updated
  - [ ] Any deployment-specific notes added

---

## Post-Deployment Tasks (Week 1)

- [ ] **Day 1**: Monitor closely for any issues
- [ ] **Day 2**: Review error logs and metrics
- [ ] **Day 3**: Optimize based on real-world usage patterns
- [ ] **Day 4**: Review cost and adjust resources if needed
- [ ] **Day 5**: Collect user feedback
- [ ] **Day 7**: Perform first backup restoration test

---

## Ongoing Maintenance

### Daily
- [ ] Review error logs
- [ ] Check monitoring dashboards
- [ ] Verify backups completed successfully

### Weekly
- [ ] Review performance metrics
- [ ] Check for security updates
- [ ] Review cost reports
- [ ] Analyze user feedback

### Monthly
- [ ] Update dependencies (`pip-audit`, update packages)
- [ ] Review and optimize costs
- [ ] Test disaster recovery procedures
- [ ] Review and update documentation
- [ ] Conduct security review
- [ ] Rotate secrets (if applicable)

### Quarterly
- [ ] Perform load testing
- [ ] Review and update disaster recovery plan
- [ ] Review scaling strategy
- [ ] Conduct security audit
- [ ] Review compliance requirements

---

## Sign-Off

**Deployment Lead**: ________________ Date: ________

**Security Review**: ________________ Date: ________

**Infrastructure Review**: ________________ Date: ________

**Final Approval**: ________________ Date: ________

---

## Notes

Use this section for deployment-specific notes:

```
_____________________________________________________________________________

_____________________________________________________________________________

_____________________________________________________________________________

_____________________________________________________________________________

_____________________________________________________________________________
```

---

## Troubleshooting Quick Reference

### Common Pre-Deployment Issues

1. **Tests failing**
   - Run `pytest -v` to see which tests are failing
   - Check that all dependencies are installed
   - Verify environment variables are set

2. **Docker build fails**
   - Check Dockerfile syntax
   - Verify all files referenced exist
   - Check for network issues (can't download packages)

3. **Cannot connect to deployed service**
   - Verify security group/firewall allows traffic
   - Check that service is running (`docker ps`)
   - Verify DNS records are correct
   - Check SSL certificate is valid

4. **High memory usage**
   - Reduce cache sizes in configuration
   - Check for memory leaks (monitor over time)
   - Increase instance memory

5. **Slow response times**
   - Verify caching is enabled
   - Check Groq API key is valid and has quota
   - Monitor Groq API rate limits
   - Consider upgrading instance size

---

## Related Documentation

- [Production Deployment Guide](PRODUCTION_DEPLOYMENT.md)
- [Docker Deployment](DOCKER_DEPLOYMENT.md)
- [Monitoring Guide](docs/MONITORING_GUIDE.md)
- [README](README.md)

---

**Version**: 1.0.0
**Last Updated**: 2025-12-27
