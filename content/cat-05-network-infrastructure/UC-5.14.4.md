<!-- AUTO-GENERATED from UC-5.14.4.json — DO NOT EDIT -->

---
id: "5.14.4"
title: "HAProxy SSL/TLS Handshake Failure Rate"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.4 · HAProxy SSL/TLS Handshake Failure Rate

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Security, Availability &middot; **Status:** Draft

*We watch haproxy ssl/tls handshake failure rate and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

TLS failures block whole cohorts of clients and often precede major incidents after renewals.

## Value

Operations teams classify HAProxy SSL/TLS handshake failures by root cause (expired cert, cipher mismatch, SNI mismatch, client cert errors), enabling targeted resolution of HTTPS connection failures.

## Implementation

Enable sufficient TLS logging without secrets. Join failure spikes with certificate inventory expiry.

## Detailed Implementation

### Prerequisites
* HAProxy syslog including SSL/TLS handshake events. Key fields: `ssl_fc_err` (frontend SSL error code), `ssl_bc_err` (backend SSL error code), `ssl_fc_protocol`, `ssl_fc_cipher`, `client_ip`.
* SSL handshake failures prevent clients from connecting. Common causes: (1) expired certificate, (2) cipher mismatch, (3) TLS version incompatibility, (4) SNI mismatch, (5) client certificate validation failure.

### Step 1 — - Configure data collection
Enable SSL logging:
```
# haproxy.cfg
frontend https_front
    bind *:443 ssl crt /etc/haproxy/certs/ alpn h2,http/1.1
    log-format "%ci:%cp [%t] %ft %b/%s %Tq/%Tw/%Tc/%Tr/%Tt %ST %B %CC %CS %tsc %ac/%fc/%bc/%sc/%rc %sq/%bq ssl_fc_err:%[ssl_fc_err] ssl_c_verify:%[ssl_c_verify] sni:%[ssl_fc_sni]"
```
Verify:
```spl
index=proxy sourcetype="haproxy:http" earliest=-4h
| where match(_raw, "ssl_fc_err:[1-9]") OR match(_raw, "(?i)ssl.*error|handshake.*fail")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- SSL handshake failure analysis:**
```spl
index=proxy (sourcetype="haproxy:http" OR sourcetype="haproxy:syslog") earliest=-4h
| where match(_raw, "ssl_fc_err:[1-9]") OR match(_raw, "(?i)ssl.*error|handshake.*fail|tls.*alert")
| rex "ssl_fc_err:(?<ssl_err>\d+)"
| rex "ssl_c_verify:(?<verify_err>\d+)"
| rex "sni:(?<sni>\S+)"
| eval failure_reason=case(ssl_err="1", "SSL_ERROR -- unspecified", ssl_err="2", "WANT_READ -- incomplete handshake", match(_raw, "(?i)no shared cipher"), "CIPHER_MISMATCH", match(_raw, "(?i)certificate.*expired"), "CERT_EXPIRED", match(_raw, "(?i)unknown.*ca|self.signed"), "UNTRUSTED_CA", match(_raw, "(?i)sni.*mismatch|no.matching.sni"), "SNI_MISMATCH", verify_err="26" OR verify_err="10", "CLIENT_CERT_EXPIRED", 1==1, "OTHER (err=".coalesce(ssl_err, "?").")")
| stats count as failures dc(client_ip) as affected_clients values(sni) as snis by failure_reason
| eval severity=case(failure_reason="CERT_EXPIRED", "CRITICAL", failures > 100, "HIGH", 1==1, "WARNING")
| sort severity, -failures
```

### Step 3 — - Validate
(a) Test with an old TLS version: `openssl s_client -tls1 -connect <haproxy>:443` -- should fail if TLS 1.0 is disabled.
(b) Test with wrong SNI: `openssl s_client -servername wrong.example.com -connect <haproxy>:443`.
(c) Check certificate validity: `echo | openssl s_client -connect <haproxy>:443 | openssl x509 -noout -dates`.

### Step 4 — - Operationalize
Dashboard ("HAProxy -- SSL Health"):
* Row 1 -- Single-value: "SSL failures (4h)", "Expired cert errors", "Cipher mismatches", "Affected clients".
* Row 2 -- SSL failure breakdown by reason.

Alerting:
* Critical (CERT_EXPIRED failures): certificate has expired -- renew immediately.
* Warning (cipher mismatch > 50): clients can't negotiate SSL -- check cipher suite.

### Step 5 — - Troubleshooting

* **CIPHER_MISMATCH** -- HAProxy cipher list doesn't include ciphers the client supports. Check: `ssl-default-bind-ciphers` in haproxy.cfg. For modern compatibility: `ssl-default-bind-ciphersuites TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256`.

* **SNI_MISMATCH** -- Client is requesting a hostname not covered by any configured certificate. Check: `crt` directive should point to a directory with all needed certs, or use `crt-list`.

* **CLIENT_CERT_EXPIRED** -- Client-side certificate has expired. Notify the client/user to renew their certificate.

## SPL

```spl
index=proxy sourcetype="haproxy:http"
| regex _raw="(?i)(SSL handshake failure|verify error|alert unknown ca|alert certificate)"
| bin _time span=5m
| stats count by frontend, _time
| where count > 20
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «HAProxy SSL/TLS Handshake Failure Rate» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](https://docs.haproxy.org/2.8/configuration.html#5.1)
