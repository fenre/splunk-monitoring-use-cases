# Splunk UC Recommender — operator & developer guide

> **TL;DR** — Install [`splunk-uc-recommender`](../splunk-apps/splunk-uc-recommender/)
> on any Splunk search head (Enterprise 9.2+ or Splunk Cloud). It
> inventories the local environment, matches against the 6 300+ use
> cases catalogued in this repository, and gives operators a one-click
> preview of ready-to-enable SPL. Every tier-1 compliance UC is also
> bundled as a **disabled** saved search so the same app covers
> GDPR<sup class="ref">[<a href="#ref-4">4</a>]</sup>, HIPAA<sup class="ref">[<a href="#ref-12">12</a>]</sup>, PCI-DSS, NIS2<sup class="ref">[<a href="#ref-3">3</a>]</sup>, ISO 27001, NIST CSF, NIST 800-53,
> DORA<sup class="ref">[<a href="#ref-5">5</a>]</sup>, CMMC, SOC 2<sup class="ref">[<a href="#ref-2">2</a>]</sup>, and SOX<sup class="ref">[<a href="#ref-10">10</a>]</sup> ITGC without a second install.

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

As of v9.0 this repository releases **one** Splunk app, generated from
the source of truth by
[`python3 -m splunk_uc generate-recommender-app`](../scripts/generate_recommender_app.py):

| App | Audience | What it ships | Cloud-safe? |
| --- | -------- | ------------- | ------------ |
| [`splunk-uc-recommender`](../splunk-apps/splunk-uc-recommender/) | Platform owners, SecOps leads, compliance teams | Four inventory scans, a match-and-score UI against the 7 300+ UC catalogue, **every tier-1 compliance UC** (GDPR, HIPAA, PCI-DSS, NIS2, ISO 27001, NIST CSF, NIST 800-53, DORA, CMMC, SOC 2, SOX ITGC) shipped as **disabled** saved searches with a filterable Compliance view, **per-UC implementation tracking** (auto-detect via SPL fingerprinting + manual override), and **per-UC Splunkbase<sup class="ref">[<a href="#ref-9">9</a>]</sup> install guidance**. | Yes — declarative content + AMD JS only. |

### What v9.0 retired

Two earlier shapes were folded back into the single app:

- **The 12 per-regulation packs** (`splunk-uc-gdpr`, `splunk-uc-pci-dss`, …)
  — their content lives inside `splunk-uc-recommender` as disabled
  saved searches and is exposed through the **Compliance** view.
- **`splunk-uc-recommender-ta`** — the Enterprise-only modular input
  that enriched the recommender's KV store with observed field names
  was retired to keep the release to a single Cloud-safe artefact.
  UCs that declare `requiredFields` are now flagged "field coverage
  unknown"; a Cloud-safe replacement is on the roadmap.

Customers running any of those legacy apps should follow
[`docs/migration-v8.md`](migration-v8.md) before uninstalling. The
`scripts/backup_legacy_app_state.sh` helper preserves operator-modified
SPL, KV state, and enabled saved-search names before removal.

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
each release ships one signed `.spl` archive with a SHA-256 sidecar:

- `splunk-uc-recommender-<version>.spl`

Or build from source:

```bash
python3 -m splunk_uc generate-recommender-app
scripts/package_splunk_apps.sh dist/
```

Upload via **Settings → Manage apps → Install app from file**. Restart
Splunk Web only if the installer asks for it (normally not required).

The first inventory refresh runs 30 minutes after install. Hit
**Recommender → Settings → Manual scan** to trigger one sooner.

### Splunk Cloud

`splunk-uc-recommender` is Cloud-safe. Upload it via ACS self-service
or a support ticket, depending on your tenant.

AppInspect readiness for `splunk-uc-recommender`:

- `app.manifest` v2, MIT `LICENSE`, README in the app root.
- No `commands.conf`, `restmap.conf`, `web.conf[expose:*]`, or
  `[script://]` inputs.
- `metadata/default.meta` keeps saved searches private.
- All 670+ bundled compliance searches ship with
  `disabled = 1` and `is_scheduled = 0`, so nothing runs on install.
- Output of `python3 -m splunk_uc audit-splunk-cloud-compat` reports
  zero pack-level findings on this app.

## Operator UI

The nav carries six Simple XML views (no Dashboard Studio variant —
that was retired in build 4 because Splunk Studio strips embedded
`<script>` tags from `splunk.viz.html`, so the recommender card grid
cannot run inside a Studio dashboard):

| View | File | Purpose |
| ---- | ---- | ------- |
| **Recommend** (default) | [`default/data/ui/views/recommend.xml`](../splunk-apps/splunk-uc-recommender/default/data/ui/views/recommend.xml) | KPI strip (sourcetypes detected / CIM accelerated / apps) + card grid of top 60 matches. |
| **Scan** | [`default/data/ui/views/scan.xml`](../splunk-apps/splunk-uc-recommender/default/data/ui/views/scan.xml) | Raw inventory tables straight from the KV store. |
| **Browse** | [`default/data/ui/views/browse.xml`](../splunk-apps/splunk-uc-recommender/default/data/ui/views/browse.xml) | Full catalogue (all 6 300+ UCs) with a live text filter. |
| **Compliance** | [`default/data/ui/views/compliance.xml`](../splunk-apps/splunk-uc-recommender/default/data/ui/views/compliance.xml) | Filter the bundled tier-1 compliance UCs by regulation, criticality, or clause. Drilldown opens the corresponding (disabled) saved search for review. |
| **Settings** | [`default/data/ui/views/settings.xml`](../splunk-apps/splunk-uc-recommender/default/data/ui/views/settings.xml) | Override the upstream API base URL (validated against the allow-list); reset; view recent scan runs. |

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

