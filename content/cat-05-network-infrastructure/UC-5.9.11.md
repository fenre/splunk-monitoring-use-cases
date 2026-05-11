<!-- AUTO-GENERATED from UC-5.9.11.json — DO NOT EDIT -->

---
id: "5.9.11"
title: "BGP AS Path Monitoring"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.9.11 · BGP AS Path Monitoring

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Anomaly, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch which internet companies carry our traffic to make sure only the ones we've approved are handling it. If a stranger suddenly starts claiming they can reach us, that's like someone putting up a fake road sign — they might be trying to redirect our traffic through their network to spy on it or steal data.*

---

## Description

Tracks distinct BGP AS paths to each monitored prefix, flagging when traffic is routed through different Autonomous Systems than previously observed. An unexpected AS in the path could indicate a BGP route leak (an ISP accidentally re-announcing your prefix through unintended transit), a BGP hijack (a malicious actor originating your prefix from their AS), or a legitimate peering change by an upstream provider.

## Value

BGP hijacking is one of the most dangerous attacks on the internet — an attacker originates your prefix from their AS, causing some ISPs to route traffic destined for your network to the attacker instead. This enables traffic interception (MitM), credential theft, and service disruption. Notable examples: the 2018 Amazon Route 53 hijack that stole cryptocurrency, and repeated hijacks of bank and government prefixes. By monitoring AS paths in Splunk and alerting when a new, unexpected ASN appears — especially as the origin AS — the security team can detect hijacks within minutes and take countermeasures (announce more-specific prefixes, contact the offending ISP, update RPKI ROAs). Even for non-malicious events, knowing when your traffic takes a new AS path lets the WAN team verify the new path meets performance and compliance requirements (e.g., traffic must not transit through certain countries).

## Implementation

Uses the same Tests Stream — Metrics data as UC-5.9.8/9/10. The `network.as.path` attribute is a string field (not a metric), so it requires `values()` and `dc()` in stats to track distinct paths. Maintain a lookup of expected/approved AS paths per prefix to alert on truly unexpected paths vs known alternatives.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.8 apply — BGP tests configured, Tests Stream enabled, BGP data flowing.
- **Document your expected origin ASN(s).** For each monitored prefix, record which ASN(s) should legitimately originate it. Create a Splunk lookup `bgp_expected_origins.csv` with columns `prefix` and `expected_origin_as`. This lookup powers the hijack detection variant in Step 2.
- **RPKI status:** Know whether your prefixes have RPKI ROAs (Route Origin Authorizations) deployed. If they do, RPKI-enforcing ISPs will reject hijack attempts — but not all ISPs enforce RPKI, so monitoring in ThousandEyes remains essential.
- **Compliance requirements:** If your organization has data sovereignty requirements (e.g., traffic must not transit through certain countries), document which AS numbers correspond to ISPs in restricted countries. This UC can detect when traffic takes an unexpected path through a non-compliant AS.

### Step 1 — Configure data collection
Same as UC-5.9.8. No additional configuration. The `network.as.path` attribute is reported in the same BGP test events.

Verify AS path data:
```spl
index=thousandeyes_metrics thousandeyes.test.type="bgp" earliest=-30m
| stats values(network.as.path) as paths by network.prefix
| eval path_count = mvcount(paths)
```
You should see one or more AS paths per prefix. The path format is a space-separated list of ASNs, e.g., `64496 3356 2914 13335`.

### Step 2 — Create the search and alert
**Path change detection:**
```spl
`stream_index` thousandeyes.test.type="bgp"
| stats dc(network.as.path) as unique_paths values(network.as.path) as as_paths latest(network.as.path) as current_path by network.prefix, thousandeyes.monitor.name
| where unique_paths > 1
| sort -unique_paths
```

**Understanding this SPL**

`dc(network.as.path)` — counts distinct AS paths seen for each prefix-monitor pair. A value of 1 means the path was stable. > 1 means the AS path changed at least once during the search window.

