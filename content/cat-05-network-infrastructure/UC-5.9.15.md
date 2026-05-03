<!-- AUTO-GENERATED from UC-5.9.15.json — DO NOT EDIT -->

---
id: "5.9.15"
title: "DNSSEC Validity Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.9.15 · DNSSEC Validity Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Availability, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We check that the digital signatures on our domain names are valid — because if the security seal is broken, some internet providers will refuse to deliver our address at all, even though the actual website is fine.*

---

## Description

Monitors the DNSSEC chain of trust for signed domains, alerting when any agent detects a validation failure. DNSSEC validation failures cause hard DNS resolution failures for DNSSEC-enforcing resolvers — not slow resolution, but complete failure to resolve the domain. This is particularly dangerous because non-enforcing resolvers continue to work, making the outage appear sporadic and hard to diagnose.

## Value

DNSSEC is designed to prevent DNS spoofing attacks, but a broken DNSSEC chain is worse than no DNSSEC at all. Without DNSSEC, a resolver returns the (potentially spoofed) answer and the user reaches something. With broken DNSSEC, an enforcing resolver returns SERVFAIL and the user reaches nothing. As more ISPs and enterprises deploy DNSSEC validation (Google Public DNS, Cloudflare, Comcast, and many European ISPs enforce it), a broken DNSSEC chain affects an increasingly large fraction of your users. The insidious part: your internal monitoring may use non-validating resolvers and see no problem, while millions of users behind validating resolvers are blacked out. ThousandEyes DNSSEC tests catch this by actually performing DNSSEC validation from agents worldwide, detecting broken chains before your customers do.

## Implementation

