# ESP CAN Gateway

## MQTT Protocol flow
```
Device (Publisher)              AWS IoT Core (Broker)
       │                               │
       │─── CONNECT (mTLS) ───────────>│ (authenticate with certificate)
       │                               │
       │<──── CONNACK ─────────────────│ (connection accepted)
       │                               │
       │─── PUBLISH ──────────────────>│ (send: topic="engine/rpm", payload=3500)
       │    (topic, payload, QoS)      │
       │                               │
       │<──── PUBACK ──────────────────│ (QoS 1 acknowledgment)
       │                               │
       │─── DISCONNECT ────────────────>│ (graceful close)
       │                               │

Consumer (Subscriber)           AWS IoT Core (Broker)
       │                               │
       │─── CONNECT ──────────────────>│
       │                               │
       │<──── CONNACK ─────────────────│
       │                               │
       │─── SUBSCRIBE ────────────────>│ (topic filter="engine/+")
       │                               │
       │<──── SUBACK ──────────────────│ (subscription confirmed)
       │                               │
       │                    ┌─ PUBLISH from publisher
       │                    │
       │<──── PUBLISH ──────┘──────────│ (matched topic "engine/rpm")
       │    (topic, payload)           │
       │                               │
       │─── PUBACK ───────────────────>│ (acknowledge receipt)
```
## CAN Gateway topic hierarchy
```
vehicles/
  └── gateway-001/
      ├── engine/
      │   ├── rpm          # Publish engine RPM every 100ms
      │   ├── coolant_temp # Publish coolant temp every 1s
      │   └── load         # CPU/network load
      ├── vehicle/
      │   ├── speed        # Vehicle speed from CAN
      │   ├── odometer     # Cumulative distance
      │   └── gear_status  # D/P/R/N indicator
      ├── diagnostics/
      │   ├── dtc          # Diagnostic trouble codes
      │   ├── error_count  # Running error tally
      │   └── health       # Overall system health
      ├── security/
      │   ├── auth_failures # HMAC validation failures
      │   ├── timestamp_drift # Clock skew detections
      │   └── policy_violations # Message rejection count
      └── gateway/
          ├── connection_state # connected/disconnected
          ├── uptime          # Seconds since boot
          └── message_rate    # Messages/sec throughput
```
## (Quality of service) QoS levels
|Qos|Name|Guarantee|Use Case|
|-----------|-----------|-----------|-----------|
| 0 | At Most Once | Fire-and-Forget | Non-critical telemetry (engine rpm)|
| 1 | At least Once | Guarenteed delivery | Importent events (DTC alerts, reconnections) |
| 2 | Exactly Once | No Duplicates | Financial/ compliance (not in scope)

## Key Algorithms Supported by AWS IoT

| Algorithm | Key size | Tls support | Recommendation |
| RSA | 2048 bit | 1.2 1.3 | Yes |
| ECC | P256 | 1.2 1.3 | yes |
| ECC | P384 | 1.2 1.3 | yes |
| ECC | P521 | 1.2 1.3 | yes |

ECC P256 recommended for esp 32 due to resource constraint

---

# CAN Gateway MQTT Publisher - Docker Flask Application

This application publishes MQTT telemetry to AWS IoT Core at configurable intervals, packaged as a Docker container with a Flask REST API.

## Features

- Publishes telemetry to AWS IoT Core at configurable intervals (default: 5 minutes)
- Flask REST API for health checks and manual publishing
- Containerized deployment with Docker
- Automatic reconnection and offline queueing
- Health check endpoints

## Prerequisites

- Docker and Docker Compose installed
- AWS IoT Core thing configured
- Device certificates (certificate, private key, and CA)

## Configuration

Edit [config.json](config.json) to configure the application:

```json
{
  "endpoint": "your-endpoint.iot.region.amazonaws.com",
  "thing_name": "can-gateway",
  "client_id": "can-gateway",
  "cert_path": "./certs/certificate.pem.crt",
  "key_path": "./certs/private.pem.key",
  "ca_path": "./certs/AmazonRootCA1.pem",
  "publish_interval_seconds": 300
}
```

**Configuration Options:**
- `publish_interval_seconds`: Frequency to publish telemetry (default: 300 = 5 minutes)
- Adjust this value to change how often messages are sent

## Setup

1. **Place your AWS IoT certificates in the `certs/` directory:**
   ```
   certs/
   ├── certificate.pem.crt
   ├── private.pem.key
   └── AmazonRootCA1.pem
   ```

2. **Update [config.json](config.json) with your AWS IoT endpoint and settings**

## Running with Docker Compose (Recommended)

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

## Running with Docker

```bash
# Build the image
docker build -t can-gateway-mqtt .

# Run the container
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/certs:/app/certs:ro \
  -v $(pwd)/config.json:/app/config.json:ro \
  --name can-gateway-mqtt \
  can-gateway-mqtt
```

## API Endpoints

### Health Check
```bash
GET http://localhost:5000/health
```
Returns MQTT connection status and configuration.

### Manual Publish
```bash
POST http://localhost:5000/publish
Content-Type: application/json

{
  "engine_rpm": 1500,
  "vehicle_speed": 60
}
```
Manually trigger a telemetry publish with optional custom payload.

### Get Configuration
```bash
GET http://localhost:5000/config
```
Returns current application configuration.

## Example Usage

```bash
# Check health
curl http://localhost:5000/health

# Manually publish telemetry
curl -X POST http://localhost:5000/publish \
  -H "Content-Type: application/json" \
  -d '{"engine_rpm": 2000, "vehicle_speed": 80}'

# View configuration
curl http://localhost:5000/config
```

## Changing Publish Frequency

To change how often messages are published:

1. Edit [config.json](config.json) and modify `publish_interval_seconds`:
   ```json
   {
     "publish_interval_seconds": 60
   }
   ```
   - 60 = 1 minute
   - 300 = 5 minutes (default)
   - 600 = 10 minutes
   - 3600 = 1 hour

2. Restart the container:
   ```bash
   docker-compose restart
   ```

## Monitoring

View real-time logs:
```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f can-gateway-mqtt
```

## Troubleshooting

1. **Connection Issues:**
   - Verify AWS IoT endpoint in config.json
   - Check certificates are valid and in correct location
   - Ensure IoT policy allows connections

2. **Certificate Errors:**
   - Verify certificate paths in config.json
   - Ensure certificates are readable (check permissions)
   - Confirm certificates match the AWS IoT thing

3. **Health Check Failures:**
   - Check container logs: `docker-compose logs`
   - Verify Flask is running on port 5000
   - Test endpoint: `curl http://localhost:5000/health`

## Production Deployment

For production:
- Use Docker secrets or environment variables for sensitive data
- Set up proper logging aggregation
- Configure restart policies
- Use orchestration (Kubernetes, ECS, etc.)
- Monitor with health check endpoints