> **Field-coverage matching note.** v9.0 retired the
> `splunk-uc-recommender-ta` companion TA that previously enriched
> the `extras` column with `fields_extracted=<csv>` via a Python
> modular input. UCs that declare `requiredFields` are now flagged
> "field coverage unknown". A Cloud-safe replacement (likely
> `| metadata` + `| typelearner`) is on the roadmap.

## Remote API contract

The four recommender indexes live under
[`api/v1/recommender/`](../api/v1/recommender/) in the repo and are
served by GitHub Pages. They are generated from `catalog.json` by
[`python3 -m splunk_uc generate-api-surface`](../scripts/generate_api_surface.py).

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
runs `python3 -m splunk_uc generate-api-surface --check` to reject drift.

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

## Developer guide

### Regenerating the app

Every file in `splunk-apps/splunk-uc-recommender/` is **generated**.
Source of truth is
[`python3 -m splunk_uc generate-recommender-app`](../scripts/generate_recommender_app.py).

```bash
# Regenerate the recommender app.
python3 -m splunk_uc generate-recommender-app

# CI drift guard — exits 1 if any generated file is out of sync.
python3 -m splunk_uc generate-recommender-app --check
```

The script writes UTF-8 with LF line endings, pins its timestamps to
the latest git commit (or `SOURCE_DATE_EPOCH` if set), and uses sorted
JSON keys so regenerated trees are byte-identical.

### Regenerating the remote API

Same story for the four recommender JSON indexes:

```bash
python3 -m splunk_uc generate-api-surface          # write
python3 -m splunk_uc generate-api-surface --check  # CI drift guard
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
| "Recommender could not load: HTTP 404" | GitHub Pages hasn't published the latest API | Run `python3 -m splunk_uc generate-api-surface` locally and commit. |
| TA modular input fails on Cloud | Modular inputs are blocked on Splunk Cloud Classic | Install the TA only on Enterprise search heads. |

For anything else, file a bug under
<https://github.com/fenre/splunk-monitoring-use-cases/issues>.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Primary sources

<a id="ref-1"></a>**[1]** Splunk Inc. (2026). *Splunk Enterprise Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk

### Supporting sources

<a id="ref-2"></a>**[2]** American Institute of Certified Public Accountants. (2017). *Trust Services Criteria (2017) for Security, Availability, Processing Integrity, Confidentiality, and Privacy*. AICPA & CIMA. SOC 2 / TSP Section 100. https://www.aicpa-cima.com/topic/audit-assurance/soc-suite-of-services

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-4"></a>**[4]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-5"></a>**[5]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

<a id="ref-6"></a>**[6]** Public Company Accounting Oversight Board. (2007). *Auditing Standard 2201 — An Audit of Internal Control Over Financial Reporting*. PCAOB. PCAOB AS 2201. https://pcaobus.org/oversight/standards/auditing-standards/details/AS2201

<a id="ref-7"></a>**[7]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-8"></a>**[8]** Splunk Inc. (2026). *Splunk Common Information Model Add-on Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/CIM

<a id="ref-9"></a>**[9]** Splunk Inc. (2026). *Splunkbase — the Splunk app marketplace*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://splunkbase.splunk.com/

<a id="ref-10"></a>**[10]** U.S. Congress. (2002). *Sarbanes-Oxley Act of 2002 — Public Company Accounting Reform and Investor Protection Act*. U.S. Government. Pub. L. 107–204. https://www.sec.gov/about/laws/soa2002.pdf

<a id="ref-11"></a>**[11]** U.S. Department of Health & Human Services. (2002). *HIPAA Privacy Rule (45 CFR Parts 160 and 164, Subparts A and E)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/privacy/index.html

<a id="ref-12"></a>**[12]** U.S. Department of Health & Human Services. (2013). *HIPAA Security Rule (45 CFR Parts 160 and 164, Subparts A and C)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/security/index.html

### Related repository documents

- [`docs/splunk-cloud-compat.md`](splunk-cloud-compat.md)

### Cited by

- [`README.md`](../README.md)
- [`docs/api-docs-guide.md`](api-docs-guide.md)
- [`docs/build-artefacts-reference.md`](build-artefacts-reference.md)
- [`docs/catalog-schema.md`](catalog-schema.md)
- [`docs/cim-models-inventory.md`](cim-models-inventory.md)
- [`docs/compliance-story-guide.md`](compliance-story-guide.md)
- [`docs/inventory-and-sizing.md`](inventory-and-sizing.md)
- [`docs/splunk-apps-use-cases-comparison.md`](splunk-apps-use-cases-comparison.md)

<!-- END-AUTOGENERATED-SOURCES -->
