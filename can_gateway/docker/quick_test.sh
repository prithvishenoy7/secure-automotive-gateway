#!/bin/bash

echo "=== Docker Container Status ==="
docker-compose ps

echo -e "\n=== Health Check ==="
curl -s http://localhost:5000/health | python -m json.tool

echo -e "\n=== Manual Publish Test ==="
curl -s -X POST http://localhost:5000/publish \
  -H "Content-Type: application/json" \
  -d "{\"test\": \"verification\", \"timestamp\": \"$(date +%s)\"}" | python -m json.tool

echo -e "\n=== Recent Logs ==="
docker-compose logs --tail=20

echo -e "\n=== Instructions ==="
echo "1. Check AWS IoT Console MQTT test client"
echo "2. Subscribe to: vehicle/can-gateway/telemetry"
echo "3. You should see the test message above"
