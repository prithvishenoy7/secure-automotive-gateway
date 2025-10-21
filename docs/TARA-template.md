# TARA for Automotive Data Processor

## Item Definition
Cloud-based application that processes simulated vehicle CAN data and stores in AWS S3.

## Assets
1. Vehicle CAN data (confidential telemetry)
2. AWS credentials (IAM keys/roles)
3. S3 bucket (data storage)
4. EC2 instance (processing)
5. Processing logic (code)

## Threat Scenarios

### TS-001: Unauthorized Access to Vehicle Data
- **Threat:** Attacker gains access to S3 bucket
- **Impact:** Data breach (HIGH - privacy violation)
- **Feasibility:** Medium (if misconfigured)
- **Risk:** HIGH
- **Treatment:** S3 encryption + IAM least privilege + bucket policies

### TS-002: Credential Theft
- **Threat:** Hardcoded AWS keys stolen from code
- **Impact:** Full AWS account compromise (CRITICAL)
- **Feasibility:** High (if keys in repo)
- **Risk:** CRITICAL
- **Treatment:** Use IAM roles, never hardcode credentials

### TS-003: Data Tampering
- **Threat:** Attacker modifies CAN data in transit or storage
- **Impact:** Data integrity loss (MEDIUM)
- **Feasibility:** Low (requires AWS access)
- **Risk:** MEDIUM
- **Treatment:** S3 versioning, CloudTrail logging

### TS-004: Denial of Service
- **Threat:** Attacker overwhelms processor or fills S3
- **Impact:** Service unavailable (MEDIUM)
- **Feasibility:** Medium
- **Risk:** MEDIUM
- **Treatment:** Rate limiting, S3 lifecycle policies, CloudWatch alarms

### TS-005: Malicious CAN Data Injection
- **Threat:** Attacker injects malicious data through input
- **Impact:** Processing errors, potential code execution (HIGH)
- **Feasibility:** Medium (if no input validation)
- **Risk:** HIGH
- **Treatment:** Input validation, data sanitization

## Risk Assessment Summary
- 2 HIGH risks
- 2 MEDIUM risks
- 1 CRITICAL risk

All will be addressed in Stories 1.3, 1.4, 1.5.
