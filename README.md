# Secure Automotive Data Processor

## Project Overview
Cloud-based CAN data processor with ISO 21434 security controls.

## Architecture Overview

### Real world arcitecture in Vehicle telematics system
```
┌─────────────────────────────────┐
│ VEHICLE (TCU)                   │
│                                 │
│  [TCU collects CAN data]        │
│         ↓                       │
│  [TCU sends via HTTPS POST]     │ ← OUTBOUND from vehicle
└─────────────┬───────────────────┘
              │ 4G/5G
              ↓
┌─────────────────────────────────┐
│ CLOUD (AWS)                     │
│                                 │
│  [API Gateway] ← INBOUND        │ ← Receives HTTPS POST
│         ↓                       │
│  [Lambda or EC2 processor]      │
│         ↓                       │
│  [S3 Storage]                   │
└─────────────────────────────────┘
```

**Real architecture needs:**
- **API Gateway** or **Load Balancer** with HTTPS endpoint (port 443 inbound)
- **Authentication** (API keys, certificates, OAuth)
- **Rate limiting** (prevent DoS)

### Simplified for this Project

We're simulating with a CSV file instead of real-time streaming. No inbound needed - we're batch processing local files.

```
     ┌─────────────────┐
     │  CAN Data CSV   │  (Simulated vehicle telemetry)
     └────────┬────────┘
              │
              ▼
┌─────────────────────────────┐
│   AWS EC2 Instance          │
│  ┌──────────────────────┐   │
│  │  Python Application  │   │
│  │  - Read CAN data     │   │
│  │  - Validate input    │   │
│  │  - Process/filter    │   │
│  │  - Log activities    │   │
│  └──────────┬───────────┘   │
└─────────────┼───────────────┘
              │ (IAM Role - No hardcoded credentials)
              ▼
   ┌──────────────────────┐
   │   AWS S3 Bucket      │
   │  (AES-256 Encrypted) │
   │  - Processed results │
   │  - Timestamped files │
   └──────────────────────┘
              │
              ▼
   ┌──────────────────────┐
   │   CloudWatch Logs    │
   │  (Monitoring)        │
   └──────────────────────┘
```


## Attack Surface Diagram
```
                    INTERNET
                       │
                       │ (Threats)
                       ↓
         ┌─────────────────────────┐
         │  Security Group         │ ← Layer 1: Network Filter
         │  - Port 22: YOUR_IP     │
         │  - Port 443: Outbound   │
         └──────────┬──────────────┘
                    │ SSH (legitimate)
                    ↓
         ┌─────────────────────────┐
         │  EC2 Instance           │ ← Layer 2: Authentication
         │  - SSH key auth only    │    (Your public key)
         │  - No password login    │
         │                         │
         │  ┌──────────────────┐   │
         │  │ Python App       │   │ ← Layer 3: Application
         │  │ - Input validate │   │    
         │  │ - Rate limiting  │   │
         │  └────────┬─────────┘   │
         │           │             │
         │  ┌────────▼─────────┐   │
         │  │ IAM Role         │   │ ← Layer 4: Permission Boundary
         │  │ (temporary creds)│   │    (Metadata service)
         │  └────────┬─────────┘   │
         └───────────┼─────────────┘
                     │ HTTPS (TLS)
                     │
         ┌───────────▼─────────────┐
         │  S3 Bucket              │ ← Layer 5: Data Protection
         │  - Server-side encrypt  │
         │  - Bucket policy        │
         │  - Versioning           │
         └─────────────────────────┘
                     │
                     ↓
         ┌─────────────────────────┐
         │  CloudWatch Logs        │ ← Layer 6: Detection
         │  - Audit trail          │
         │  - Anomaly detection    │
         └─────────────────────────┘
```
### ATTACK PATHS and MITIGATIONS:

| Threat Scenario    | Attack Path                                      |Mitigation                                  |
| -----------        | -----------                                      |-----------                                 |
| TS-001             | Internet → S3 bucket (if misconfigured)          |S3 server-side encryption (AES-256)         |
| TS-002             | Compromise EC2 → Find hardcoded creds → AWS API  |IAM roles (no hardcoded credentials)        |
| TS-003             | Malicious CAN data → Buffer overflow → RCE       | Input validation (CAN message validation)  |
| TS-004             | MITM → Intercept EC2↔S3 traffic                  | TLS encryption (HTTPS to S3)               |
| TS-005             | Internet → SSH brute force → EC2 root            | Security Group (SSH from specific IP only) |


### LEGITIMATE PATH:
* Admin IP → SSH (port 22) → EC2
           → Run processor.py
           → IAM role → S3 upload
           → CloudWatch logging

## Components
- **S3 Bucket**: `secure-can-processor-YYYYMMDD`
- **IAM Role**: `CANProcessorRole`
- **Security Group**: SSH port 22 from admin IP only
- **EC2**: `t3.micro` in eu-north-1

## Running
```bash
python3 src/processor.py data/sample_can_data.csv secure-can-processor-YYYYMMDD
```

## Author
Prithvi Shenoy - Embedded Engineer → Automotive Cybersecurity Expert