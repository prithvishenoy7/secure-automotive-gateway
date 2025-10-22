# Secure Automotive Data Processor
## Architecture Overview

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