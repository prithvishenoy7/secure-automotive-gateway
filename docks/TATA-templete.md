# TARA Template (Threat Analysis and Risk Assessment)

Purpose

A concise description of the purpose of this TARA (Threat Analysis and Risk Assessment) template and when to use it.

Metadata

- Author: @prithvishenoy-knowit
- Date: 2025-10-21
- Version: 1.1
- Status: Draft

Project Context

Briefly describe how this artifact relates to the secure-automotive-gateway project and which modules/components it affects.

TARA Overview

Explain the TARA approach, scope, methodology, and any standards followed (e.g., ISO 21434, SAE J3061, NIST).

Asset Identification

- Asset ID
- Asset name
- Asset description
- Owner
- Confidentiality, Integrity, Availability (CIA) classification

Threat Sources

List potential threat sources (e.g., malicious actors, supply chain, insiders, faults) and their capabilities.

Threat Scenarios

| ID | Scenario | Threat Source | Trigger/Entry Point | Affected Asset(s) | Description |
|----|----------|---------------|---------------------|-------------------|-------------|
| TARA-001 | Example: ECU takeover via insecure update | Remote attacker | OTA update service | Gateway, ECU | Short description of the scenario |

Vulnerabilities

List identified vulnerabilities, how they relate to threat scenarios, and references to code, configs, or design documents.

Likelihood & Impact Assessment

- Likelihood: (e.g., Low/Medium/High) — rationale
- Impact: (e.g., Low/Medium/High) — rationale
- Scoring method: (e.g., qualitative, CVSS, custom scale)

Risk Evaluation

Summarize assessed risks combining likelihood and impact. Include risk rating and prioritization.

Risk Treatment & Recommendations

For each prioritized risk provide:
- Recommended mitigations (technical and organizational)
- Suggested security controls
- Owner and target completion date

Residual Risk

Document residual risk after proposed mitigations and acceptance criteria for residual risk.

Verification & Validation

Describe tests, threat modeling, code reviews, penetration testing, and monitoring activities to validate mitigations.

Monitoring & Review

Describe how risks will be reviewed and monitored over time, including triggers for re-assessment and responsible parties.

Artifacts & Evidence

List evidence to collect (logs, test results, design review notes, threat model files) and where to store them.

Change Log

- 1.0 (2025-10-21) - Draft created by @prithvishenoy-knowit
- 1.1 (2025-10-21) - Converted to TARA template and clarified sections

References

- ISO 21434
- SAE J3061
- NIST Cybersecurity Framework

Notes

Any additional notes, links to related issues/PRs, or next steps.