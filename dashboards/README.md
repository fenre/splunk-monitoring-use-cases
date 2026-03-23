# Splunk Dashboard Studio exports

JSON definitions for **Splunk Dashboard Studio** (Enterprise / Cloud). Data is generated with **`makeresults`** and **`eval`** — **synthetic demo only**, suitable for layout reviews and stakeholder walkthroughs.

## Catalog Quick-Start Portfolio (`catalog-quick-start-top2.json`)

- **Scope:** The **first two** use cases listed under **Quick Start** in `use-cases/INDEX.md` for each of the **22** categories → **44** use cases.
- **Layout:** **44 separate chart objects** — exactly **one** Dashboard Studio visualization per use case (not a table, not one chart containing all series). Each panel’s **title** is `UC-… — use case name` and **description** is the category line; there are **no** per–use-case markdown blocks stacked above charts.
- **Page chrome only:** three small markdown blocks (dashboard title, subtitle, DEMO) plus the time-range input — everything else is a `splunk.*` chart.
- **Chart mix (rotates by panel):** `splunk.singlevalue` (with **sparkline** trend), `splunk.line`, `splunk.area`, `splunk.column` — all fed by **`makeresults`** / `eval` demo SPL tailored to the chart type.
- **Regenerate:** `python3 scripts/generate_catalog_dashboard.py` (edits UC lists in that script when INDEX Quick Start changes).

### Import into Splunk

1. In Splunk Web, open **Dashboards** (or **Search & Reporting** → **Dashboards**).
2. **Create** → **Dashboard** → choose **Dashboard Studio** (not Classic).
3. Open the Studio editor, then use **… (menu)** → **Import** / **Edit source** (wording varies by version) and paste or upload this JSON, **or** create an empty dashboard and replace the **Source** JSON.
4. Save into your app (e.g. **Search & Reporting** or a custom app). No indexes or forwarders are required; searches run as demo data.

If your Splunk build does not expose **Import**, create a new Studio dashboard, switch to **Source** (or **Code**) view, and replace the document with the contents of `catalog-quick-start-top2.json`.

### Deploy with the REST API (Splunk Enterprise / Splunk Cloud)

Splunk stores Dashboard Studio definitions through the **`data/ui/views`** endpoint. The JSON export must be wrapped in XML (`<dashboard version="2">` … `<definition><![CDATA[ … ]]></definition>`). The helper script **`scripts/deploy_dashboard_studio_rest.py`** builds that envelope and **POST**s it for you.

**Reference:** [Create a dashboard using REST API endpoints](https://docs.splunk.com/Documentation/Splunk/latest/DashStudio/RESTusage) (Splunk Docs).

**Prerequisites**

- Management port reachable (default **8089** for Enterprise; Splunk Cloud uses your deployment’s **Management API** host/port from Admin).
- Credentials with permission to create/edit dashboards in the target app (e.g. `admin` or a role with **`edit_dashboard`** / appropriate capabilities).
- Python **3** (stdlib only; no `pip` install required).

**Authentication (choose one)**

| Method | Environment variables |
|--------|-------------------------|
| **Bearer token** (recommended) | `SPLUNK_TOKEN` or `SPLUNK_REST_TOKEN` (e.g. from `secrets.env` after `set -a && . ./secrets.env`) |
| **Basic** | `SPLUNK_USER` and `SPLUNK_PASSWORD` (if only password is set, user defaults to `admin`) |

**Owner namespace:** `SPLUNK_OWNER` must match the Splunk user the token was issued for (REST path `servicesNS/<owner>/<app>/…`). If you use a personal token from **Settings → Tokens**, set `SPLUNK_OWNER` to that username (not necessarily `admin`).

**Common options**

| Variable | Default | Meaning |
|----------|---------|---------|
| `SPLUNK_HOST` | `localhost` | Splunk hostname or IP |
| `SPLUNK_PORT` | `8089` | Management port |
| `SPLUNK_SCHEME` | `https` | Use `http` only if you know your instance is HTTP |
| `SPLUNK_APP` | `search` | App context (e.g. `search` for Search & Reporting) |
| `SPLUNK_OWNER` | `admin` | REST namespace user; use `nobody` only if your deployment expects app-shared objects that way |
| `SPLUNK_VERIFY_SSL` | `1` | Set to `0` for self-signed certs in lab (**not** for production) |

**Example — token**

```bash
export SPLUNK_HOST="splunk.mycompany.com"
export SPLUNK_TOKEN="eyJ..."   # from Splunk Web → Account → Tokens, or your org’s token flow
python3 scripts/deploy_dashboard_studio_rest.py \
  --file dashboards/catalog-quick-start-top2.json \
  --name catalog_quick_start_top2
```

**Example — username / password**

```bash
export SPLUNK_HOST="splunk.mycompany.com"
export SPLUNK_USER="admin"
export SPLUNK_PASSWORD='your-password'
python3 scripts/deploy_dashboard_studio_rest.py \
  --file dashboards/catalog-quick-start-top2.json \
  --name catalog_quick_start_top2
```

**Lab / self-signed TLS**

```bash
export SPLUNK_VERIFY_SSL=0
# or
python3 scripts/deploy_dashboard_studio_rest.py --file dashboards/catalog-quick-start-top2.json --insecure
```

The script tries **create** first; if the dashboard ID already exists, it **POST**s an **update** to `.../data/ui/views/<name>`.

After success, open **Search & Reporting** (or your `--app`) → **Dashboards** → find the dashboard by **label** (same as the JSON `title`).

To regenerate this file after editing the Quick Start lists in `use-cases/INDEX.md`, update the UC lists in **`scripts/generate_catalog_dashboard.py`** and run:

```bash
python3 scripts/generate_catalog_dashboard.py
```

## Executive demo (`executive-health-dashboard.json`)

Oil & gas–themed **network health** demo (map, availability, threats, site table). Same import steps as above.
