#!/bin/bash

# Test script to verify Hatchet workflow is working

echo "=========================================="
echo "🧪 Testing Hatchet Workflow Registration"
echo "=========================================="
echo ""

# 1. Check if worker is running
echo "1️⃣ Checking Hatchet Worker..."
if docker ps | grep -q "loan-underwriting-hatchet-worker"; then
    echo "✅ Hatchet worker is running"
    docker logs loan-underwriting-hatchet-worker 2>&1 | grep "✅ Workflow registered successfully" > /dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Workflow is registered"
    else
        echo "❌ Workflow not registered"
        exit 1
    fi
else
    echo "❌ Hatchet worker is not running"
    echo "   Run: docker-compose up -d hatchet-worker"
    exit 1
fi
echo ""

# 2. Create test application
echo "2️⃣ Creating test application..."
APP_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/applications/ \
  -H "Content-Type: application/json" \
  -d '{
    "business": {
      "legal_name": "Hatchet Test Co",
      "state": "TX",
      "years_in_business": 3,
      "annual_revenue": 750000
    },
    "guarantor": {
      "first_name": "Jane",
      "last_name": "Smith",
      "email": "jane@test.com",
      "fico_score": 680,
      "years_in_business": 3
    },
    "business_credit": {
      "paydex_score": 70,
      "paynet_class": "B",
      "has_recent_bankruptcy": false
    },
    "loan_request": {
      "requested_amount": 75000,
      "equipment_type": "Construction",
      "equipment_year": 2022,
      "loan_term_months": 48
    }
  }')

APP_ID=$(echo $APP_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
APP_REF=$(echo $APP_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['reference_id'])")
echo "✅ Created application: ID=$APP_ID ($APP_REF)"
echo ""

# 3. Submit application
echo "3️⃣ Submitting application..."
curl -s -X POST http://localhost:8001/api/v1/applications/$APP_ID/submit > /dev/null
echo "✅ Application submitted"
echo ""

# 4. Trigger underwriting
echo "4️⃣ Triggering underwriting with Hatchet..."
RUN_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/underwriting/$APP_ID/run)
RUN_ID=$(echo $RUN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "✅ Underwriting run started: ID=$RUN_ID"
echo ""

# 5. Check if Hatchet was used
echo "5️⃣ Verifying Hatchet was used..."
sleep 2
docker logs loan-underwriting-api 2>&1 | tail -20 | grep "✓ Started Hatchet workflow" > /dev/null
if [ $? -eq 0 ]; then
    WORKFLOW_ID=$(docker logs loan-underwriting-api 2>&1 | tail -20 | grep "✓ Started Hatchet workflow" | tail -1 | awk '{print $6}')
    echo "✅ Hatchet workflow started: $WORKFLOW_ID"
    echo "✅ View in dashboard: https://cloud.onhatchet.run"
else
    echo "❌ Hatchet workflow failed"
    docker logs loan-underwriting-api 2>&1 | tail -10 | grep "Hatchet"
    exit 1
fi
echo ""

# 6. Check worker processed it
echo "6️⃣ Checking worker execution..."
sleep 3
docker logs loan-underwriting-hatchet-worker 2>&1 | tail -20 | grep "Validating application $APP_ID" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Worker processed the workflow"
    echo "   Steps executed:"
    docker logs loan-underwriting-hatchet-worker 2>&1 | tail -30 | grep "application $APP_ID" | sed 's/^/     /'
else
    echo "❌ Worker did not process the workflow"
    exit 1
fi
echo ""

echo "=========================================="
echo "🎉 SUCCESS! Hatchet is working correctly!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  • Worker: Running and registered ✅"
echo "  • API: Using Hatchet (not BackgroundTasks) ✅"
echo "  • Workflow: Executed successfully ✅"
echo ""
echo "Next steps:"
echo "  • View workflow in Hatchet dashboard"
echo "  • Check application matches: curl http://localhost:8001/api/v1/applications/$APP_ID/matches"
echo "  • Monitor worker logs: docker logs -f loan-underwriting-hatchet-worker"