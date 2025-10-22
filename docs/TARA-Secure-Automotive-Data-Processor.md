# Threat Analysis and Risk Assessment (TARA)
## Project 1: Secure Automotive Data Processor

---

## 1. ITEM DEFINITION

### 1.1 Item Overview
**Item Name:** Vehicle Telematics Data Processing System (Cloud Component)

**Vehicle Function Context:** 
Remote vehicle diagnostics and fleet management system. In a real deployment, 
this would be the backend receiving data from in-vehicle Telematics Control Units (TCUs).

**Description:** 
Cloud-based application that receives, processes, and stores vehicle CAN bus 
telemetry data transmitted from connected vehicles.

**Note on Scope:**
In full ISO 21434 analysis, the "item" would be the in-vehicle TCU. For this 
learning project, we're analyzing the cloud backend component using ISO 21434 
methodology to understand the threat modeling process.

### 1.2 Item Boundaries

**In Scope:**
- AWS EC2 instance running Python application
- AWS S3 storage bucket for processed data
- IAM roles and policies
- Data processing logic
- Network interfaces (HTTPS endpoints)

**Out of Scope:**
- In-vehicle TCU hardware (simulated)
- Vehicle CAN networks (simulated via CSV)
- End-user applications consuming the data
- Physical AWS data center security

### 1.3 Operational Environment
- **Deployment:** AWS Cloud (us-east-1 region)
- **Access:** Programmatic (no human GUI)
- **Data Volume:** ~1000 CAN messages per vehicle per minute
- **Retention:** 90 days in S3
- **Users:** Automated systems only (no human access to EC2)

---

## 2. ASSET IDENTIFICATION

Assets are elements of the system that have value and require protection.

| Asset ID | Asset Name | Description | C | I | A | Rationale |
|----------|-----------|-------------|---|---|---|-----------|
| A-001 | Vehicle CAN telemetry data | Raw and processed vehicle diagnostic data | **H** | M | L | Contains vehicle location, driving patterns, VIN - privacy sensitive |
| A-002 | AWS IAM credentials | Access keys, roles, policies for AWS services | **C** | **C** | H | Compromise = full AWS account takeover |
| A-003 | S3 bucket | Storage location for all processed data | **H** | H | M | Central repository; breach exposes all vehicle data |
| A-004 | EC2 instance | Compute resource running processing application | M | **H** | H | Compromise allows code injection, data manipulation |
| A-005 | Processing application code | Python scripts, logic, algorithms | L | **H** | M | Integrity critical; malicious modification = corrupted outputs |
| A-006 | AWS account | Top-level AWS account and billing | **C** | **C** | **C** | Root-level compromise = total system loss |
| A-007 | CloudWatch logs | Audit trail and security monitoring data | M | **H** | M | Tampering hides evidence of attacks |

**Legend:**
- C = Confidentiality, I = Integrity, A = Availability
- **C** = Critical, **H** = High, M = Medium, L = Low

---

## 3. THREAT SCENARIO IDENTIFICATION

### TS-001: Unauthorized Access to S3 Bucket
**Threat:** External attacker gains unauthorized read access to S3 bucket

**Attack Path:**
1. Attacker scans for misconfigured S3 buckets (public read permissions)
2. Discovers bucket contains vehicle telemetry data
3. Downloads all historical data

**Assets Affected:** A-001 (telemetry data), A-003 (S3 bucket)

**Impact Analysis:**
- **Safety Impact:** None (no vehicle control affected)
- **Financial Impact:** GDPR fines (€20M or 4% revenue), lawsuit costs
- **Operational Impact:** Reputational damage, customer trust loss
- **Privacy Impact:** Exposure of vehicle locations, driving patterns for thousands of vehicles

**Impact Rating:** **HIGH** (severe privacy breach, regulatory penalties)

**Attack Feasibility:**
- Knowledge: Low (automated scanners exist)
- Window of Opportunity: High (always accessible if misconfigured)
- Equipment: Low (basic tools)
- Overall Feasibility: **MEDIUM**

**Risk Level:** **HIGH** (High Impact × Medium Feasibility)

**Treatment Decision:** **REDUCE** - Implement security controls
- Control 1: Enable S3 bucket encryption (AES-256)
- Control 2: Block public access at bucket policy level
- Control 3: Use IAM roles with least privilege (no public read)
- Control 4: Enable S3 access logging
- Control 5: Implement bucket versioning (detect tampering)

---

### TS-002: Credential Theft from Code Repository
**Threat:** AWS access keys hardcoded in application source code are exposed

**Attack Path:**
1. Developer accidentally commits AWS credentials to GitHub
2. Attacker uses GitHub scanning tools to find exposed keys
3. Attacker uses keys to access S3, EC2, or other AWS services
4. Lateral movement to other AWS resources

**Assets Affected:** A-002 (IAM credentials), A-006 (AWS account)

**Impact Analysis:**
- **Safety Impact:** None directly, but could escalate
- **Financial Impact:** Unauthorized AWS usage ($$$), potential crypto mining
- **Operational Impact:** Complete system compromise, data destruction possible
- **Privacy Impact:** Access to all vehicle data, potential exfiltration