`values(network.as.path)` — lists all observed AS paths so you can visually compare them. Look for differences in the transit ASNs (middle of the path) and especially the origin AS (rightmost ASN).

`latest(network.as.path)` — the most recently observed AS path (the current routing state).

**BGP hijack detection variant** (the critical security use case):
```spl
`stream_index` thousandeyes.test.type="bgp"
| eval origin_as = mvindex(split(network.as.path, " "), -1)
| stats dc(origin_as) as unique_origins values(origin_as) as origins latest(origin_as) as current_origin by network.prefix
| lookup bgp_expected_origins prefix as network.prefix OUTPUT expected_origin_as
| where unique_origins > 1 OR current_origin != expected_origin_as
| eval alert_type = case(
    isnotnull(expected_origin_as) AND current_origin != expected_origin_as, "POTENTIAL HIJACK — origin AS mismatch",
    unique_origins > 1, "ORIGIN AS CHANGED — investigate",
    1=1, "UNKNOWN")
| sort -alert_type
```

This extracts the origin AS (rightmost ASN in the path) and compares it against your expected origin lookup. A mismatch is the strongest indicator of a BGP hijack.

**Why the origin AS matters most:** In a BGP hijack, the attacker announces YOUR prefix from THEIR AS. This changes the origin AS. Transit AS changes are far more common and usually benign (ISP peering changes). Origin AS changes are rare and almost always significant.

