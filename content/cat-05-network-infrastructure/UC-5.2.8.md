<!-- AUTO-GENERATED from UC-5.2.8.json — DO NOT EDIT -->

---
id: "5.2.8"
title: "Certificate Inspection Failures"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.2.8 · Certificate Inspection Failures

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We track certificate and decryption issues so we can sort broken sites and policy gaps from real interception attacks.*

---

## Description

SSL decryption failures mean traffic passes uninspected — could be legitimate cert pinning or SSL evasion.

## Value

Security teams classify SSL/TLS decryption failures by root cause (cert pinning, expired certs, cipher mismatches), identifying uninspected HTTPS traffic that bypasses security inspection.

## Implementation

Enable decryption logging. Track failure rates by destination. Tune exclusion lists.

## Detailed Implementation

### Prerequisites
* Firewall SSL/TLS decryption logs. Palo Alto: `sourcetype=pan:decryption` or `sourcetype=pan:threat` with subtype=decrypt. Fortinet: `sourcetype=fgt_utm` with type=ssl. Cisco FTD: SSL policy events in `cisco:firepower:syslog`. Key fields: `action` (ssl-error/decrypt-error/bypass), `dest`, `dest_port`, `reason`, `ssl_version`, `cert_subject`.
* Certificate inspection failures mean HTTPS traffic passes uninspected, creating a security blind spot. Causes: (1) certificate pinning (legitimate), (2) unsupported cipher, (3) client/server using TLS 1.3 without decryption support, (4) self-signed/expired certificates, (5) SSL evasion techniques.

### Step 1 — - Configure data collection
**Palo Alto:**
```
# Policies > Decryption > ensure policy covers required traffic
# Objects > Decryption Profile > set failure actions (block or log-and-allow)
# Device > Log Settings > ensure decryption log forwarding
```
Verify:
```spl
index=firewall (sourcetype="pan:decryption" OR (sourcetype="fgt_utm" type="ssl") OR (sourcetype="cisco:firepower:syslog" ssl_error)) earliest=-4h
| where match(action, "(?i)ssl-error|decrypt-error|bypass|fail")
| stats count by sourcetype, host
```

### Step 2 — - Create the search and alert

**Primary search -- Certificate inspection failure analysis:**
```spl
index=firewall earliest=-4h
| where match(_raw, "(?i)ssl.error|decrypt.error|decrypt.fail|cert.*(invalid|expired|untrusted|pinned)|ssl.*bypass")
| eval failure_reason=case(match(_raw, "(?i)pinning|pinned|HPKP"), "CERT_PINNING", match(_raw, "(?i)expired"), "CERT_EXPIRED", match(_raw, "(?i)untrusted|self.signed|unknown.CA"), "UNTRUSTED_CA", match(_raw, "(?i)cipher|algorithm|unsupported"), "UNSUPPORTED_CIPHER", match(_raw, "(?i)version|protocol|tls.1\.3"), "PROTOCOL_MISMATCH", match(_raw, "(?i)timeout|handshake.fail"), "HANDSHAKE_FAIL", 1==1, "OTHER")
| eval dst=coalesce(dest, dest_ip, dstaddr)
| eval dport=coalesce(dest_port, dstport)
| stats count as failures dc(dst) as unique_destinations values(dst) as sample_dests by failure_reason
| eval severity=case(failure_reason="UNSUPPORTED_CIPHER", "HIGH -- traffic bypassing decryption", failure_reason="CERT_PINNING" AND failures > 500, "WARNING -- high pinning bypass volume", failure_reason="CERT_EXPIRED", "WARNING -- expired upstream certificates", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -failures
```

**Top uninspected destinations:**
```spl
index=firewall (action="ssl-error" OR action="decrypt-error" OR action="bypass") earliest=-4h
| eval dst=coalesce(dest, dest_ip)
| stats count as bypasses by dst
| sort -bypasses | head 20
```

### Step 3 — - Validate
(a) Palo Alto: Monitor > Logs > Decryption -- check for ssl-error actions.
(b) Test with a cert-pinned site (e.g., many banking sites) -- should show as bypass/pinning.
(c) Verify decryption profile is attached to relevant security policies.

### Step 4 — - Operationalize
Dashboard ("Firewall -- SSL Decryption Health"):
* Row 1 -- Single-value: "Decryption failures (4h)", "Bypassed destinations", "Expired certs", "Pinned sites".
* Row 2 -- Failure reason breakdown.
* Row 3 -- Top uninspected destinations.

Alerting:
* High (unsupported cipher causing decryption bypass): security gap.
* Warning (high cert pinning volume): review pinning exclusion list.

### Step 5 — - Troubleshooting

* **Certificate pinning bypass** -- Legitimate for banking/financial apps. Add to decryption exclusion list with documentation. Review periodically.

* **Unsupported cipher** -- Firewall may not support the cipher. Update firmware for TLS 1.3/QUIC support. Check: firewall software version and cipher support matrix.

* **Decryption causing application breakage** -- Some apps break when decrypted (certificate validation in app). Add to bypass list. Common: Windows Update, Apple services, healthcare apps with embedded certs.

## SPL

```spl
index=firewall sourcetype="pan:decryption" action="ssl-error"
| stats count by dest, dest_port, reason | sort -count
```

## Visualization

Table, Pie chart (reasons), Trend line.

## Known False Positives

Legacy clients, certificate rotations, HSM or cipher changes, and broken sites can all raise certificate inspection errors.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
