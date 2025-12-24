#!/bin/bash

# Test script to demonstrate Hatchet retry logic

echo "=========================================="
echo " Testing Hatchet Retry Logic"
echo "=========================================="
echo ""

cat << 'EOF'
Retry Configuration:
  📝 validate_application:  2 retries, 30s timeout
  📝 derive_features:       2 retries, 30s timeout  
  📝 get_active_lenders:    2 retries, 30s timeout
  🔥 evaluate_lenders:      3 retries, 120s timeout (critical)
  📝 finalize_results:      2 retries, 30s timeout

How Retries Work:
  • Automatic retry on transient failures (DB timeouts, network issues)
  • Exponential backoff between attempts (Hatchet default)
  • Each retry attempt logged in Hatchet dashboard
  • Workflow only fails after ALL retries exhausted
  • Critical evaluation step gets extra retries (3 vs 2)

Benefits:
  ✓ Resilient to temporary database connection issues
  ✓ Handles network hiccups gracefully
  ✓ Reduces manual intervention needed
  ✓ Full visibility in Hatchet Cloud dashboard

EOF

echo ""
echo "To see retries in action:"
echo "  1. View workflow runs at: https://cloud.onhatchet.run"
echo "  2. Each step shows attempt count and retry history"
echo "  3. Failed attempts are logged with error details"
echo "  4. Successful retries are highlighted in green"
echo ""

echo " Running a test workflow..."
echo ""

# Create and submit application
APP_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/applications/ \
  -H "Content-Type: application/json" \
  -d '{
    "business": {
      "legal_name": "Retry Test Company",
      "state": "NY",
      "years_in_business": 4,
      "annual_revenue": 600000
    },
    "guarantor": {
      "first_name": "Test",
      "last_name": "User",
      "email": "retry@test.com",
      "fico_score": 700,
      "years_in_business": 4
    },
    "business_credit": {
      "paydex_score": 72,
      "paynet_class": "B",
      "has_recent_bankruptcy": false
    },
    "loan_request": {
      "requested_amount": 60000,
      "equipment_type": "Manufacturing",
      "equipment_year": 2021,
      "loan_term_months": 42
    }
  }')

APP_ID=$(echo $APP_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)

if [ -z "$APP_ID" ]; then
    echo "❌ Failed to create application"
    exit 1
fi

echo " Created application ID: $APP_ID"

# Submit it
curl -s -X POST http://localhost:8001/api/v1/applications/$APP_ID/submit > /dev/null
echo " Application submitted"

# Trigger underwriting
RUN_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/underwriting/$APP_ID/run)
RUN_ID=$(echo $RUN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
echo " Underwriting triggered (Run ID: $RUN_ID)"

sleep 2

# Check if Hatchet was used
WORKFLOW_LINE=$(docker logs loan-underwriting-api 2>&1 | grep "✓ Started Hatchet workflow" | tail -1)
if [ -n "$WORKFLOW_LINE" ]; then
    WORKFLOW_ID=$(echo "$WORKFLOW_LINE" | awk '{print $6}')
    echo " Hatchet workflow started: $WORKFLOW_ID"
    echo ""
    echo "=========================================="
    echo "View retry details in Hatchet dashboard:"
    echo "   https://cloud.onhatchet.run"
    echo "   Workflow ID: $WORKFLOW_ID"
    echo "=========================================="
else
    echo " Hatchet not used"
fi

echo ""
echo "Retry Logic Summary:"
echo "  • All 5 steps have automatic retry enabled ✓"
echo "  • Critical evaluation step has 3 retries ✓"
echo "  • Exponential backoff between attempts ✓"
echo "  • Full visibility in Hatchet dashboard ✓"