**Data sovereignty variant** (for compliance monitoring):
```spl
`stream_index` thousandeyes.test.type="bgp"
| eval as_list = split(network.as.path, " ")
| mvexpand as_list
| lookup as_country_mapping asn as as_list OUTPUT country
| stats values(country) as transit_countries by network.prefix, thousandeyes.monitor.name, network.as.path
| search transit_countries="<restricted_country>"
```
This variant checks whether any ASN in the path maps to a restricted country using a lookup table of ASN-to-country mappings (available from RIPE NCC's RIS database).

**Scheduling:** For hijack detection: cron `*/15 * * * *`, time range `-30m to now`. This is a security-critical alert — do NOT suppress for more than 30 minutes. For general path change monitoring: cron `*/30 * * * *`, time range `-4h to now`, throttle by `network.prefix` for 4 hours.

### Step 3 — Validate
(a) **Verify origin AS extraction.** Run the hijack detection variant and confirm the `current_origin` field matches your actual origin ASN. You can verify your origin ASN at bgp.he.net or routeviews.org.

(b) **Populate the expected origins lookup.** Create `bgp_expected_origins.csv` in your app's `lookups/` directory:
```csv
prefix,expected_origin_as
203.0.113.0/24,64496
198.51.100.0/24,64496
```

(c) **Test with a known path.** For a stable prefix, `unique_origins` should be 1 and `current_origin` should match your expected ASN.

(d) **Verify multi-homing visibility.** If your prefix is multihomed, you'll see multiple unique AS paths (different transit ASNs) but the origin AS should be the same in all of them. If `unique_origins > 1` for a single-homed prefix, that's a strong hijack indicator.

### Step 4 — Operationalize
**Dashboard** (add as the security row in the UC-5.9.8 "BGP Prefix Health" dashboard):
- CRITICAL alert panel: origin AS mismatch detection, red background if any prefix shows a non-expected origin.
- Table: prefix | expected origin AS | current origin AS | status (MATCH / MISMATCH) | unique paths | all observed paths.
- Timeline: AS path changes over 24 hours with markers at each change event.

**Alerting:**
- **Origin AS mismatch → CRITICAL security alert.** Immediate page to NOC AND Security team. This may be a BGP hijack.
- **Transit AS change (origin unchanged) → Informational.** Notify network engineering via Slack/Teams.

**Runbook — BGP Hijack Response** (owner: Security + Network Engineering, joint response):
1. **Confirm the hijack.** Verify the origin AS mismatch in ThousandEyes BGP Route Visualization. Cross-reference with bgp.he.net and routeviews.org. Check whether the unexpected origin AS is known (ISP vs unknown).
2. **Assess impact.** Check reachability (UC-5.9.8) — how many monitors are routing to the hijacker's AS instead of yours?
3. **Immediate mitigation:** Announce more-specific sub-prefixes. If your hijacked prefix is a /24, you can announce two /25s. Most ISPs will prefer the more-specific route, routing traffic back to your network. (Note: /25s may not be accepted by all ISPs.)
4. **Contact the offending ISP.** Use the origin ASN to identify the ISP (bgp.he.net shows ASN ownership). Contact their NOC and abuse desk with evidence from ThousandEyes.
5. **Update RPKI.** If you don't have ROAs, create them immediately to prevent future hijacks from RPKI-enforcing ISPs. If you have ROAs, verify they are valid and correct.
6. **Engage your upstream ISP.** Ask your upstream to apply BGP communities or filters to prevent the hijacked prefix from being preferred over your legitimate announcement.
7. **Document and post-mortem.** Record the timeline, impact, and response for the security incident report.

### Step 5 — Troubleshooting

- **`network.as.path` is empty or missing** — The field may be named differently in your app version. Check `| fieldsummary | search field=*path*` or `| fieldsummary | search field=*as*` to find the correct field name.

- **Origin AS extraction returns null** — The `split()` function requires the AS path to be a space-separated string. If the path uses a different delimiter (commas, pipes), adjust the split character.

- **Expected origins lookup not matching** — Verify the lookup file is in the correct app directory, the field names match, and the prefix format matches exactly (e.g., `203.0.113.0/24` in both the data and the lookup).

- **All common troubleshooting** — See UC-5.9.8 and UC-5.9.1 Step 5.

## SPL

```spl
`stream_index` thousandeyes.test.type="bgp"
| stats dc(network.as.path) as unique_paths values(network.as.path) as as_paths latest(network.as.path) as current_path by network.prefix, thousandeyes.monitor.name
| where unique_paths > 1
| sort -unique_paths
```

## Visualization

(1) Table: prefix, monitor, unique path count, all observed AS paths, current AS path — sorted by unique_paths descending. Highlight rows where the origin AS (rightmost ASN) changed. (2) Timeline: path change events with AS path diff showing which ASNs appeared/disappeared. (3) Alert panel: new origin AS detected (potential hijack indicator). (4) Drilldown to ThousandEyes BGP Route Visualization.

## Known False Positives

**Normal upstream ISP path selection variation.** When your prefix is multihomed through multiple ISPs, different monitors will naturally see different AS paths (via ISP-A vs ISP-B). The number of unique paths for a multihomed prefix is typically 2–5 and stable over time. This is not a path change — it's multiple simultaneous paths. Distinguish by checking whether the `dc(network.as.path)` count is consistent with your known upstream count.

**AS path prepending changes.** When your network team or an upstream ISP adds or removes AS path prepending (e.g., changing from `64496 64496 64496` to `64496`), the path changes in length but the ASNs in the path remain the same. This is benign traffic engineering. Distinguish by checking whether the same ASNs are present in both the old and new paths, just with different repetition.

**Transit provider swap by upstream ISP.** Your ISP may change its upstream transit provider (e.g., from Cogent to Lumen), causing the transit ASN in the path to change. The origin AS remains yours, and reachability is maintained. Distinguish by verifying the origin AS is still your AS and that reachability (UC-5.9.8) is 100%.

**IXP route server ASN visibility.** At some Internet Exchange Points, the route server's ASN appears briefly in the path during convergence, then is removed. This produces a transient path change that's an artifact of the exchange point's route server configuration.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes BGP Route Monitoring — AS path visibility](https://docs.thousandeyes.com/product-documentation/internet-and-wan-monitoring/tests/)
- [NIST — Securing BGP and RPKI](https://www.nist.gov/publications/)
- [Cloudflare — How BGP hijacking works and how to prevent it](https://www.cloudflare.com/learning/security/glossary/bgp-hijacking/)
