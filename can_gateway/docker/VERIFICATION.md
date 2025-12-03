# Verification Guide - Docker MQTT Publisher to AWS IoT Core

This guide walks you through verifying that your Docker container is successfully connecting to AWS IoT Core and publishing messages.

## Prerequisites Checklist

Before starting, ensure you have:
- [ ] Valid AWS IoT certificates in `certs/` directory
- [ ] Correct AWS IoT endpoint in `config.json`
- [ ] AWS IoT Thing created and active
- [ ] IoT Policy attached to certificate with proper permissions
- [ ] Docker container running

## Step 1: Verify Container is Running

```bash
# Check container status
docker-compose ps

# Should show:
# NAME                STATE     PORTS
# can-gateway-mqtt    Up        0.0.0.0:5000->5000/tcp
```

If not running:
```bash
cd esp_can_gateway/docker
docker-compose up -d
```

## Step 2: Check Container Logs

```bash
# View real-time logs
docker-compose logs -f

# Look for these success messages:
# [MQTT] Connecting to a2tubkd8f0ljd4-ats.iot.eu-north-1.amazonaws.com...
# [MQTT] Connected to AWS IoT Core
# [MQTT] Connection confirmed!
# Publisher thread started with interval: 300s
```

**Common Error Messages:**
- `Connection refused` - Check endpoint in config.json
- `SSL handshake failed` - Certificate issue
- `Not authorized` - IoT policy needs updating

## Step 3: Test Health Endpoint

```bash
# Check application health
curl http://localhost:5000/health

# Expected response:
{
  "status": "healthy",
  "mqtt_connected": true,
  "config": {
    "endpoint": "a2tubkd8f0ljd4-ats.iot.eu-north-1.amazonaws.com",
    "thing_name": "can-gateway",
    "publish_interval_seconds": 300
  }
}
```

**Key field:** `"mqtt_connected": true` confirms MQTT connection is active.

## Step 4: Manually Trigger a Test Publish

```bash
# Send a test message
curl -X POST http://localhost:5000/publish \
  -H "Content-Type: application/json" \
  -d '{"test": "manual_publish", "engine_rpm": 1500}'

# Expected response:
{
  "status": "success",
  "topic": "vehicle/can-gateway/telemetry",
  "payload": {
    "test": "manual_publish",
    "engine_rpm": 1500,
    "timestamp": 1234567890.123
  }
}
```

Check container logs immediately after:
```bash
docker-compose logs --tail=20
```

## Step 5: Verify Messages in AWS IoT Core

### Option A: Using AWS IoT Console (Recommended for Testing)

1. **Open AWS IoT Console:**
   - Go to https://console.aws.amazon.com/iot/
   - Select your region (eu-north-1)

2. **Navigate to MQTT Test Client:**
   - In left menu: Test → MQTT test client

3. **Subscribe to Your Topic:**
   - Click "Subscribe to a topic"
   - Enter topic: `vehicle/can-gateway/telemetry`
   - Click "Subscribe"

4. **Trigger a Manual Publish:**
   ```bash
   curl -X POST http://localhost:5000/publish
   ```

5. **Watch for Messages:**
   - You should see messages appear in the AWS console
   - Each message shows timestamp, topic, and payload

### Option B: Using AWS CLI

```bash
# Subscribe to the topic using AWS CLI
aws iot-data subscribe-to-topic \
  --topic-name "vehicle/can-gateway/telemetry" \
  --region eu-north-1

# In another terminal, trigger publish
curl -X POST http://localhost:5000/publish
```

### Option C: Using Python Script

Create a subscriber script to verify messages:

```python
# save as verify_messages.py
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import json
import time

def message_callback(client, userdata, message):
    print(f"\n[RECEIVED MESSAGE]")
    print(f"Topic: {message.topic}")
    payload = json.loads(message.payload.decode('utf-8'))
    print(f"Payload: {json.dumps(payload, indent=2)}")

# Configure subscriber
subscriber = AWSIoTMQTTClient("test-subscriber")
subscriber.configureEndpoint("a2tubkd8f0ljd4-ats.iot.eu-north-1.amazonaws.com", 8883)
subscriber.configureCredentials(
    "./certs/AmazonRootCA1.pem",
    "./certs/private.pem.key",
    "./certs/certificate.pem.crt"
)

print("Connecting to AWS IoT...")
subscriber.connect()
print("Connected!")

print("Subscribing to vehicle/can-gateway/telemetry...")
subscriber.subscribe("vehicle/can-gateway/telemetry", 1, message_callback)
print("Waiting for messages... (Press Ctrl+C to exit)")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nDisconnecting...")
    subscriber.disconnect()
```

Run it:
```bash
python verify_messages.py
```

## Step 6: Check AWS CloudWatch Logs

AWS IoT Core logs connection and publish attempts:

1. **Enable CloudWatch Logs (if not enabled):**
   ```bash
   aws iot set-v2-logging-options \
     --role-arn arn:aws:iam::YOUR_ACCOUNT:role/IoTLoggingRole \
     --default-log-level INFO
   ```

2. **View Logs:**
   - Go to CloudWatch Console
   - Navigate to Log groups
   - Look for `/aws/iot/`
   - Filter for your thing name: "can-gateway"

## Step 7: Verify Scheduled Publishing

The container publishes every 5 minutes (300 seconds) by default.

1. **Watch logs for scheduled publishes:**
   ```bash
   docker-compose logs -f --tail=50

   # You should see messages like:
   # Published to vehicle/can-gateway/telemetry: {'timestamp': 1234567890, ...}
   ```

2. **Monitor in AWS IoT Console:**
   - Keep the MQTT test client subscribed
   - Wait for the next interval (check `publish_interval_seconds` in config)
   - Message should appear automatically

## Troubleshooting

### Problem: "mqtt_connected": false

**Check certificates:**
```bash
# Verify certificates exist
ls -la esp_can_gateway/docker/certs/

# Should show:
# certificate.pem.crt
# private.pem.key
# AmazonRootCA1.pem
```

**Verify certificate is attached to thing:**
```bash
aws iot list-thing-principals --thing-name can-gateway
```

### Problem: "Not authorized to connect"

**Check IoT Policy:**
```bash
# List policies
aws iot list-policies

# Get policy document
aws iot get-policy --policy-name YourPolicyName
```

**Required policy permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iot:Connect",
      "Resource": "arn:aws:iot:eu-north-1:*:client/can-gateway"
    },
    {
      "Effect": "Allow",
      "Action": "iot:Publish",
      "Resource": "arn:aws:iot:eu-north-1:*:topic/vehicle/can-gateway/*"
    },
    {
      "Effect": "Allow",
      "Action": "iot:Subscribe",
      "Resource": "arn:aws:iot:eu-north-1:*:topicfilter/vehicle/can-gateway/*"
    },
    {
      "Effect": "Allow",
      "Action": "iot:Receive",
      "Resource": "arn:aws:iot:eu-north-1:*:topic/vehicle/can-gateway/*"
    }
  ]
}
```

### Problem: SSL/TLS Errors

**Verify endpoint:**
```bash
# Test endpoint connectivity
openssl s_client -connect a2tubkd8f0ljd4-ats.iot.eu-north-1.amazonaws.com:8883 \
  -CAfile certs/AmazonRootCA1.pem \
  -cert certs/certificate.pem.crt \
  -key certs/private.pem.key

# Should show "Verify return code: 0 (ok)"
```

### Problem: No Messages in AWS IoT

**Check topic name matches:**
- Container publishes to: `vehicle/{thing_name}/telemetry`
- Subscriber must use same topic or wildcard: `vehicle/+/telemetry`

**Verify QoS settings:**
- Publisher uses QoS 1 (at least once delivery)
- Subscriber should use QoS 1 or higher

## Complete Verification Checklist

- [ ] Container is running (`docker-compose ps`)
- [ ] Logs show "Connected to AWS IoT Core"
- [ ] Health endpoint returns `"mqtt_connected": true`
- [ ] Manual publish returns success
- [ ] Messages appear in AWS IoT Console MQTT test client
- [ ] Scheduled publishes occur at configured interval
- [ ] No errors in container logs
- [ ] CloudWatch shows successful connections (optional)

## Quick Test Script

Save this as `quick_test.sh`:

```bash
#!/bin/bash

echo "=== Docker Container Status ==="
docker-compose ps

echo -e "\n=== Health Check ==="
curl -s http://localhost:5000/health | jq '.'

echo -e "\n=== Manual Publish Test ==="
curl -s -X POST http://localhost:5000/publish \
  -H "Content-Type: application/json" \
  -d '{"test": "verification", "timestamp": "'$(date +%s)'"}' | jq '.'

echo -e "\n=== Recent Logs ==="
docker-compose logs --tail=20

echo -e "\n=== Instructions ==="
echo "1. Check AWS IoT Console MQTT test client"
echo "2. Subscribe to: vehicle/can-gateway/telemetry"
echo "3. You should see the test message above"
```

Run it:
```bash
chmod +x quick_test.sh
./quick_test.sh
```

## Success Indicators

You'll know everything is working when:
1. Health endpoint shows `mqtt_connected: true`
2. Manual publish returns success status
3. Messages appear in AWS IoT Console within 1-2 seconds
4. Container logs show no errors
5. Scheduled publishes occur every 5 minutes (or your configured interval)

## Next Steps

Once verified:
- Adjust `publish_interval_seconds` in config.json
- Customize payload in app.py
- Set up CloudWatch alarms for monitoring
- Configure log aggregation for production
