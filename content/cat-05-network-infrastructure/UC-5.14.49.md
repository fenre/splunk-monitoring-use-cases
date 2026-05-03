<!-- AUTO-GENERATED from UC-5.14.49.json — DO NOT EDIT -->

---
id: "5.14.49"
title: "Traefik Mutual TLS Client Certificate Errors"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.49 · Traefik Mutual TLS Client Certificate Errors

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Security, Audit &middot; **Status:** Draft

*We watch traefik mutual tls client certificate errors and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

mTLS ecosystems break silently when CAs rotate.

## Value

Operations teams classify Traefik mutual TLS client certificate failures by error type (expired, untrusted CA, missing cert), enabling targeted client communication for certificate renewal.

## Implementation

Configure `tls.options.clientAuthType`; never log private keys or full chains in access logs.

## Detailed Implementation

### Prerequisites
* Traefik logs with mutual TLS (mTLS) events. Data in `index=proxy` with `sourcetype=traefik:log` or `sourcetype=traefik:access`. Key events: client certificate validation failures, untrusted CA, expired client cert.
* Mutual TLS: Traefik can require client certificates for authentication. Configured per entrypoint or per router with `tls.options` specifying `clientAuth.caFiles` and `clientAuth.clientAuthType` (RequireAndVerifyClientCert, VerifyClientCertIfGiven, etc.). Failed client cert verification results in TLS handshake failure.

### Step 1 — - Configure data collection
```yaml
# traefik.yml -- mTLS
tls:
  options:
    mtls-strict:
      clientAuth:
        caFiles:
        - /etc/traefik/certs/client-ca.crt
        clientAuthType: RequireAndVerifyClientCert
      minVersion: VersionTLS12
```
Verify:
```spl
index=proxy (sourcetype="traefik:log" OR sourcetype="traefik:access") earliest=-4h
| where match(_raw, "(?i)client.*cert|tls.*handshake.*fail|mutual.*tls|mTLS|bad certificate|unknown.*ca|expired.*cert|certificate.*required")
| stats count
```

### Step 2 — - Create the search and alert

**Primary search -- mTLS client certificate error analysis:**
```spl
index=proxy (sourcetype="traefik:log" OR sourcetype="traefik:access") earliest=-4h
| where match(_raw, "(?i)tls.*handshake|client.*cert|mutual.*tls|bad certificate|unknown.*ca|expired.*cert|certificate.*required|certificate.*verify")
| eval cert_error=case(match(_raw, "(?i)expired.*cert|certificate.*expired"), "CLIENT_CERT_EXPIRED", match(_raw, "(?i)unknown.*ca|untrusted|ca.*not.*found"), "UNTRUSTED_CA", match(_raw, "(?i)certificate.*required|no.*cert"), "NO_CLIENT_CERT", match(_raw, "(?i)bad.*certificate|invalid.*cert|verify.*fail"), "INVALID_CERT", match(_raw, "(?i)tls.*handshake.*fail"), "TLS_HANDSHAKE_FAIL", 1==1, "OTHER")
| rex "(?:from|client|addr)\s*[:=]?\s*(?<client_ip>[0-9.]+)"
| stats count as errors dc(client_ip) as affected_clients by cert_error
| eval severity=case(cert_error="UNTRUSTED_CA" AND errors > 50, "HIGH -- many untrusted CA errors", cert_error="CLIENT_CERT_EXPIRED", "WARNING -- expired client certificates", cert_error="NO_CLIENT_CERT", "WARNING -- clients without certificates", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -errors
```

### Step 3 — - Validate
(a) Connect without client cert: `curl -k https://<traefik>/` -- should fail if RequireAndVerifyClientCert.
(b) Connect with valid client cert: `curl --cert client.crt --key client.key https://<traefik>/` -- should succeed.
(c) Connect with expired cert and verify the error is logged.

### Step 4 — - Operationalize
Dashboard ("Traefik -- mTLS"):
* Row 1 -- Single-value: "Client cert errors (4h)", "Expired certs", "Untrusted CA", "Missing certs".
* Row 2 -- Certificate error breakdown.

Alerting:
* High (untrusted CA > 50): clients using certs from wrong CA.
* Warning (expired client certs): notify clients to renew.

### Step 5 — - Troubleshooting

* **UNTRUSTED_CA** -- Client certificate is signed by a CA not in `clientAuth.caFiles`. Add the client CA to the trust chain or issue client certs from the correct CA.

* **CLIENT_CERT_EXPIRED** -- Client needs to renew their certificate. If many clients affected simultaneously, check if the CA itself expired.

* **NO_CLIENT_CERT with VerifyClientCertIfGiven** -- Client is not sending a cert but the TLS option only verifies if given (optional). If you want to require certs, use RequireAndVerifyClientCert.

## SPL

```spl
index=proxy sourcetype="traefik:access"
| where DownstreamStatus==401 OR match(_raw, "(?i)(unknown ca|certificate required|handshake failure)")
| stats count by RouterName, ClientAddr
| where count > 15
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Traefik Mutual TLS Client Certificate Errors» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://doc.traefik.io/traefik/https/tls/)
