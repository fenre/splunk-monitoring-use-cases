# Splunk App Design — Infrastructure & Security Use Case Library

This document describes a **design only** (no code) for turning this repository into a **Splunk app** similar in concept to **Splunk Security Essentials (SSE) / ESCU**, but **broader in scope** (infrastructure, cloud, applications, and security). The design uses **Splunk UCC** (Universal Configuration Console / addonfactory-ucc-generator) as the structural and tooling starting point.

---

## 1. Vision and scope

### 1.1 What the app is

- **Name (concept):** e.g. *Infrastructure & Security Use Case Library* (or *Monitoring Use Case Library*).
- **Purpose:** A single Splunk app that:
  - Exposes the repo’s **~3,000 use cases** as a **browsable, filterable catalog** inside Splunk.
  - Lets users **view SPL, implementation notes, CIM/data model, and dependencies** per use case.
  - Optionally **ships or generates saved searches** (and later alerts/dashboards) so users can “enable” use cases with one action.
- **Audience:** IT ops, SREs, security analysts, and Splunk admins who need a single place to discover and implement monitoring use cases across infra, cloud, apps, and security.

### 1.2 How it differs from SSE/ESCU

| Aspect | SSE/ESCU | This app (design) |
|--------|----------|-------------------|
| Scope | Security detections and stories | Infra + cloud + app + security (all 20 categories) |
| Content source | security_content repo (contentctl, YAML) | This repo (markdown, build.py → data.js) |
| Primary object | Detections (alerts), analytic stories | Use cases (catalog + optional saved searches / alerts) |
| Build tool | contentctl | Custom build (extend current build.py or UCC + content generator) |

The app should feel like “Security Essentials for the whole stack”: same idea (curated, ready-to-use content), broader domain.

---

## 2. UCC as design starting point

### 2.1 Why UCC

- **Consistent layout:** UCC defines a clear app/add-on structure (`metadata/`, `default/`, `appserver/`, `bin/`, `lib/`), which fits a “content + optional UI” app.
- **Tooling and packaging:** `ucc-gen build` and `ucc-gen package` give a standard build and .spl/.tgz output.
- **UI and REST:** If the app needs a **configuration or catalog UI** (browse use cases, enable/disable, link to docs), UCC’s appserver and REST patterns are a good fit.
- **Docs and maintainability:** Following UCC conventions makes the app familiar to anyone who has built or deployed UCC-based add-ons.

### 2.2 What we take from UCC (design only)