Create DNSSEC tests in ThousandEyes: **Cloud & Enterprise Agents → Test Settings → Add New Test → DNS → DNSSEC**. Enter the domain name to validate (must be a DNSSEC-signed domain). ThousandEyes will validate the complete chain from root to authoritative zone.

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, Tests Stream — Metrics input enabled).
- **DNSSEC tests configured in ThousandEyes.** Navigate to **Cloud & Enterprise Agents → Test Settings → Add New Test → DNS → DNSSEC**. Enter the domain to validate. Only domains with DNSSEC signing enabled can be tested — if the domain is not signed, the test will report validation failures (because there's nothing to validate).
- **Domain must be DNSSEC-signed.** Verify with `dig DNSKEY example.com` — you should see DNSKEY records. Also check `dig DS example.com` at the parent zone to confirm the DS record is present.
- **Understand your DNSSEC architecture.** Know:
  - Who signs the zone (internal BIND/Knot, cloud provider like Route 53/Cloudflare, managed DNS service)
  - Key rollover schedule and process (automated RFC 7583 vs manual)
  - Where the DS record is managed (registrar, parent zone operator)
  - RRSIG signature validity period (typical: 7–30 days, resign interval: daily)
- **DNSSEC validation tools for triage:** dnsviz.net, dnssec-debugger.verisignlabs.com, `delv` (BIND 9.10+), `drill -DT` (ldns).

### Step 1 — Configure data collection
DNSSEC test metrics flow through the same Tests Stream — Metrics OTel input. Verify:
```spl
index=thousandeyes_metrics thousandeyes.test.type="dns-dnssec" earliest=-30m
| stats count avg(dns.lookup.validity) as avg_validity by dns.question.name
```

### Step 2 — Create the search and alert
```spl
`stream_index` thousandeyes.test.type="dns-dnssec"
| stats avg(dns.lookup.validity) as avg_validity min(dns.lookup.validity) as min_validity by dns.question.name, thousandeyes.source.agent.name
| where avg_validity < 100
| sort avg_validity
```

**Understanding this SPL**

`thousandeyes.test.type="dns-dnssec"` — filters to DNSSEC validation tests specifically.

`dns.lookup.validity` — 100% when the full DNSSEC chain validates, 0% when any part fails. There is no "partial" validity — DNSSEC either validates completely or fails completely.

`where avg_validity < 100` — ANY validity failure is critical. DNSSEC failures cause hard SERVFAIL responses from validating resolvers. This is not a performance issue — it's an availability issue for a significant fraction of users.

**Aggregate domain-level alert:**
```spl
`stream_index` thousandeyes.test.type="dns-dnssec"
| stats avg(dns.lookup.validity) as avg_validity dc(thousandeyes.source.agent.name) as total_agents by dns.question.name
| eval failing_agents = round(total_agents * (100 - avg_validity) / 100, 0)
| where avg_validity < 100
| sort avg_validity
```

**Scheduling:** cron `*/5 * * * *`, time range `-15m to now`. DNSSEC failures are critical — use a 5-minute schedule. Throttle by `dns.question.name` for 1 hour maximum (shorter than most UCs because DNSSEC failures are time-sensitive — every hour of broken DNSSEC compounds the user impact).

### Step 3 — Validate
(a) **Verify DNSSEC is working.** Use dnsviz.net or Verisign's DNSSEC debugger to visualize your domain's DNSSEC chain. All links should be green/valid.

(b) **Cross-reference with ThousandEyes UI.** Navigate to the DNSSEC test view. The UI shows validity status per agent with detailed error messages (e.g., "RRSIG expired", "Missing DS record", "DNSKEY mismatch").

(c) **Confirm the domain is actually DNSSEC-signed.** `dig DNSKEY <domain> +short` should return one or more DNSKEY records. If it returns nothing, the domain is not signed and the test will always fail.

### Step 4 — Operationalize
**Dashboard** (add as a security row in the UC-5.9.13 "DNS Health" dashboard):
- Single value per signed domain: DNSSEC validity % (red if < 100%). This is a binary indicator — either the chain is valid or it's not.
- Timeline: validity over time showing exactly when failures started (critical for correlating with key rollover events).

**Alerting:**
- DNSSEC validity < 100% → CRITICAL alert. Immediate page to DNS team AND security team. Include domain name, number of affected agents, and link to dnsviz.net visualization.

**Runbook — DNSSEC Failure Response** (owner: DNS team):
1. **Confirm the failure.** Check dnsviz.net for the domain. Identify which part of the chain is broken (root, TLD, authoritative zone).
2. **If RRSIG expired:** The signing system stopped re-signing the zone. Restart the signing process and re-sign immediately. Verify with `dig RRSIG <domain>`.
3. **If DS record mismatch:** A key rollover occurred but the DS record at the parent zone wasn't updated (or was updated incorrectly). Contact your registrar to update the DS record. This is the #1 cause of DNSSEC outages.
4. **If DNSKEY missing:** The signing key was deleted or the zone was replaced with an unsigned version. Restore the DNSKEY records and re-sign.
5. **Emergency mitigation:** If you cannot fix the DNSSEC chain immediately, consider temporarily removing DNSSEC by withdrawing the DS record from the parent zone. This converts your domain back to unsigned DNS (vulnerable to spoofing but at least reachable). This is a last resort — coordinate with security.

### Step 5 — Troubleshooting

- **Validity always 0% for all agents** — The domain may not be DNSSEC-signed, or the DNSSEC chain may be fundamentally broken. Verify with `dig DNSKEY <domain>` and dnsviz.net.

- **Validity drops to 0% briefly every N days** — RRSIG signatures are expiring and being re-signed. If the re-signing happens slightly after expiration rather than before, there's a brief window of invalid signatures. Fix by adjusting the resign interval to run well before expiration (e.g., re-sign when RRSIG has 50% lifetime remaining).

- **`dns.lookup.validity` field missing** — The field name may differ in your version. Check `| fieldsummary | search field=dns*`.

- **All common troubleshooting** — See UC-5.9.1 Step 5.

## SPL

```spl
`stream_index` thousandeyes.test.type="dns-dnssec"
| stats avg(dns.lookup.validity) as avg_validity min(dns.lookup.validity) as min_validity by dns.question.name, thousandeyes.source.agent.name
| where avg_validity < 100
| sort avg_validity
```

## Visualization

(1) Single value per domain: DNSSEC validity % (red if < 100%). (2) Timechart: validity over time per domain — a drop from 100% to 0% is immediately visible and demands immediate action. (3) Table: domain, agent, validity %, min validity — sorted worst-first. (4) Combined with UC-5.9.13 (DNS availability) to correlate DNSSEC failures with DNS availability drops.

## Known False Positives

**Key rollover in progress.** During a planned DNSSEC Key Signing Key (KSK) or Zone Signing Key (ZSK) rollover, there is a brief window where some resolvers have the old key and some have the new key. Depending on timing, ThousandEyes may report validity failures during the rollover. Distinguish by checking whether the failure is brief (< 2 hours) and corresponds to a planned key rollover in your DNS management system. Well-executed rollovers (RFC 7583 timings) should not cause validation failures.

**Parent zone DS record propagation delay.** After updating your DNSKEY and requesting a DS record update at the parent zone (registrar), there's a propagation delay (24–48 hours for some TLDs) before all resolvers see the new DS record. During this window, some agents may report validity failures. This is the most common cause of real DNSSEC outages — failure to coordinate DS record updates with key rollovers.

**Resolver-side DNSSEC configuration issue.** Some agents may use resolvers that have broken DNSSEC validation themselves (wrong trust anchor, clock skew affecting signature validation). If only one agent shows failures while all others show 100%, the problem is likely that agent's resolver, not your DNSSEC chain. Distinguish by checking whether the failure is isolated to one agent.

**Expired RRSIG signatures.** RRSIG records have an expiration time. If your DNSSEC signing system stops signing (software crash, expired HSM certificate, key rotation failure), the RRSIG records expire and validation fails. This is a real DNSSEC failure, not a false positive — but the root cause is your signing infrastructure, not the DNS infrastructure.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes DNSSEC Test Configuration](https://docs.thousandeyes.com/product-documentation/internet-and-wan-monitoring/tests/dns-tests/dnssec-test)
- [DNSSEC Deployment Guide — ICANN](https://www.icann.org/resources/pages/dnssec-what-is-it-why-important-2019-03-05-en)
- [DNSSEC Debugger — Verisign Labs](https://dnssec-debugger.verisignlabs.com/)
