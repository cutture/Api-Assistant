#!/bin/bash
# Health Check Script
# Performs comprehensive health checks on the deployed application

set -e

# Configuration
APP_URL=${APP_URL:-"http://localhost:8501"}
TIMEOUT=${HEALTH_CHECK_TIMEOUT:-10}
SLACK_WEBHOOK=${SLACK_WEBHOOK_URL:-""}
EMAIL=${ALERT_EMAIL:-""}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

echo "🏥 API Integration Assistant - Health Check"
echo "   URL: $APP_URL"
echo "   Timeout: ${TIMEOUT}s"
echo ""

# Helper function for checks
check() {
    local name=$1
    local command=$2
    local critical=${3:-false}

    echo -n "Checking $name... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
        return 0
    else
        if [ "$critical" = true ]; then
            echo -e "${RED}✗ FAIL${NC}"
            ((FAILED++))
        else
            echo -e "${YELLOW}⚠ WARNING${NC}"
            ((WARNINGS++))
        fi
        return 1
    fi
}

# 1. Basic connectivity
check "HTTP connectivity" \
    "curl -f -s --connect-timeout $TIMEOUT $APP_URL/_stcore/health" \
    true

# 2. Response time
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' --connect-timeout $TIMEOUT $APP_URL/_stcore/health 2>/dev/null || echo "999")
RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc | cut -d. -f1)

echo -n "Response time... "
if [ "$RESPONSE_TIME_MS" -lt 1000 ]; then
    echo -e "${GREEN}✓ PASS${NC} (${RESPONSE_TIME_MS}ms)"
    ((PASSED++))
elif [ "$RESPONSE_TIME_MS" -lt 5000 ]; then
    echo -e "${YELLOW}⚠ WARNING${NC} (${RESPONSE_TIME_MS}ms - slower than expected)"
    ((WARNINGS++))
else
    echo -e "${RED}✗ FAIL${NC} (${RESPONSE_TIME_MS}ms - too slow!)"
    ((FAILED++))
fi

# 3. SSL certificate (if HTTPS)
if [[ $APP_URL == https://* ]]; then
    DOMAIN=$(echo $APP_URL | sed -e 's|https://||' -e 's|/.*||')

    check "SSL certificate validity" \
        "echo | timeout $TIMEOUT openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -checkend 86400" \
        false

    # Check certificate expiration
    if command -v openssl &> /dev/null; then
        EXPIRY=$(echo | timeout $TIMEOUT openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
        if [ -n "$EXPIRY" ]; then
            EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$EXPIRY" +%s 2>/dev/null)
            NOW_EPOCH=$(date +%s)
            DAYS_UNTIL_EXPIRY=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

            echo -n "SSL certificate expiration... "
            if [ "$DAYS_UNTIL_EXPIRY" -gt 30 ]; then
                echo -e "${GREEN}✓ PASS${NC} ($DAYS_UNTIL_EXPIRY days remaining)"
                ((PASSED++))
            elif [ "$DAYS_UNTIL_EXPIRY" -gt 7 ]; then
                echo -e "${YELLOW}⚠ WARNING${NC} ($DAYS_UNTIL_EXPIRY days remaining)"
                ((WARNINGS++))
            else
                echo -e "${RED}✗ FAIL${NC} (expires in $DAYS_UNTIL_EXPIRY days!)"
                ((FAILED++))
            fi
        fi
    fi
fi

# 4. Docker container status (if local)
if [ "$APP_URL" = "http://localhost:8501" ] && command -v docker &> /dev/null; then
    check "Docker container running" \
        "docker ps --format '{{.Names}}' | grep -q 'api-assistant'" \
        true

    # Check container health
    if docker ps --format '{{.Names}}' | grep -q 'api-assistant'; then
        CONTAINER_STATUS=$(docker inspect --format='{{.State.Health.Status}}' api-assistant 2>/dev/null || echo "unknown")

        echo -n "Container health status... "
        case $CONTAINER_STATUS in
            healthy)
                echo -e "${GREEN}✓ PASS${NC} (healthy)"
                ((PASSED++))
                ;;
            starting)
                echo -e "${YELLOW}⚠ WARNING${NC} (starting)"
                ((WARNINGS++))
                ;;
            unhealthy|unknown)
                echo -e "${RED}✗ FAIL${NC} ($CONTAINER_STATUS)"
                ((FAILED++))
                ;;
        esac

        # Check resource usage
        STATS=$(docker stats --no-stream --format "{{.CPUPerc}}|{{.MemPerc}}" api-assistant 2>/dev/null)
        if [ -n "$STATS" ]; then
            CPU_PERC=$(echo $STATS | cut -d'|' -f1 | sed 's/%//')
            MEM_PERC=$(echo $STATS | cut -d'|' -f2 | sed 's/%//')

            echo -n "CPU usage... "
            if (( $(echo "$CPU_PERC < 80" | bc -l) )); then
                echo -e "${GREEN}✓ PASS${NC} (${CPU_PERC}%)"
                ((PASSED++))
            elif (( $(echo "$CPU_PERC < 90" | bc -l) )); then
                echo -e "${YELLOW}⚠ WARNING${NC} (${CPU_PERC}%)"
                ((WARNINGS++))
            else
                echo -e "${RED}✗ FAIL${NC} (${CPU_PERC}% - too high!)"
                ((FAILED++))
            fi

            echo -n "Memory usage... "
            if (( $(echo "$MEM_PERC < 85" | bc -l) )); then
                echo -e "${GREEN}✓ PASS${NC} (${MEM_PERC}%)"
                ((PASSED++))
            elif (( $(echo "$MEM_PERC < 95" | bc -l) )); then
                echo -e "${YELLOW}⚠ WARNING${NC} (${MEM_PERC}%)"
                ((WARNINGS++))
            else
                echo -e "${RED}✗ FAIL${NC} (${MEM_PERC}% - too high!)"
                ((FAILED++))
            fi
        fi
    fi
