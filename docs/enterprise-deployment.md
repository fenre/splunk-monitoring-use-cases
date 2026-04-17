# Enterprise Deployment Guide

> Audience — Splunk platform engineers, SREs and security architects deploying this
> catalog inside a managed Splunk environment (Enterprise, Cloud, ITSI, or
> Enterprise Security).

This guide explains how to consume the project's four deliverables in
production:

1. **The web dashboard** (`index.html` / GitHub Pages) — browsable catalog
   for analysts.
2. **`TA-splunk-use-cases`** — Splunk Technology Add-on with Quick-Start
   scheduled searches.
3. **`DA-ITSI-monitoring-use-cases`** — ITSI content pack with KPI base
   searches, thresholds and service templates.
4. **`DA-ESS-monitoring-use-cases`** — Enterprise Security content pack
   with correlation searches, MITRE ATT&CK governance and analytic
   stories.

All four artefacts are built from the **same `catalog.json`** and share
their UC identifiers, so you can trace any alert back to its upstream
use-case page with one click.

---

## 1. Prerequisites

| Component | Minimum | Tested | Notes |
|-----------|---------|--------|-------|
| Splunk Enterprise / Cloud | 9.0.0 | 10.2.x | Splunk Cloud customers must use the Splunkbase "vetted" release of the TA (see §6 for validation). |
| Splunk Common Information Model | 5.3.0 | 6.0.x | Required for every content pack. |
| Splunk IT Service Intelligence | 4.15 | 4.19 | Only required for the ITSI content pack. |
| Splunk Enterprise Security | 7.3 | 8.1 | Only required for the ES content pack. |
| Splunk_SA_CIM dependency | 5.3.0+ | — | Shipped separately via Splunkbase. |

> **Supported deployment topologies:** Single-instance, distributed (dedicated
> search head), search-head cluster (SHC). All artefacts are SHC-safe — they
> contain no `local/` overrides or persistent state.

### Required indexes

The TA ships with a single `uc_index_*` macro per category that resolves
to `index=*` by default. Replace those macros with your site's real
index names before enabling any scheduled search (see §3.4).

---

## 2. Obtain the release

