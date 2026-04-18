# Splunk UC Recommender

App ID: `splunk-uc-recommender`  
App version: **6.0.0**  
Generated: `2026-04-17T16:48:56Z`  
Upstream catalogue: [fenre/splunk-monitoring-use-cases](https://github.com/fenre/splunk-monitoring-use-cases)

This app does **two** things in one Splunk install:

1. **Recommends** monitoring use cases from the upstream
   [Splunk Monitoring Use Cases catalogue](https://fenre.github.io/splunk-monitoring-use-cases/api/v1) based on
   what is actually deployed in your environment (sourcetypes, indexes,
   CIM acceleration, installed apps).
2. **Bundles** every tier-1 compliance use case from the same
   catalogue — CMMC, EU DORA, GDPR, HIPAA Security, ISO/IEC 27001,
   NIS2, NIST SP 800-53, NIST CSF, PCI DSS, SOC 2, SOX ITGC — as
   disabled-by-default saved searches plus one merged
   `uc_compliance_mappings` lookup, so you do not need to install one
   app per regulation.

It is **preview-only by default**: the recommender side never writes
saved searches automatically. Every recommendation ships with a
"Copy SPL" button and a deep-link into the Search & Reporting app so
operators can review, adapt, and save the search themselves. The
bundled compliance saved searches are also `disabled = 1`/
`is_scheduled = 0` until an operator opens the **Compliance** view,
filters by regulation, and explicitly enables the ones they want.

## How it works

1. Four low-cost scheduled searches under
   `default/savedsearches.conf` populate the `uc_recommender_inventory`
   KV store with your active sourcetypes, indexes, CIM acceleration
   status, and installed apps.
2. When you open the **Recommend** dashboard, a small piece of
   JavaScript under `appserver/static/js/recommender.js`:
   * reads the inventory via a search job
     (`| inputlookup uc_recommender_inventory`);
   * fetches four JSON indexes from the upstream API:
     - `/api/v1/recommender/sourcetype-index.json`
     - `/api/v1/recommender/cim-index.json`
     - `/api/v1/recommender/app-index.json`
     - `/api/v1/recommender/uc-thin.json`
   * joins them, scores each UC (exact sourcetype match = 3, fuzzy = 1,
     CIM accelerated = 2, matching app = 1, × criticality weight), and
     renders the top 60 cards.
3. Clicking **Details** loads the full compliance sidecar from
   `/api/v1/compliance/ucs/<id>.json` for the 1 200+ compliance-tagged
   UCs.
4. The **Compliance** view reads
   `lookups/uc_compliance_mappings.csv` (also written by the
   generator) so operators can pick a regulation, see every bundled
   UC that satisfies a clause, and click straight through to the
   saved-search definition to enable it.

The app only talks to the hard-coded allow-list of upstream hosts
(currently `https://fenre.github.io`). The **Settings** tab lets
operators override the API base URL; the override is validated against
the allow-list and stored in `localStorage` before it is used.

## Requirements

* Splunk Enterprise or Splunk Cloud, version 9.2+
* Outbound HTTPS from the search head to
  `https://fenre.github.io/splunk-monitoring-use-cases/api/v1/`
* KV store enabled (default on every supported deployment)

## Install

```
tar czf splunk-uc-recommender.spl splunk-uc-recommender/
# Upload via Settings → Manage Apps → Install from file
```

After install, open **Apps → Splunk UC Recommender**. The first
inventory refresh runs 30 minutes later. Hit **Settings → Manual
scan** to kick one off immediately.

## Splunk Cloud compatibility

* No `commands.conf`, `restmap.conf`, `web.conf[expose:*]`, or
  `[script://]` inputs.
* Only built-in SPL commands (`metadata`, `eventcount`, `tstats`,
  `rest`, `inputlookup`, `outputlookup`).
* All browser-side logic is bundled under `appserver/static/`.
* Outbound fetch calls are restricted to an explicit allow-list with
  `credentials: 'omit'`.

## AppInspect readiness

* `app.manifest` v2.0.0 with full `info` block.
* `metadata/default.meta` keeps saved searches private and exports
  macros, lookups, and eventtypes as `system`.
* MIT `LICENSE` at the app root.
* No local/ overrides shipped; all defaults live under `default/`.

## Files in this app

```
splunk-uc-recommender/
├── app.manifest
├── README.md
├── LICENSE
├── default/
│   ├── app.conf
│   ├── savedsearches.conf       # 4 Cloud-safe scan searches
│   │                            # + every tier-1 compliance UC, disabled
│   ├── collections.conf         # KV: uc_recommender_inventory + scan_runs
│   ├── transforms.conf          # KV + CSV lookup definitions
│   ├── macros.conf              # uc_recommender_* + uc_compliance_* macros
│   ├── eventtypes.conf          # recommender + per-(reg, family) eventtypes
│   ├── tags.conf
│   └── data/ui/
│       ├── nav/default.xml      # Recommend · Scan · Browse · Compliance ·
│       │                        # Studio · Settings · Search
│       └── views/
│           ├── recommend.xml    # primary recommendation page
│           ├── scan.xml         # raw inventory tables
│           ├── browse.xml       # full catalogue filter
│           ├── compliance.xml   # filter bundled UCs by regulation/clause
│           ├── settings.xml     # API base URL override, reset
│           ├── recommend_studio.xml
│           └── recommend.json   # Dashboard Studio v2 layout
├── appserver/static/
│   ├── js/
│   │   ├── recommender.js       # main UI, AMD module
│   │   ├── scanner.js           # inventory helpers
│   │   └── uc-card.js           # standalone card renderer
│   ├── css/recommender.css
│   └── data/catalog-fallback.json
├── lookups/
│   ├── uc_recommender_static.csv     # stamped catalogueVersion + apiBase
│   └── uc_compliance_mappings.csv    # one row per (UC, clause)
├── metadata/default.meta
└── static/                      # icons placeholder
```

## What the bundled compliance content covers

Every tier-1 framework defined in `data/regulations.json` ships in the
same lookup and same `savedsearches.conf`:

| Framework        | Source key   |
|------------------|--------------|
| CMMC 2.0         | `cmmc`       |
| EU DORA          | `dora`       |
| GDPR             | `gdpr`       |
| HIPAA Security   | `hipaa-security` |
| ISO/IEC 27001    | `iso-27001`  |
| NIS2             | `nis2`       |
| NIST SP 800-53   | `nist-800-53` |
| NIST CSF         | `nist-csf`   |
| PCI DSS          | `pci-dss`    |
| SOC 2            | `soc-2`      |
| SOX ITGC         | `sox-itgc`   |

UCs that satisfy multiple frameworks appear once in
`savedsearches.conf` (deduped by UC id) with every regulation listed in
their `description`/`action.uc_compliance.param.regulations` field.
The same UC fans out to one row per (regulation, clause) tuple in the
lookup so per-clause reporting still works.

## Companion TA (`splunk-uc-recommender-ta`)

Enterprise-only add-on that adds a modular input
(`uc_recommender_deep_scan`) which samples one event per
`(index, sourcetype)` pair and writes extracted field names back into
the inventory. Install it on any search head where you want the
recommender to prefer UCs whose `requiredFields` are actually present
in your data. **Not Cloud-vetted** — leave it off Splunk Cloud stacks.

---

_This app is generated. Edits in place will be overwritten. File bug
reports and content requests at
<https://github.com/fenre/splunk-monitoring-use-cases/issues>._
