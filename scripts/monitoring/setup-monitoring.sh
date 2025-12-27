#!/bin/bash
# Monitoring Setup Script
# Sets up basic monitoring and alerting for the API Integration Assistant

set -e

PROVIDER=${1:-""}

echo "📊 API Integration Assistant - Monitoring Setup"
echo ""

if [ -z "$PROVIDER" ]; then
    echo "Usage: $0 <provider>"
    echo ""
    echo "Supported providers:"
    echo "  aws        - AWS CloudWatch"
    echo "  gcp        - GCP Cloud Monitoring"
    echo "  azure      - Azure Monitor"
    echo "  prometheus - Prometheus + Grafana (self-hosted)"
    echo ""
    exit 1
fi

case $PROVIDER in
    aws)
        echo "Setting up AWS CloudWatch monitoring..."

        # Create log group
        aws logs create-log-group \
            --log-group-name /ecs/api-assistant \
            --region ${AWS_REGION:-us-east-1} || true

        # Create CloudWatch dashboard
        cat > dashboard.json <<'EOF'
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ECS", "CPUUtilization", {"stat": "Average"}],
          [".", "MemoryUtilization", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "ECS Resource Utilization"
      }
    }
  ]
}
EOF

        aws cloudwatch put-dashboard \
            --dashboard-name api-assistant \
            --dashboard-body file://dashboard.json \
            --region ${AWS_REGION:-us-east-1}

        rm dashboard.json

        # Create SNS topic for alerts
        TOPIC_ARN=$(aws sns create-topic \
            --name api-assistant-alerts \
            --region ${AWS_REGION:-us-east-1} \
            --query TopicArn \
            --output text)

        echo "✅ Created SNS topic: $TOPIC_ARN"
        echo ""
        echo "💡 Subscribe to alerts:"
        echo "   aws sns subscribe --topic-arn $TOPIC_ARN --protocol email --notification-endpoint your-email@example.com"

        # Create CloudWatch alarms
        echo "Creating CloudWatch alarms..."

        aws cloudwatch put-metric-alarm \
            --alarm-name api-assistant-high-cpu \
            --alarm-description "CPU > 80% for 5 minutes" \
            --metric-name CPUUtilization \
            --namespace AWS/ECS \
            --statistic Average \
            --period 300 \
            --threshold 80 \
            --comparison-operator GreaterThanThreshold \
            --evaluation-periods 1 \
            --alarm-actions $TOPIC_ARN \
            --region ${AWS_REGION:-us-east-1}

        aws cloudwatch put-metric-alarm \
            --alarm-name api-assistant-high-memory \
            --alarm-description "Memory > 90%" \
            --metric-name MemoryUtilization \
            --namespace AWS/ECS \
            --statistic Average \
            --period 300 \
            --threshold 90 \
            --comparison-operator GreaterThanThreshold \
            --evaluation-periods 1 \
            --alarm-actions $TOPIC_ARN \
            --region ${AWS_REGION:-us-east-1}

        echo "✅ AWS CloudWatch monitoring setup complete!"
        ;;

    gcp)
        echo "Setting up GCP Cloud Monitoring..."

        PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}

        # Create notification channel
        echo "Creating notification channel..."
        gcloud alpha monitoring channels create \
            --display-name="API Assistant Alerts" \
            --type=email \
            --channel-labels=email_address=your-email@example.com \
            --project=$PROJECT_ID || true

        # Create alert policies (requires gcloud alpha)
        cat > alert-policy.yaml <<'EOF'
displayName: "High CPU Usage"
conditions:
  - displayName: "CPU > 80%"
    conditionThreshold:
      filter: 'resource.type = "cloud_run_revision" AND metric.type = "run.googleapis.com/container/cpu/utilizations"'
      comparison: COMPARISON_GT
      thresholdValue: 0.8
      duration: 300s
EOF

        gcloud alpha monitoring policies create --policy-from-file=alert-policy.yaml --project=$PROJECT_ID || true
        rm alert-policy.yaml

        echo "✅ GCP Cloud Monitoring setup complete!"
        echo ""
        echo "💡 View monitoring:"
        echo "   https://console.cloud.google.com/monitoring?project=$PROJECT_ID"
        ;;

    azure)
        echo "Setting up Azure Monitor..."

        RESOURCE_GROUP=${AZURE_RESOURCE_GROUP:-"api-assistant-rg"}

        # Create action group
        az monitor action-group create \
            --name api-assistant-alerts \
            --resource-group $RESOURCE_GROUP \
            --short-name api-alert || true

        # Add email receiver
        echo "Please enter email for alerts:"
        read EMAIL

        az monitor action-group update \
            --name api-assistant-alerts \
            --resource-group $RESOURCE_GROUP \
            --add-action email api-admin $EMAIL

        echo "✅ Azure Monitor setup complete!"
        echo ""
        echo "💡 View monitoring:"
        echo "   https://portal.azure.com/#blade/Microsoft_Azure_Monitoring/AzureMonitoringBrowseBlade"
        ;;

    prometheus)
        echo "Setting up Prometheus + Grafana..."

        # Create docker-compose for monitoring stack
        cat > docker-compose.monitoring.yml <<'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"
    restart: unless-stopped

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
EOF

        # Create Prometheus configuration
        cat > prometheus.yml <<'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  - job_name: 'api-assistant'
    static_configs:
      - targets: ['api-assistant:8501']
    metrics_path: '/_stcore/health'
EOF

        # Start monitoring stack
        docker-compose -f docker-compose.monitoring.yml up -d

        echo "✅ Prometheus + Grafana setup complete!"
        echo ""
        echo "🌐 Access URLs:"
        echo "   Prometheus: http://localhost:9090"
        echo "   Grafana:    http://localhost:3000 (admin/admin)"
        echo ""
        echo "💡 Next steps:"
        echo "   1. Add Prometheus as data source in Grafana"
        echo "   2. Import dashboard: https://grafana.com/grafana/dashboards/893"
        echo "   3. Create alerts in Grafana"
        ;;

    *)
        echo "❌ Unknown provider: $PROVIDER"
        exit 1
        ;;
esac

echo ""
echo "🎉 Monitoring setup complete!"
