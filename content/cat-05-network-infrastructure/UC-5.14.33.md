<!-- AUTO-GENERATED from UC-5.14.33.json — DO NOT EDIT -->

---
id: "5.14.33"
title: "Squid SSL Bump Peek-and-Splice Decision Audit"
status: "draft"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.14.33 · Squid SSL Bump Peek-and-Splice Decision Audit

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Security, Compliance &middot; **Status:** Draft

*We watch squid ssl bump peek-and-splice decision audit and catch issues early, before they turn into outages for the people who rely on the network.*

---

## Description

Regulators expect proof of what is inspected versus passed through.

## Value

Operations teams audit Squid SSL bump peek-and-splice decisions, tracking which HTTPS connections are decrypted (bumped) vs bypassed (spliced) for compliance and security visibility.

## Implementation

Restrict index permissions; follow jurisdiction on TLS inspection. Redact sensitive domains in exports.

## Detailed Implementation

### Prerequisites
* Squid logs with SSL bump events. Data in `index=proxy` with `sourcetype=squid:access` or `sourcetype=squid:cache`. Key events: ssl_bump (splice, peek, bump, stare, terminate), SSL error codes.
* SSL bump peek-and-splice: Squid intercepts HTTPS traffic. In "peek" mode, Squid examines the Client Hello SNI and server certificate without decrypting. In "splice" mode, it creates a tunnel (no decryption). In "bump" mode, it decrypts and re-encrypts (full MITM). Decisions are made per-connection based on ACLs. Key security: audit which connections are bumped (decrypted) vs spliced (bypassed).

### Step 1 — - Configure data collection
```
# squid.conf -- SSL bump
http_port 3128 ssl-bump cert=/etc/squid/certs/squid-ca.pem generate-host-certificates=on

acl step1 at_step SslBump1
acl step2 at_step SslBump2
acl step3 at_step SslBump3
acl banking dstdomain .bank.example.com .finance.example.com
ssl_bump peek step1 all
ssl_bump splice banking
ssl_bump bump step2 all
```
Verify:
```spl
index=proxy (sourcetype="squid:access" OR sourcetype="squid:cache") earliest=-4h
| where match(_raw, "(?i)ssl_bump|SPLICE|BUMP|PEEK|ssl_crtd|TERMINATE")
| stats count by _raw | head 20
```

### Step 2 — - Create the search and alert

**Primary search -- SSL bump decision audit:**
```spl
index=proxy (sourcetype="squid:access" OR sourcetype="squid:cache") earliest=-4h
| where match(_raw, "(?i)ssl_bump|SPLICE|BUMP|ssl_crtd|cert.gen")
| eval bump_action=case(match(_raw, "(?i)SPLICE|splice"), "SPLICE_BYPASS", match(_raw, "(?i)BUMP|bump"), "BUMP_DECRYPT", match(_raw, "(?i)PEEK|peek"), "PEEK_ONLY", match(_raw, "(?i)TERMINATE|terminate"), "TERMINATE", match(_raw, "(?i)ssl.*error|cert.*fail|cert.*gen.*fail"), "SSL_ERROR", 1==1, "OTHER")
| rex field=request_url "(?:CONNECT\s+)?(?<ssl_domain>[^:/ ]+)"
| stats count as connections dc(ssl_domain) as unique_domains values(ssl_domain) as sample_domains by bump_action
| eval severity=case(bump_action="SSL_ERROR", "HIGH -- SSL certificate generation errors", bump_action="TERMINATE", "WARNING -- terminated connections", bump_action="SPLICE_BYPASS" AND connections > 1000, "INFO -- heavy spliced traffic (not inspected)", 1==1, "INFO")
| where severity != "INFO" OR bump_action="SPLICE_BYPASS"
| sort severity, -connections
```

### Step 3 — - Validate
(a) Access a banking site -- should be SPLICE (bypassed).
(b) Access a regular HTTPS site -- should be BUMP (decrypted).
(c) Check certificate generation: `ls /var/lib/squid/ssl_db/` -- should contain generated certs.

### Step 4 — - Operationalize
Dashboard ("Squid -- SSL Bump Audit"):
* Row 1 -- Single-value: "Bumped (decrypted)", "Spliced (bypassed)", "SSL errors", "Terminated".
* Row 2 -- Bump vs splice ratio per domain category.

Alerting:
* High (SSL errors > 50): certificate generation or validation issues.
* Info (splice ratio report): periodic audit of what traffic is not being inspected.

### Step 5 — - Troubleshooting

* **SSL errors / cert generation failures** -- Check: (1) CA certificate is valid and not expired, (2) `ssl_crtd` helper is running, (3) disk space for cert DB (`/var/lib/squid/ssl_db/`).

* **All traffic being spliced** -- ACL order issue. `ssl_bump splice all` may appear before `ssl_bump bump`. Check order -- first match wins.

* **Client certificate errors after bumping** -- SSL bump breaks end-to-end certificate validation. Clients need the Squid CA installed as a trusted root. Distribute via GPO or MDM.

## SPL

```spl
index=proxy sourcetype="squid:access"
| where match(_raw, "(?i)bump|splice|peek|SSL_")
| stats count by ssl_bump_action, dst_domain
| sort - count
| head 50
```

## Visualization

Time series for rates and latency, top/dedup for hotspots, single-value alerts on health thresholds.

## Known False Positives

Edge cases: multi-vendor mixes and ad hoc feeds can include lab traffic and partial visibility that mimics issues until scopes are defined. Tuning tip: match this to «Squid SSL Bump Peek-and-Splice Decision Audit» and exclude change windows, scans, and lab VLANs you already expect.

## References

- [Vendor documentation](http://www.squid-cache.org/Doc/config/ssl_bump/)