Download the three `.spl` packages from the
[latest GitHub release](https://github.com/fenre/splunk-monitoring-use-cases/releases/latest):

```
TA-splunk-use-cases-<ver>.spl
DA-ITSI-monitoring-use-cases-<ver>.spl
DA-ESS-monitoring-use-cases-<ver>.spl
SHA256SUMS.txt
```

Verify integrity before uploading to Splunk:

```bash
shasum -a 256 -c SHA256SUMS.txt
```

If you build from source instead, run:

```bash
git clone https://github.com/fenre/splunk-monitoring-use-cases
cd splunk-monitoring-use-cases
python3 build.py
scripts/package_ta.sh dist/
scripts/package_itsi.sh dist/
scripts/package_es.sh dist/
```

---

## 3. Install the Technology Add-on (TA)

### 3.1 Installation

**Splunk Enterprise (non-SHC):**

1. Log in to Splunk Web as an admin.
2. Navigate to *Apps → Manage Apps → Install app from file*.
3. Upload `TA-splunk-use-cases-<ver>.spl`.
4. Restart Splunk when prompted.

**Search-head cluster (SHC):**

1. Copy the `.spl` onto the deployer:
   ```bash
   scp TA-splunk-use-cases-<ver>.spl deployer:/tmp/
   ```
2. Extract to the deployer's shcluster apps directory:
   ```bash
   tar -xzf /tmp/TA-splunk-use-cases-<ver>.spl \
     -C $SPLUNK_HOME/etc/shcluster/apps/
   ```
3. Push the bundle:
   ```bash
   splunk apply shcluster-bundle -target https://<captain>:8089 \
     -auth admin:<pw>
   ```

**Splunk Cloud:**

Upload the `.spl` via the Splunk Cloud Admin Config Service (ACS) or
the Splunk Cloud self-service app installer. The TA passes AppInspect
cloud vetting; no custom deployment work is required.

### 3.2 Verify installation

1. Open *Settings → Searches, reports, and alerts*.
2. Filter by app `TA-splunk-use-cases`; you should see ≈115 saved
   searches prefixed with `UC-`.
3. All searches are **disabled by default** — this is deliberate. See
   §3.4 before enabling anything.

### 3.3 App permissions

By default the saved searches are exported `system`-wide (read-only
for `user`). Restrict the app's role permissions via
*Settings → Access controls → Roles* if you want to limit who can run
the Quick-Start searches.

### 3.4 Tuning: index macros and scheduling

The TA ships one macro per category (`uc_index_os`, `uc_index_net`,
`uc_index_sec`, …). Each macro resolves to `index=*` by default so
searches work on a fresh install, but you **must** override them with
your site-specific indexes to avoid scanning the entire datastore:

1. Go to *Settings → Advanced search → Search macros*.
2. Filter app `TA-splunk-use-cases`.
3. For each macro, replace the `index=*` definition with your indexes,
   e.g. `index=linux OR index=windows`.

After tuning macros, enable searches in small batches (10–20 at a time)
and observe search-scheduler load before enabling more.

The cron schedule is set by criticality:

| Criticality | cron | earliest / latest |
|-------------|------|-------------------|
| critical | `*/15 * * * *` | `-30m@m` / `now` |
| high | `0 * * * *` | `-1h@h` / `now` |
| medium | `0 */2 * * *` | `-2h@h` / `now` |
| low | `0 */6 * * *` | `-6h@h` / `now` |

Override these via `local/savedsearches.conf` overlays if your environment
requires different cadences.

---

## 4. Install the ITSI content pack

### 4.1 Pre-flight checklist

- ITSI 4.15+ is running.
- The user performing the install has the `itoa_admin` role.
- `Splunk_SA_CIM` is installed and up-to-date on the ITSI search head(s).

### 4.2 Installation

1. On the ITSI search head (or SHC deployer):
   ```bash
   scp DA-ITSI-monitoring-use-cases-<ver>.spl <host>:/tmp/
   ```
2. Upload via *Apps → Manage Apps → Install app from file*.
3. Restart ITSI search head / dispatch the bundle to the SHC.

### 4.3 Import content

The content pack ships its KPI base searches, thresholds, templates and
services as `default/*.conf` files. ITSI auto-discovers them after
startup, but you must **explicitly import** them via:

*ITSI → Settings → Service Templates → Import from file* **or**
*ITSI → Configuration → Data Integrations → ITSI content packs*.

After import:

1. Review the four KPI templates (`Linux Host`, `Windows Host`,
   `Network Interface`, `Web Application Availability`).
2. Link them to the matching service templates.
3. Attach existing entities or import new ones via
   `Splunk_TA_nix`, `Splunk_TA_windows`, etc.

### 4.4 Threshold tuning

All thresholds ship with **conservative static values**. After 7–14
days of baseline data, switch critical KPIs to adaptive (standard
deviation) thresholds via the KPI editor. See
[`ta/DA-ITSI-monitoring-use-cases/README.md`](../ta/DA-ITSI-monitoring-use-cases/README.md)
for specific guidance.

---

## 5. Install the ES content pack

### 5.1 Pre-flight checklist

- Splunk Enterprise Security 7.3+ is running.
- MITRE ATT&CK framework is already ingested in ES governance.
- `Splunk_SA_CIM` is installed with the Authentication, Network_Traffic,
  Endpoint, Change and Alerts data models accelerated.

### 5.2 Installation

Same procedure as §3 (`DA-ESS-monitoring-use-cases-<ver>.spl`).

### 5.3 Verify correlation searches

After install you should see **650 correlation searches** in
*ES → Content Management → Type = Correlation Search*.

All are **disabled by default** to avoid an alerting stampede. Review
the analytic stories first (*ES → Content Management → Type = Analytic
Story*) which group searches by MITRE ATT&CK tactic and use case
family.

### 5.4 Governance and risk-based alerting

The content pack writes MITRE ATT&CK technique mappings into
`governance.conf` so each notable event is automatically decorated
with `annotations.mitre_attack.*` fields. To use risk-based alerting:

1. Enable the `Risk Scoring` modular input under *ES → Risk Factors*.
2. The correlation searches include `action.risk.*` parameters that
   increment risk scores for the matching asset/identity.
3. Review the seeded `risk_factor_editor.conf` entries under
   `ta/DA-ESS-monitoring-use-cases/default/`.

### 5.5 Enabling searches safely

1. Start with the **10 highest-value critical use cases** from your
   threat-model priority list.
2. Let them run for 24 hours, monitor `search_queue.log` for skipped
   executions.
3. Enable in batches of 20, not all 650 at once.

If you need the **full** set of 1,874 security UCs (critical through
low), regenerate with:

```bash
python3 scripts/build_es.py --include-all
scripts/package_es.sh dist/
```

---

## 6. Splunk Cloud validation

All three packages are authored to pass:

| Check | Tool | Status |
|-------|------|--------|
| Splunk AppInspect (cloud vetting) | `splunk-appinspect inspect <pack>.spl --mode precert` | Expected to pass. |
| CIM compliance | SA-cim_vladiator | Expected to pass. |
| Dynamic code analysis | Splunk Cloud ACS pipeline | No custom Python / JS scripts — static conf only. |

Re-run AppInspect locally before submitting to Splunk Cloud vetting:

```bash
pip install splunk-appinspect
splunk-appinspect inspect dist/TA-splunk-use-cases-<ver>.spl \
  --mode precert --included-tags cloud
```

---

## 7. Dashboard hosting

The `index.html` dashboard is a **pure static site** — no build step,
no backend. Three hosting options in increasing order of control:

1. **GitHub Pages (public)** — no setup; use
   <https://fenre.github.io/splunk-monitoring-use-cases/>.
2. **Enterprise internal static host** — copy the repo's root to any
   web server (nginx, Apache, S3 + CloudFront, Azure Static Web Apps).
   Set the base URL via `SITE_BASE_URL` environment variable before
   running `build.py`.
3. **Splunk Dashboard Studio overlay** — embed the catalog in Splunk via
   an iframe panel:
   ```xml
   <panel>
     <html>
       <iframe src="/static/app/monitoring_use_cases/index.html"
               width="100%" height="900" frameborder="0"></iframe>
     </html>
   </panel>
   ```

The dashboard consumes the JSON API described in
[`openapi.yaml`](../openapi.yaml); you can hit the same endpoints from
any custom integration — see [`api-docs.html`](../api-docs.html) for
an interactive reference.

---

## 8. Upgrade path

1. Download the new release from GitHub.
2. Run `shasum -a 256 -c SHA256SUMS.txt`.
3. Upload the new `.spl` — Splunk replaces the default bundle in place.
4. Re-apply any `local/` overrides (macros, tuned thresholds) — these
   are preserved across upgrades.
5. Review the CHANGELOG for new UCs and breaking changes.
6. Re-enable newly added searches after the standard batch-enable
   procedure (§3.4, §5.5).

### Rollback

Because all packages are conf-only, rollback is symmetric:

```bash
# On the search head (non-SHC example)
mv $SPLUNK_HOME/etc/apps/TA-splunk-use-cases{,.new}
tar -xzf TA-splunk-use-cases-<previous>.spl \
  -C $SPLUNK_HOME/etc/apps/
splunk restart
```

---

## 9. Support, lifecycle and SLA

- **Upstream source of truth** —
  <https://github.com/fenre/splunk-monitoring-use-cases>. File issues
  there; do not open Splunk support cases for catalog content.
- **Release cadence** — new minor versions every 2–3 months; patch
  releases as needed. See [ROADMAP.md](../ROADMAP.md).
- **Supported versions** — the two most recent minor versions. Older
  releases continue to work but no longer receive link-rot fixes or
  Splunk Cloud revalidation.
- **Security disclosures** — follow [SECURITY.md](../SECURITY.md).

---

## 10. Checklist for go-live

Before enabling any production alerting:

- [ ] All three `.spl` files verified via SHA-256.
- [ ] TA installed on search head(s); SHC bundle applied.
- [ ] Index macros in the TA replaced with site-specific indexes.
- [ ] ITSI content pack imported via Service Templates UI.
- [ ] ITSI entities attached to the four service templates.
- [ ] ES correlation searches reviewed — analytic stories approved
      by SOC lead.
- [ ] Initial 10 critical searches enabled and observed for 24 hours.
- [ ] Dashboard hosting option chosen and linked from the intranet.
- [ ] Runbooks created for each enabled notable event (link to the
      corresponding UC page via `UC-<ID>`).
- [ ] Upgrade & rollback procedure documented for ops-on-call.

Once complete, progressively enable the remaining content in batches
as outlined in §3.4 and §5.5. Welcome to a gold-standard Splunk
monitoring deployment — and please open a PR if you add new use cases,
improvements or integration patterns that other adopters could benefit
from.
