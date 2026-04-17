# DA-ESS-monitoring-use-cases — Enterprise Security Content Pack

A Splunk Enterprise Security (ES) content pack derived from the
security-relevant categories of the
[Splunk Monitoring Use Cases](https://github.com/fenre/splunk-monitoring-use-cases)
catalog.  Ships correlation searches with MITRE ATT&CK mappings,
CIM-aligned eventtypes, and risk-based-alerting seeds.

## What it contains

| Configuration                                  | Stanzas        | Purpose                                                                 |
|------------------------------------------------|---------------:|-------------------------------------------------------------------------|
| `default/savedsearches.conf`                   | ~650            | Correlation searches (critical + high criticality from cat 9/10/14/17/22) |
| `default/governance.conf`                      | ~500            | MITRE ATT&CK technique + tactic mappings per correlation search         |
| `default/analytic_stories.conf`                | ~14             | Analytic Stories grouping correlation searches by ATT&CK tactic         |
| `default/eventtypes.conf`                      | 10              | CIM-aligned shortcuts (`ess_auth_fail`, `ess_endpoint_process`, …)      |
| `default/tags.conf`                            | 10              | CIM tags applied to the eventtypes                                      |
| `metadata/default.meta`                        | —               | Global export so ES consumes the content from any app context           |

> **Note** — only security categories 9 (Identity), 10 (Endpoint),
> 14 (OT/ICS), 17 (Zero Trust), and 22 (Compliance) are promoted to ES
> correlation searches.  Operational categories remain in the
> non-security TA.

## Selection logic

A UC is promoted to a correlation search when **all** of these hold:

1. Its SPL starts with `index=`, `search index=`, or `| tstats`
   (filter-first — required for notable-event generation).
2. It contains an aggregation (`| stats`, `| tstats`, `| timechart`,
   `| where`, `| dedup`, or `| streamstats`) — correlation searches must
   reduce to detection rows.
3. Its category is one of 9, 10, 14, 17, or 22 (see roadmap `v5.1`).

The default pack caps selection to 400 critical + 250 high-criticality
UCs.  Re-run `python3 scripts/build_es.py --include-all` to produce the
full 1,800+ correlation search pack.

## Prerequisites

- Splunk Enterprise Security ≥ 7.0 on the search head.
- Splunk Common Information Model (CIM) ≥ 5.3 with the relevant data
  models (Authentication, Endpoint, Network_Traffic, …) accelerated.
- Upstream TAs producing CIM-compliant events (Splunk_TA_windows,
  Splunk_TA_nix, Splunk Add-on for Okta, Splunk Add-on for AWS, …).

## Installation

1. Install `DA-ESS-monitoring-use-cases-<version>.spl` from the
   [Releases page](https://github.com/fenre/splunk-monitoring-use-cases/releases)
   or run `bash scripts/package_es.sh` locally.
2. In Splunk Web: *Apps → Manage Apps → Install app from file*.
3. Open ES → *Configure → Content Management* — filter by app
   `DA-ESS-monitoring-use-cases` to see the installed correlation
   searches.
4. **All correlation searches ship disabled**.  Review each search,
   adjust indexes and thresholds to your environment, and enable
   deliberately.
5. (Optional) Enable Risk-Based Alerting per correlation search by
   setting `action.risk = 1` and adjusting `_risk_object` /
   `_risk_object_type` to your asset/identity lookups.

## Governance & MITRE mapping

Each correlation search that has one or more MITRE technique IDs in the
catalog writes a matching stanza in `governance.conf`:

```ini
[ESCS-9.1.1 - Brute-Force Login Detection]
governance = mitre_attack
mitre_attack = T1110,T1110.001
mitre_attack_tactics = Credential Access
```

The derivation rule: tactic = `TACTIC_BY_PREFIX[T<id>.split('.',1)[0]]`.
Adjust the map in `scripts/build_es.py` if you need different bucketing.

## Risk-Based Alerting (RBA) seeds

All correlation searches contain disabled RBA parameters:

```ini
action.risk = 0
action.risk.param._risk_score = 40
action.risk.param._risk_object = host
action.risk.param._risk_object_type = system
```

To enable RBA:

1. Add customer-specific asset and identity lookups.
2. Set `action.risk = 1` per search.
3. Tune `_risk_score` per severity (e.g. 20/40/60/80).
4. Map `_risk_object` to the CIM-normalised field your data actually
   contains (`user`, `src`, `dest`, …) — do not leave it at `host`
   unconditionally.

## Regenerating content

```bash
python3 scripts/build_es.py                 # default capped pack
python3 scripts/build_es.py --include-all   # every security UC
```

## Support and licence

- Upstream project: <https://github.com/fenre/splunk-monitoring-use-cases>
- Licence: MIT (see `LICENSE`).
- This pack is a **community project** — not an officially supported
  Splunk product.  Review every correlation search before enabling.