- **Directory layout:** Adopt UCC’s separation of:
  - **metadata/** — App manifest, version, dependencies.
  - **default/** — Shipped config: `app.conf`, `savedsearches.conf`, lookups, `data/ui/` (views, nav).
  - **appserver/** — Static assets and, if needed, a React or static UI for the use case catalog.
  - **bin/** — Only if we add REST endpoints (e.g. to serve catalog JSON or “enable use case”).
- **Manifest and app.conf:** Use an UCC-style **app.manifest** (or equivalent) so that `app.conf` is generated with correct label, version, author, and dependency list.
- **No modular inputs for v1:** The first version is a **content and catalog app**, not a data-collection add-on. UCC’s input framework is reserved for a later phase (e.g. a separate TA that collects data, or an “enable use case” action that creates a saved search).

---

## 3. Content model: from repo to Splunk objects

### 3.1 Source of truth

- **Use cases:** `use-cases/cat-*.md` (and `INDEX.md` for category metadata).
- **Build output today:** `build.py` → `data.js` (DATA, CAT_META, CAT_STARTERS, CAT_GROUPS).

### 3.2 Mapping repo concepts to the app

| Repo concept | Splunk app artifact | Notes |
|--------------|---------------------|--------|
| Categories (1–20) | Lookup or static JSON | category_id, name, description, icon, quick_start_uc_ids; drives nav and filters. |
| Use case (UC-x.y.z) | One row in **use case catalog** + optional **saved search** | Catalog: id, name, category, subcategory, SPL, CIM, TA, implementation summary, difficulty, criticality, etc. |
| SPL (q) | `savedsearches.conf` stanza and/or catalog field | Only for use cases that have SPL; name e.g. `IMUC - UC-1.1.1 - Kernel Core Dump` (prefix to avoid clashes). |
| Implementation / “View more” (md) | Catalog field or linked doc | Stored in lookup (e.g. CSV with one row per UC and a “detailed_impl” column) or served via REST from generated JSON. |
| INDEX.md quick starters | Same as category metadata | Part of category lookup or a separate “starter” lookup. |

### 3.3 Use case catalog (lookup or REST)

- **Preferred (design):** A **lookup table** (e.g. `use_case_catalog.csv` in `default/lookups/`) with columns such as:
  - `uc_id`, `name`, `category_id`, `subcategory`, `spl`, `cim_models`, `app_ta`, `data_sources`, `implementation_summary`, `detailed_impl`, `difficulty`, `criticality`, `quick_win`, `references`, `mitre_ids`, ...
- **Alternative:** Catalog as **static JSON** under `appserver/static/` (e.g. `catalog.json`) and a simple REST handler or direct file read for the UI. Lookup is better for Splunk-native search/drilldown (e.g. `| inputlookup use_case_catalog`).
- **Saved searches:** For use cases that have SPL, the build process emits **savedsearches.conf** stanzas (search name, search string, description, optionally alert config). Users can run or enable them from the UI or from Search.

### 3.4 What gets packaged in the app

- **default/app.conf** — App identity, version, optional dependencies (e.g. Splunk_SA_CIM).
- **default/savedsearches.conf** — One stanza per use case that has SPL (disabled by default or enabled as “template” with no schedule).
- **default/lookups/use_case_catalog.csv** (and possibly **use_case_catalog.lookup** in default) — Full catalog for nav, filters, and “View details”.
- **default/data/ui/views/** — At least one dashboard/view that shows the catalog (and optionally embeds or links to the current `index.html` experience).
- **appserver/** — Static resources; optionally the current dashboard as a single-page app (index.html + data.js or catalog.json).
- **metadata/** — Default.meta for lookups and saved searches; app.manifest for UCC-style build.

---

## 4. App directory layout (UCC-inspired)

High-level layout below. No implementation detail, only where things live.

```
<app_name>/
├── default/
│   ├── app.conf
│   ├── savedsearches.conf      # Generated from repo (one stanza per UC with SPL)
│   ├── lookups/
│   │   ├── use_case_catalog.csv
│   │   └── use_case_catalog.lookup (or .conf)
│   ├── data/
│   │   └── ui/
│   │       ├── nav/
│   │       │   └── default.xml
│   │       └── views/
│   │           ├── use_case_library.xml    # Main catalog/dashboard
│   │           └── ...                     # Optional per-category or detail views
│   └── (no inputs.conf in v1 — content only)
├── appserver/
│   ├── static/
│   │   ├── openapi.json        # If UCC generates it; optional
│   │   ├── catalog.json        # Optional: catalog for SPA; else use lookup
│   │   └── (assets for dashboard if SPA)
│   └── (UCC React/source if we use UCC UI)
├── metadata/
│   ├── default.meta            # Permissions for lookups, saved searches, views
│   └── (app.manifest or equivalent for UCC)
├── bin/                        # Optional: REST handlers for catalog or “enable use case”
│   └── (Python handlers only if needed)
├── lib/                        # Only if we add Python (e.g. REST)
└── README/
    └── (app description, install, dependencies)
```

- **default/** holds all “content” that is shipped with the app (searches, lookups, views).
- **appserver/** holds what the UI needs (static files or UCC-built UI).
- **Build pipeline** (see below) produces `savedsearches.conf` and `use_case_catalog.csv` (and optional `catalog.json`) from the repo’s markdown and current `build.py` output.

---

## 5. Build pipeline: repo → app package

### 5.1 Design principle

- **Single source of truth:** `use-cases/*.md` and `INDEX.md`.
- **Two outputs:**  
  - **Current:** `data.js` for the existing static site.  
  - **New:** App content (lookup CSV, savedsearches.conf, optional catalog.json) and then the Splunk app package.

### 5.2 Build stages (conceptual)

1. **Parse (existing):** `build.py` (or equivalent) parses markdown and INDEX.md. Today it emits `data.js`; it (or a sibling script) should also emit:
   - **use_case_catalog.csv** — One row per use case (uc_id, name, category_id, subcategory, spl, cim_models, app_ta, data_sources, implementation_summary, detailed_impl, difficulty, criticality, …).
   - **savedsearches.conf** — One stanza per use case that has a non-empty SPL field; search name includes UC-ID for traceability.
2. **App assembly:** Copy or generate into the app directory:
   - `default/lookups/use_case_catalog.csv` (and lookup def).
   - `default/savedsearches.conf`.
   - `default/app.conf` (from manifest).
   - `default/data/ui/` views and nav.
   - `appserver/static/` if we use static catalog or current dashboard.
3. **UCC package (if using UCC):** Run `ucc-gen build` then `ucc-gen package` so the final artifact is a valid .spl (or .tgz) that Splunk accepts.

If we do **not** use UCC’s generator for this app (e.g. we only adopt its layout), then “package” is a script that zips `default/`, `metadata/`, `appserver/`, etc., into an app archive.

### 5.3 Saved search naming and safety

- **Naming:** e.g. `IMUC - UC-1.1.1 - Kernel Core Dump Generation` so that:
  - All app searches are easy to find (prefix `IMUC` or similar).
  - UC-ID is visible for support and docs.
- **Default state:** Searches are **disabled** or **not scheduled** by default so they do not run until the user explicitly enables or schedules them (reduces risk of accidental load).

---

## 6. UI/UX inside Splunk

### 6.1 Entry point

- **App menu:** One app (e.g. “Infrastructure & Security Use Case Library” or “Monitoring Use Case Library”).
- **Default view:** A **Use Case Library** dashboard that:
  - Lists/filters use cases by category, subcategory, difficulty, criticality, monitoring type (same dimensions as the current site).
  - Lets the user open a **detail view** for one use case: name, SPL, CIM/data model, implementation summary, “View more detailed instructions”, required TAs, references.

### 6.2 Two UI implementation options (design only)

- **Option A — Simple XML + lookup:**  
  - One or more Simple XML dashboards that use `| inputlookup use_case_catalog` and tokens for filtering.  
  - Detail panel or separate view shows the selected row’s SPL and implementation (from lookup fields).  
  - No custom backend; works with pure Splunk.

- **Option B — Embedded SPA (current site):**  
  - Serve the existing `index.html` (and `data.js` or `catalog.json`) from `appserver/static/` and embed it in an iframe or as the app’s main view.  
  - Easiest way to reuse current UX; catalog data can be loaded from `catalog.json` or from a REST endpoint that reads the lookup.

Choose one for v1 (e.g. Option A for minimal dependency, Option B for feature parity with current site).

### 6.3 “Enable use case” (later phase)

- **Concept:** A button or action “Add to my environment” that creates a **copy** of the saved search in the user’s context (or in a dedicated app like “My Monitoring Content”) with a schedule and alert action.  
- **Implementation (design):** Either a REST handler (e.g. `bin/` Python) that calls the Splunk API to create a saved search, or a link that opens Search with the SPL pre-filled so the user saves it manually.  
- Not required for the first version; the first version can be “catalog + view SPL + run search from app.”

---

## 7. Dependencies and packaging

### 7.1 App dependencies

- **Optional (recommended):** Declare dependency on **Splunk_SA_CIM** so that CIM-relevant use cases are clearly associated with the CIM app. Do not hard-require it so that users can still browse the catalog without CIM.
- **No mandatory TAs:** The app does not require specific technology add-ons; the catalog only states “recommended app/TA” per use case. Users install TAs as needed.

### 7.2 Packaging format

- **.spl** (or .tgz) suitable for:
  - Upload via Splunk Web (Apps → Install app from file).
  - Deployment via deployment server or automation.
- **Versioning:** Version in app.conf (and manifest) aligned with repo tags (e.g. 1.0.0 for first release).

---

## 8. Phasing and next steps

| Phase | Scope | Outcome |
|-------|--------|--------|
| **Design (current)** | Agree on layout, content model, build stages, UI option. | This document. |
| **Build extension** | Extend build (or add script) to emit `use_case_catalog.csv` and `savedsearches.conf` from existing markdown. | Artifacts ready to drop into app layout. |
| **App shell** | Create app directory structure (UCC-style or manual), app.conf, metadata, default nav and one view. | Installable app that shows a minimal “Use Case Library” view. |
| **Catalog view** | Implement main dashboard (Simple XML or embedded SPA) that reads catalog and shows detail. | Users can browse and view SPL/implementation in Splunk. |
| **Packaging** | Add UCC-based or custom packaging step to produce .spl. | One command (or CI job) produces the app package. |
| **Optional: REST and “Enable”** | Add REST endpoint for catalog and “enable use case” action. | Users can create saved searches from the app. |

---

## 9. Summary

- **Goal:** A Splunk app that delivers the same value as the current repo (use case catalog, SPL, implementation guidance) **inside** Splunk, in an SSE-like way but for infra + cloud + app + security.
- **Structure:** UCC-style layout (default/, appserver/, metadata/) and, if desired, UCC tooling for build/package.
- **Content:** One catalog (lookup or JSON) and optional savedsearches.conf generated from `use-cases/*.md` and INDEX.md.
- **UX:** One main “Use Case Library” view (Simple XML or embedded current dashboard) with filters and detail; optional “enable use case” later.
- **No code in this doc:** Only design; implementation (build scripts, views, optional REST) follows in a later step.