**Impact Rating:** **CRITICAL** (full account compromise)

**Attack Feasibility:**
- Knowledge: Low (well-known attack pattern)
- Window of Opportunity: High (GitHub history is permanent)
- Equipment: Low (free GitHub scanners)
- Overall Feasibility: **HIGH**

**Risk Level:** **CRITICAL** (Critical Impact × High Feasibility)

**Treatment Decision:** **REDUCE** - Implement security controls
- Control 1: Use IAM roles for EC2 (no hardcoded credentials)
- Control 2: Scan code with git-secrets before commits
- Control 3: Use AWS Secrets Manager for any required secrets
- Control 4: Rotate all credentials immediately if exposed
- Control 5: Enable AWS CloudTrail for audit logging

---

### TS-003: Malicious CAN Data Injection
**Threat:** Attacker injects malformed or malicious CAN data to crash processor

**Attack Path:**
1. Attacker compromises data source (simulated TCU)
2. Sends specially crafted CAN messages:
   - Extremely long data fields (buffer overflow attempt)
   - SQL injection strings in CAN ID fields
   - Null bytes or format string attacks
   - Millions of messages (DoS)
3. Application crashes, becomes unavailable, or executes malicious code

**Assets Affected:** A-004 (EC2 instance), A-005 (application code)

