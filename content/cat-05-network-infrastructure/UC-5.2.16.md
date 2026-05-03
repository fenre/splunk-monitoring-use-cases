<!-- AUTO-GENERATED from UC-5.2.16.json — DO NOT EDIT -->

---
id: "5.2.16"
title: "SSL/TLS Decryption Failures"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.16 · SSL/TLS Decryption Failures

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We count decryption and handshake failures so you can tell policy missteps and old clients from someone tampering in the middle.*

---

## Description

Decryption failures create blind spots in security inspection. Tracking failures by destination reveals certificate pinning, protocol mismatches, or policy gaps.

## Value

Operations teams monitor SSL/TLS decryption engine performance, detecting resource exhaustion and protocol errors that cause traffic to bypass security inspection.

## Implementation

Enable decryption logging. Group failures by reason (unsupported cipher, certificate pinning, policy exclude). Review and update decryption policy based on findings.

## Detailed Implementation

### Prerequisites
* Firewall SSL/TLS decryption performance logs. Palo Alto: `pan:system` and `pan:decryption`, Fortinet: `fgt_event` with SSL events. Key metrics: decryption sessions, decryption failures, decryption bypass events, certificate errors.
* SSL/TLS decryption failures create visibility gaps -- traffic that should be inspected passes through uninspected. Distinct from certificate inspection failures (UC-5.2.8): this UC focuses on the decryption engine performance (resource exhaustion, protocol errors, capacity).

### Step 1 — - Configure data collection
Verify decryption events:
```spl
index=firewall earliest=-4h
| where match(_raw, "(?i)decrypt|ssl.*(fail|error|bypass|offload|session)|tls.*(fail|error)")
| stats count by sourcetype, host
```

### Step 2 — - Create the search and alert

**Primary search -- SSL/TLS decryption failure analysis:**
```spl
index=firewall earliest=-4h
| where match(_raw, "(?i)decrypt.*(fail|error|resource|capacity|timeout)|ssl.*(fail|error|bypass)|tls.*(error|unsupported)")
| eval failure_type=case(match(_raw, "(?i)resource|capacity|limit|no.*hw.accel"), "RESOURCE_EXHAUSTION", match(_raw, "(?i)unsupported.*(version|protocol|cipher)"), "UNSUPPORTED_PROTOCOL", match(_raw, "(?i)timeout|handshake.*timeout"), "HANDSHAKE_TIMEOUT", match(_raw, "(?i)bypass|exclude|skip"), "POLICY_BYPASS", match(_raw, "(?i)error|fail"), "DECRYPTION_ERROR", 1==1, "OTHER")
| stats count as failures dc(coalesce(dest_ip, dest)) as affected_destinations by host, failure_type
| eval severity=case(failure_type="RESOURCE_EXHAUSTION", "CRITICAL -- decryption hardware/software saturated", failure_type="HANDSHAKE_TIMEOUT", "HIGH -- SSL handshakes timing out", failure_type="UNSUPPORTED_PROTOCOL" AND failures > 100, "WARNING -- many unsupported protocol errors", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -failures
```

### Step 3 — - Validate
(a) Palo Alto: `show system setting ssl-decrypt` -- shows decryption statistics and capacity.
(b) Check hardware acceleration: PA `show running resource-monitor` -- SSL proxy utilization.
(c) Verify decryption is functioning: browse a test HTTPS site through the firewall and check for decryption log entries.

### Step 4 — - Operationalize
Dashboard ("Firewall -- SSL Decryption Health"):
* Row 1 -- Single-value: "Decryption failures", "Resource exhaustion events", "Handshake timeouts", "Bypassed flows".
* Row 2 -- Failure type breakdown.

Alerting:
* Critical (resource exhaustion): decryption engine overloaded -- traffic passing uninspected.
* High (handshake timeouts > 50/hr): performance degradation.

### Step 5 — - Troubleshooting

* **Resource exhaustion** -- Decryption hardware accelerator is saturated. Options: (1) upgrade to a model with higher SSL throughput, (2) reduce decryption scope (exclude low-risk categories), (3) enable hardware offloading if not already active.

* **Handshake timeouts** -- SSL handshakes taking too long. Check: (1) OCSP/CRL responder latency, (2) certificate chain validation time, (3) network latency to external sites.

* **Unsupported protocol (TLS 1.3/QUIC)** -- Some firewall models don't support TLS 1.3 decryption. Update firmware. QUIC (HTTP/3) often bypasses decryption entirely -- consider blocking QUIC to force HTTP/2 over TLS.

## SPL

```spl
index=network sourcetype="pan:decryption" action="decrypt-error" OR action="no-decrypt"
| stats count by reason, dest, dest_port
| sort 50 -count
```

## Visualization

Bar chart (failure reasons), Table (top undecrypted destinations), Pie chart (by reason).

## Known False Positives

Legacy clients, pinned certificates, and pinned apps that resist inspection raise decryption errors without an attack.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
