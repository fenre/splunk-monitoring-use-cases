# Splunk UC Recommender — operator & developer guide

> **TL;DR** — Install [`splunk-uc-recommender`](../splunk-apps/splunk-uc-recommender/)
> on any Splunk search head (Enterprise 9.2+ or Splunk Cloud). It
> inventories the local environment, matches against the 6 300+ use
> cases catalogued in this repository, and gives operators a one-click
> preview of ready-to-enable SPL. Every tier-1 compliance UC is also
> bundled as a **disabled** saved search so the same app covers
> GDPR, HIPAA, PCI-DSS, NIS2, ISO 27001, NIST CSF, NIST 800-53,
> DORA, CMMC, SOC 2, and SOX ITGC without a second install.

This document covers:

- [What the app ships](#what-the-app-ships)
- [End-to-end architecture](#architecture)
- [Install / uninstall](#install)
- [Operator-facing UI](#operator-ui)
- [Bundled compliance content](#bundled-compliance-content)
- [Scan saved searches and KV store layout](#inventory-scans)
- [Remote API contract (what the app fetches)](#remote-api-contract)
- [Security model (origin allow-list, sandboxing, CSP, XSS)](#security-model)
- [Developer guide — regenerating and extending the app](#developer-guide)
- [Troubleshooting](#troubleshooting)

---

## What the app ships

This repository releases **two** Splunk apps — both generated from the
same source of truth by
[`scripts/generate_recommender_app.py`](../scripts/generate_recommender_app.py):

| App | Audience | What it ships | Cloud-safe? |
| --- | -------- | ------------- | ------------ |
| [`splunk-uc-recommender`](../splunk-apps/splunk-uc-recommender/) | Platform owners, SecOps leads, compliance teams | Four inventory scans, a match-and-score UI against the 6 300+ UC catalogue, plus **every tier-1 compliance UC** (GDPR, HIPAA, PCI-DSS, NIS2, ISO 27001, NIST CSF, NIST 800-53, DORA, CMMC, SOC 2, SOX ITGC) shipped as **disabled** saved searches with a filterable Compliance view. | Yes — declarative content + AMD JS only. |
| [`splunk-uc-recommender-ta`](../splunk-apps/splunk-uc-recommender-ta/) | Enterprise search heads only | One modular input that samples a few events per `(index, sourcetype)` and enriches the recommender's KV store with the observed field names. | **No** — Enterprise-only because modular inputs must be individually vetted for Splunk Cloud. |

The older per-regulation packs (`splunk-uc-gdpr`, `splunk-uc-pci-dss`,
etc.) are no longer part of the release. Their content lives inside
`splunk-uc-recommender` as disabled saved searches and is exposed
through the **Compliance** view.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│ GitHub Pages (fenre.github.io/splunk-monitoring-use-cases)           │
│                                                                      │
│   /api/v1/recommender/sourcetype-index.json   (≈150 KB, 2 295 keys)  │
│   /api/v1/recommender/cim-index.json          (≈3 KB, 11 keys)       │
│   /api/v1/recommender/app-index.json          (≈340 KB, 1 200 keys)  │
│   /api/v1/recommender/uc-thin.json            (≈4.4 MB, 6 304 rows)  │
│   /api/v1/compliance/ucs/<id>.json            (full sidecars)        │
└───────────────────────────▲──────────────────────────────────────────┘
                            │ HTTPS GET (allow-list enforced)
┌───────────────────────────┴──────────────────────────────────────────┐
│ Splunk search head (splunk-uc-recommender)                           │
│                                                                      │
│   ┌────────────────────────┐      ┌───────────────────────────────┐  │
│   │ default/savedsearches  │─────▶│ KV: uc_recommender_inventory  │  │
│   │  · sourcetype scan     │      │  rows: type, name, count,     │  │
│   │  · index scan          │      │        firstSeen, lastSeen,   │  │
│   │  · CIM acceleration    │      │        extras                 │  │
│   │  · installed apps      │      └───────────────┬───────────────┘  │
│   └────────────────────────┘                      │                  │
│                                                   ▼                  │
│   ┌──────────────────────────────────────────────────────────────┐   │
│   │ appserver/static/js/recommender.js (AMD module)              │   │
│   │  1. inputlookup uc_recommender_inventory (via SearchManager) │   │
│   │  2. fetch the four remote indexes (credentials: 'omit')      │   │
│   │  3. score: exact sourcetype×3 + CIM accel×2 + fuzzy×1        │   │
│   │  4. render top 60 cards → Copy SPL / Open in Search          │   │
│   └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

The primary app runs on **any** Splunk search head. No outbound
compute happens on the server side; the four saved searches only touch
local Splunk APIs (metadata, eventcount, REST, KV store). All remote
fetches happen **in the browser** from the operator's session to
`https://fenre.github.io`, keeping the server in a Cloud-safe
"preview-only" posture.

## Install

Prefer the official release artefacts under **GitHub → Releases** —
each release ships two signed `.spl` archives with SHA-256 sidecars:

- `splunk-uc-recommender-<version>.spl`
- `splunk-uc-recommender-ta-<version>.spl`

Or build from source:

```bash
python3 scripts/generate_recommender_app.py
scripts/package_splunk_apps.sh dist/
```

The default packager produces only those two archives. Upload via
**Settings → Manage apps → Install app from file**. Restart Splunk Web
only if the installer asks for it (normally not required).

The first inventory refresh runs 30 minutes after install. Hit
**Recommender → Settings → Manual scan** to trigger one sooner.

### Splunk Cloud

Only `splunk-uc-recommender` is Cloud-safe. Upload it via ACS
self-service or a support ticket, depending on your tenant. **Do not**
upload `splunk-uc-recommender-ta` to Splunk Cloud; it carries a Python
modular input that must be individually vetted.

AppInspect readiness for `splunk-uc-recommender`:

- `app.manifest` v2, MIT `LICENSE`, README in the app root.
- No `commands.conf`, `restmap.conf`, `web.conf[expose:*]`, or
  `[script://]` inputs.
- `metadata/default.meta` keeps saved searches private.
- All 670+ bundled compliance searches ship with
  `disabled = 1` and `is_scheduled = 0`, so nothing runs on install.
- Output of `python3 scripts/audit_splunk_cloud_compat.py` reports
  zero pack-level findings on this app.

## Operator UI

The nav carries five Simple XML views plus a Dashboard Studio variant
of the recommendation page:

| View | File | Purpose |
| ---- | ---- | ------- |
| **Recommend** (default) | [`default/data/ui/views/recommend.xml`](../splunk-apps/splunk-uc-recommender/default/data/ui/views/recommend.xml) | KPI strip (sourcetypes detected / CIM accelerated / apps) + card grid of top 60 matches. |
| **Scan** | [`default/data/ui/views/scan.xml`](../splunk-apps/splunk-uc-recommender/default/data/ui/views/scan.xml) | Raw inventory tables straight from the KV store. |
| **Browse** | [`default/data/ui/views/browse.xml`](../splunk-apps/splunk-uc-recommender/default/data/ui/views/browse.xml) | Full catalogue (all 6 300+ UCs) with a live text filter. |
| **Compliance** | [`default/data/ui/views/compliance.xml`](../splunk-apps/splunk-uc-recommender/default/data/ui/views/compliance.xml) | Filter the bundled tier-1 compliance UCs by regulation, criticality, or clause. Drilldown opens the corresponding (disabled) saved search for review. |
| **Settings** | [`default/data/ui/views/settings.xml`](../splunk-apps/splunk-uc-recommender/default/data/ui/views/settings.xml) | Override the upstream API base URL (validated against the allow-list); reset; view recent scan runs. |
| **Recommend (Dashboard Studio)** | [`default/data/ui/views/recommend_studio.xml`](../splunk-apps/splunk-uc-recommender/default/data/ui/views/recommend_studio.xml) + [`recommend.json`](../splunk-apps/splunk-uc-recommender/default/data/ui/views/recommend.json) | Same KPIs and card grid but in the Dashboard Studio v2 layout for operators who have switched their tenant over. |

Each card on **Recommend** exposes two actions:

1. **Details** — slides in a drawer, fetches the full compliance
   sidecar from `/api/v1/compliance/ucs/<id>.json`, and renders the
   UC's SPL inside a `<pre>` block plus **Copy SPL** and **Open in
   Search app** buttons.
2. **Open in Search app** — deep-links into Splunk's built-in Search &
   Reporting app with the SPL pre-populated (`/app/search/search?q=…`)
   so the operator can adapt it in context before saving.

## Bundled compliance content

Every tier-1 compliance use case from the catalogue is shipped as a
saved search inside `splunk-uc-recommender` with the following
guarantees:

| Guardrail | Value |
| --- | --- |
| `disabled` | `1` — never runs on install. |
| `is_scheduled` / `enableSched` | `0` — no cron schedule until an operator explicitly enables it. |
| `action.uc_compliance.param.uc_id` | The canonical `NN.NN.N` UC id. |
| `action.uc_compliance.param.regulations` | Comma-separated list of frameworks that mapped this UC (e.g. `gdpr,iso-27001,nist-csf`). |
| `action.uc_compliance.param.clauses` | Comma-separated list of clause references (e.g. `Art.5/6`, `AC-2`, `8.16`). |
| `action.uc_compliance.param.versions` | Framework versions pinned by the catalogue (e.g. `gdpr@2016/679,iso-27001@2022`). |
| Stanza title | Human-readable UC title, so the search is easy to spot in **Settings → Searches**. |

A single UC that maps to multiple frameworks (say, a PII-detection
control that satisfies both GDPR Art.5/6 and ISO 27001 8.16) is
shipped as **one** saved search annotated with every framework that
references it. The per-clause detail still lives in the lookup below.

The app also ships a unified lookup, `uc_compliance_mappings`, that
has one row per `(UC, framework-entry)`:

| Field | Description |
| --- | --- |
| `uc_id` | `22.1.1`, `22.15.7`, … |
| `title` | UC title (identical across rows for the same `uc_id`). |
| `criticality` | `critical`, `high`, `medium`, `low` — may be empty for UCs whose catalogue entry does not declare a criticality. |
| `regulation` | Framework slug (`gdpr`, `pci-dss`, `nist-800-53`, `iso-27001`, …). |
| `regulation_version` | Framework version (`2016/679`, `rev-5`, `v2.0`, …). |
| `clause` | Clause / control reference (`Art.5/6`, `AC-2`, `8.16`, `CC6.1`, …). |
| `clause_url` | Upstream link to the clause reference when the catalogue provides one. |
| `assurance` | How strong the mapping is (`full`, `partial`, `contributing`). |
| `mode` | Role of the UC for that clause (`satisfies`, `detects-violation-of`). |
| `source_path` | Catalogue source file the mapping was extracted from. |

The **Compliance** view joins those rows in-memory and exposes three
dropdowns — regulation, criticality, title — so a SOC lead preparing a
GDPR audit can filter straight to the disabled searches that cover
that framework, click through to Settings → Searches, and enable the
ones that match their environment.

## Inventory scans

All four scans share one KV store collection
(`uc_recommender_inventory`) with a single row shape:

| Field | Type | Example |
| ----- | ---- | ------- |
| `_key` | string | `sourcetype::stash` / `cim::Authentication` / `app::Splunk_TA_nix` / `index::main` |
| `type` | string | `sourcetype`, `index`, `cim_model`, `app` |
| `name` | string | `stash`, `Authentication`, `Splunk TA nix`, `main` |
| `count` | number | event count / acceleration size / `1` for apps |
| `firstSeen` | string (`YYYY-MM-DDThh:mm:ssZ`) | `` (apps) or first metadata date |
| `lastSeen` | string (`YYYY-MM-DDThh:mm:ssZ`) | most recent scan run |
| `extras` | string | `accelerated` / `not_accelerated` / app version / `fields_extracted=…` (from the TA) |

To avoid races when four scans share one collection, each scan uses a
**read → filter → append → write-back** pattern:

```spl
| inputlookup uc_recommender_inventory
| where type!="sourcetype"
| append [
    | metadata type=sourcetypes index=*
    | eval type="sourcetype", name=sourcetype, count=totalCount, …
    | table _key type name count firstSeen lastSeen extras
  ]
| outputlookup uc_recommender_inventory append=false
```

That guarantees a sourcetype scan leaves the index/CIM/app rows
untouched and vice-versa. The authoritative definitions live in
[`default/savedsearches.conf`](../splunk-apps/splunk-uc-recommender/default/savedsearches.conf).

Cadence:

| Scan | Cron | Typical cost |
| ---- | ---- | ------------ |
| Sourcetypes | `*/30 * * * *` | seconds — `| metadata type=sourcetypes` is metadata-only |
| Indexes | `*/30 * * * *` | seconds — `| eventcount summarize=false` |
| CIM acceleration | `0 * * * *` | sub-second — REST probe of `/services/data/models` |
| Installed apps | `13 3 * * *` (once/day) | sub-second — REST probe of `/services/apps/local` |

The companion TA (`splunk-uc-recommender-ta`) adds one more
input — `uc_recommender_deep_scan` — that once per day samples
`| head 5` events per `(index, sourcetype)` pair, extracts the list
of field names, and stuffs them into the `extras` column as
`fields_extracted=<csv>`. The recommender can then prefer UCs whose
`requiredFields` are actually present in your data.

> **The TA is Enterprise-only.** Modular inputs must be explicitly
> vetted for Splunk Cloud, so we ship the TA separately and mark it
> `"Enterprise": ">=9.2"` with no Cloud `_cloud` deployment target.

## Remote API contract

The four recommender indexes live under
[`api/v1/recommender/`](../api/v1/recommender/) in the repo and are
served by GitHub Pages. They are generated from `catalog.json` by
[`scripts/generate_api_surface.py`](../scripts/generate_api_surface.py).

### `sourcetype-index.json`

```json
{
  "schemaVersion": "1.0.0",
  "catalogueVersion": "6.0",
  "generatedAt": "2026-04-17T00:00:00Z",
  "sourcetypes": {
    "wineventlog:security": ["22.15.7", "22.15.9", "22.18.3"],
    "cisco:asa":           ["22.01.3", "22.01.5"],
    …
  }
}
```

### `cim-index.json`

```json
{
  "schemaVersion": "1.0.0",
  "cimModels": {
    "Authentication": ["22.15.1", "22.15.5", …],
    "Endpoint":       […],
    "Network_Traffic":[…]
  }
}
```

### `app-index.json`

```json
{
  "schemaVersion": "1.0.0",
  "apps": {
    "Splunk Enterprise Security":   [{"id": "22.15.1", "required": true}, …],
    "Splunk_TA_nix":                […],
    "Cisco_TA":                     […]
  }
}
```

### `uc-thin.json`

```json
{
  "schemaVersion": "1.0.0",
  "useCases": [
    {"id": "22.15.1", "title": "…", "value": "…", "criticality": "high",
     "difficulty": "medium", "monitoringType": "detection",
     "splunkPillar": "security", "app": "Splunk Enterprise Security",
     "cimModels": ["Authentication"], "mitreAttack": ["T1078"]}
  ]
}
```

All four are regenerated deterministically. The repository's CI job
runs `python3 scripts/generate_api_surface.py --check` to reject drift.

## Security model

- **Origin allow-list.** `appserver/static/js/recommender.js` only
  accepts API base URLs whose `origin` is in `ALLOWED_ORIGINS`
  (currently just `https://fenre.github.io`). Any operator override
  set via the Settings page is validated against the same list before
  it is saved to `localStorage` and before it is fetched.
- **Credentials-free fetches.** All `fetch()` calls use
  `credentials: 'omit'` and `cache: 'no-cache'`; the remote host never
  sees Splunk session cookies.
- **No raw HTML from the catalogue.** The UI never passes remote
  strings through `innerHTML`. Every DOM node is built via
  `document.createElement`/`textContent`/`setAttribute`, and link
  `href` values are accepted only when they match `/^(https?:|mailto:)/i`
  (so a malicious catalogue cannot inject `javascript:` URLs).
- **No server-side fetches.** The Splunk server never talks to the
  catalogue. If your tenant blocks outbound `https://fenre.github.io`,
  the browser-side UI fails gracefully and the scan dashboards still
  work from the local KV store.
- **Preview-only writes.** No generator path creates saved searches on
  the target instance. The copy-SPL button uses
  `navigator.clipboard.writeText` which requires a user gesture.
- **Cloud vetting.** The app ships only declarative content (saved
  searches, macros, lookups, views) plus AMD JavaScript under
  `appserver/static/`. It has no `commands.conf`, `restmap.conf`,
  `[script://]` inputs, or `web.conf[expose:*]` stanzas. The audit
  report at [docs/splunk-cloud-compat.md](splunk-cloud-compat.md)
  shows zero findings for `splunk-uc-recommender`.

The companion TA does add a Python modular input. It uses the Splunk
session key provided on stdin, talks only to `https://localhost:8089`,
and writes back to the primary app's KV store. Source is at
[`splunk-apps/splunk-uc-recommender-ta/bin/deep_scan.py`](../splunk-apps/splunk-uc-recommender-ta/bin/deep_scan.py).

## Developer guide

### Regenerating the apps

Every file in `splunk-apps/splunk-uc-recommender/` and
`splunk-apps/splunk-uc-recommender-ta/` is **generated**. Source of
truth is [`scripts/generate_recommender_app.py`](../scripts/generate_recommender_app.py).

```bash
# Regenerate both apps.
python3 scripts/generate_recommender_app.py

# Only the primary app (skip the TA).
python3 scripts/generate_recommender_app.py --no-ta

# CI drift guard — exits 1 if any generated file is out of sync.
python3 scripts/generate_recommender_app.py --check
```

The script writes UTF-8 with LF line endings, pins its timestamps to
the latest git commit (or `SOURCE_DATE_EPOCH` if set), and uses sorted
JSON keys so regenerated trees are byte-identical.

### Regenerating the remote API

Same story for the four recommender JSON indexes:

```bash
python3 scripts/generate_api_surface.py          # write
python3 scripts/generate_api_surface.py --check  # CI drift guard
```

Outputs land under `api/v1/recommender/` and are committed to the
repository so GitHub Pages can serve them.

### Testing

[`tests/recommender/match.test.mjs`](../tests/recommender/match.test.mjs)
runs the match-and-score logic with a fixture KV-store inventory and a
trimmed index and asserts that:

- exact sourcetype matches outrank fuzzy matches;
- a UC whose only signal is a missing app still scores lower than
  one that also has a CIM match;
- the `safeLinkHref` sanitiser rejects `javascript:` and `data:`
  URLs.

```bash
node --test tests/recommender/*.test.mjs
```

The same invocation is wired into `.github/workflows/validate.yml`
alongside the generator's `--check` run.

## Troubleshooting

| Symptom | Likely cause | Fix |
| ------- | ------------ | --- |
| Recommend page spins forever | Browser cannot reach `https://fenre.github.io` | Confirm egress; the UI will surface the fetch error after the first timeout. |
| "Refusing to fetch …" error | Settings override points outside the allow-list | Clear the override in Settings or choose a URL under `https://fenre.github.io`. |
| Empty inventory tables | Scans not yet run | Wait 30 minutes after install, or trigger **Manual scan** from the Settings page. |
| "Recommender could not load: HTTP 404" | GitHub Pages hasn't published the latest API | Run `python3 scripts/generate_api_surface.py` locally and commit. |
| TA modular input fails on Cloud | Modular inputs are blocked on Splunk Cloud Classic | Install the TA only on Enterprise search heads. |

For anything else, file a bug under
<https://github.com/fenre/splunk-monitoring-use-cases/issues>.