**Impact Analysis:**
- **Safety Impact:** None (cloud component doesn't affect vehicle)
- **Financial Impact:** Loss of telemetry service, SLA penalties
- **Operational Impact:** Service downtime, fleet monitoring blind spot
- **Privacy Impact:** None directly

**Impact Rating:** **MEDIUM** (service disruption, no data breach)

**Attack Feasibility:**
- Knowledge: Medium (requires understanding of input validation bypass)
- Window of Opportunity: High (if input validation is weak)
- Equipment: Low (can simulate from laptop)
- Overall Feasibility: **MEDIUM**

**Risk Level:** **MEDIUM** (Medium Impact × Medium Feasibility)

**Treatment Decision:** **REDUCE** - Implement security controls
- Control 1: Strict input validation (whitelist valid CAN IDs, data length checks)
- Control 2: Rate limiting (max messages per second per vehicle)
- Control 3: Sanitize all inputs before processing
- Control 4: Exception handling (fail gracefully, don't crash)
- Control 5: Anomaly detection (flag unusual patterns)

---

### TS-004: Man-in-the-Middle Attack on Data Transit
**Threat:** Attacker intercepts data between EC2 and S3

**Attack Path:**
1. Attacker gains network position between EC2 and S3 (unlikely in AWS VPC)
2. Intercepts unencrypted HTTP traffic
3. Reads or modifies data in transit
4. Injects false telemetry data

**Assets Affected:** A-001 (telemetry data), A-003 (S3 bucket)

**Impact Analysis:**
- **Safety Impact:** Potential (if false data leads to incorrect maintenance decisions)
- **Financial Impact:** Incorrect diagnostics, warranty fraud
- **Operational Impact:** Data integrity loss, unreliable analytics
- **Privacy Impact:** Exposure during transmission

**Impact Rating:** **HIGH** (data confidentiality and integrity compromise)

**Attack Feasibility:**
- Knowledge: High (requires network-level access within AWS)
- Window of Opportunity: Low (AWS VPC isolation)
- Equipment: High (advanced network tools)
- Overall Feasibility: **LOW**

**Risk Level:** **MEDIUM** (High Impact × Low Feasibility)

**Treatment Decision:** **REDUCE** - Implement security controls
- Control 1: Use HTTPS/TLS for all S3 uploads (boto3 default)
- Control 2: Verify TLS certificate validity
- Control 3: Use VPC endpoints for S3 (traffic never leaves AWS network)
- Control 4: Enable S3 transfer acceleration with encryption

---

### TS-005: EC2 Instance Compromise via SSH
**Threat:** Attacker gains unauthorized SSH access to EC2 instance

**Attack Path:**
1. Attacker scans internet for open SSH ports
2. Attempts brute force or credential stuffing on SSH
3. Successfully authenticates (weak password, stolen key)
4. Escalates privileges to root
5. Installs malware, exfiltrates data, modifies code

**Assets Affected:** A-004 (EC2 instance), A-005 (application code), A-002 (credentials on instance)

**Impact Analysis:**
- **Safety Impact:** None directly
- **Financial Impact:** Crypto mining, resource abuse, data breach costs
- **Operational Impact:** Complete system compromise
- **Privacy Impact:** Access to all telemetry data, credentials

**Impact Rating:** **HIGH** (full instance control)

**Attack Feasibility:**
- Knowledge: Low (automated tools available)
- Window of Opportunity: High (if SSH exposed to internet)
- Equipment: Low (basic tools)
- Overall Feasibility: **HIGH** (if misconfigured)

**Risk Level:** **HIGH** (High Impact × High Feasibility if exposed)

**Treatment Decision:** **REDUCE** - Implement security controls
- Control 1: Security group allows SSH only from specific IP (your workstation)
- Control 2: Use SSH key authentication only (no passwords)
- Control 3: Disable root SSH login
- Control 4: Use AWS Systems Manager Session Manager instead of SSH
- Control 5: Enable fail2ban or similar intrusion prevention

---

## 4. RISK ASSESSMENT SUMMARY

| Threat ID | Threat Scenario | Impact | Feasibility | Risk Level | Treatment |
|-----------|----------------|---------|-------------|------------|-----------|
| TS-001 | Unauthorized S3 access | HIGH | MEDIUM | **HIGH** | REDUCE |
| TS-002 | Credential theft | CRITICAL | HIGH | **CRITICAL** | REDUCE |
| TS-003 | Malicious data injection | MEDIUM | MEDIUM | **MEDIUM** | REDUCE |
| TS-004 | MITM attack | HIGH | LOW | **MEDIUM** | REDUCE |
| TS-005 | EC2 SSH compromise | HIGH | HIGH | **HIGH** | REDUCE |

**Risk Distribution:**
- CRITICAL: 1 threat
- HIGH: 2 threats  
- MEDIUM: 2 threats
- LOW: 0 threats

**Priority Actions:**
1. Address TS-002 immediately (CRITICAL)
2. Address TS-001 and TS-005 (HIGH)
3. Address TS-003 and TS-004 (MEDIUM)

---

## 5. SECURITY REQUIREMENTS

Requirements derived from threat treatments:

### SR-001: No Hardcoded Credentials
**Derived from:** TS-002  
**Requirement:** Application shall not contain hardcoded AWS credentials  
**Verification:** Code review + automated scanning with git-secrets  
**Implementation:** Use IAM roles for EC2 instances

### SR-002: S3 Encryption at Rest
**Derived from:** TS-001  
**Requirement:** All S3 buckets shall use AES-256 encryption  
**Verification:** AWS Config rule check  
**Implementation:** Enable default encryption on bucket

### SR-003: Input Validation
**Derived from:** TS-003  
**Requirement:** All CAN data inputs shall be validated before processing  
**Verification:** Unit tests with malicious inputs  
**Implementation:** Validation function checking: CAN ID format, data length, rate limits

### SR-004: Encrypted Data Transit
**Derived from:** TS-004  
**Requirement:** All data in transit shall use TLS 1.2 or higher  
**Verification:** Network traffic analysis  
**Implementation:** boto3 uses HTTPS by default, verify no HTTP fallback

### SR-005: Network Segmentation
**Derived from:** TS-005  
**Requirement:** EC2 instance shall only allow necessary inbound connections  
**Verification:** Security group audit  
**Implementation:** Security group allows SSH from specific IP only, no other inbound

### SR-006: Audit Logging
**Derived from:** All threats  
**Requirement:** All security-relevant events shall be logged  
**Verification:** Log review in CloudWatch  
**Implementation:** CloudWatch Logs with 90-day retention

### SR-007: Least Privilege IAM
**Derived from:** TS-001, TS-002  
**Requirement:** IAM roles shall have minimum required permissions  
**Verification:** IAM policy review  
**Implementation:** Role can only PutObject to specific S3 bucket, CreateLogStream to specific log group

---

## 6. RESIDUAL RISK

After implementing all security controls:

| Threat ID | Original Risk | Controls Implemented | Residual Risk | Accepted? |
|-----------|---------------|---------------------|---------------|-----------|
| TS-001 | HIGH | SR-002, SR-007 | LOW | ✅ Yes |
| TS-002 | CRITICAL | SR-001, SR-007 | LOW | ✅ Yes |
| TS-003 | MEDIUM | SR-003 | LOW | ✅ Yes |
| TS-004 | MEDIUM | SR-004 | LOW | ✅ Yes |
| TS-005 | HIGH | SR-005 | LOW | ✅ Yes |

**Risk Acceptance Rationale:**
All residual risks are LOW after implementing compensating controls. Remaining risks (e.g., AWS region-level outage, zero-day vulnerabilities) are accepted as they require defense-in-depth beyond this project's scope.

---

## 7. NEXT STEPS

**Immediate Actions for Week 1:**
1. ✅ Implement SR-001 (IAM roles) in Story 1.3
2. ✅ Implement SR-002 (S3 encryption) in Story 1.4
3. ✅ Implement SR-003 (input validation) in Story 1.4
4. ✅ Implement SR-004 (TLS) - verify in Story 1.4
5. ✅ Implement SR-005 (security groups) in Story 1.4
6. ✅ Implement SR-006 (logging) in Story 1.4
7. ✅ Implement SR-007 (least privilege) in Story 1.4

**Verification Plan:**
- Code review: Check for hardcoded credentials
- Automated testing: Unit tests with malicious inputs
- AWS Console: Verify encryption, security groups, IAM policies
- CloudWatch: Confirm logs are being generated

---

## DOCUMENT HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-21 | Prithvi Shenoy | Initial TARA for Project 1 |

---

## REFERENCES

- ISO/SAE 21434:2021 - Road vehicles - Cybersecurity engineering
- NIST SP 800-53 - Security and Privacy Controls
- AWS Well-Architected Framework - Security Pillar
- OWASP Top 10