fi

# 5. Disk space (if local)
if [ "$APP_URL" = "http://localhost:8501" ]; then
    DISK_USAGE=$(df -h /app/data 2>/dev/null | awk 'NR==2 {print $5}' | sed 's/%//' || echo "0")

    echo -n "Disk space... "
    if [ "$DISK_USAGE" -lt 70 ]; then
        echo -e "${GREEN}✓ PASS${NC} (${DISK_USAGE}% used)"
        ((PASSED++))
    elif [ "$DISK_USAGE" -lt 85 ]; then
        echo -e "${YELLOW}⚠ WARNING${NC} (${DISK_USAGE}% used)"
        ((WARNINGS++))
    else
        echo -e "${RED}✗ FAIL${NC} (${DISK_USAGE}% used - too high!)"
        ((FAILED++))
    fi
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary:"
echo -e "  ${GREEN}Passed:${NC}   $PASSED"
echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "  ${RED}Failed:${NC}   $FAILED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Overall status
TOTAL=$((PASSED + WARNINGS + FAILED))
if [ $FAILED -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    EXIT_CODE=0
elif [ $FAILED -eq 0 ]; then
    echo -e "${YELLOW}⚠ Some warnings detected${NC}"
    EXIT_CODE=0
else
    echo -e "${RED}✗ Health check failed!${NC}"
    EXIT_CODE=1
fi

# Send alerts if configured
if [ $EXIT_CODE -ne 0 ] || [ $WARNINGS -gt 0 ]; then
    MESSAGE="Health check on $APP_URL: $PASSED passed, $WARNINGS warnings, $FAILED failed"

    # Slack notification
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🏥 $MESSAGE\"}" \
            "$SLACK_WEBHOOK" 2>/dev/null || true
    fi

    # Email notification (requires mailx or sendmail)
    if [ -n "$EMAIL" ] && command -v mail &> /dev/null; then
        echo "$MESSAGE" | mail -s "API Assistant Health Check Alert" "$EMAIL" 2>/dev/null || true
    fi
fi

exit $EXIT_CODE
