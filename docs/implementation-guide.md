# Implementation Guide — Splunk directory, apps, and inputs

This guide covers **tasks that are common across use cases**: where files live, how to install apps, how to configure inputs (including scripted inputs), and where searches and alerts are stored. Use it together with each use case’s **Implementation** and **View more detailed instructions** in the dashboard.

---

## 1. Splunk directory structure

- **`$SPLUNK_HOME`** — Root of the Splunk installation (e.g. `/opt/splunk` on Linux, `C:\Program Files\Splunk` on Windows).
- **`$SPLUNK_HOME/etc/apps/`** — All apps and add-ons are installed here. Each app has its own folder (e.g. `Splunk_TA_nix`, `search`).
- **`$SPLUNK_HOME/etc/system/`** — Built-in Splunk configuration. Prefer not to edit here; override in your app’s `local/` or in `etc/apps/<your_app>/local/`.
- **Inside an app:**
  - **`default/`** — Default config and UI; shipped with the app. Do not edit; your changes would be overwritten on upgrade.
  - **`local/`** — Your overrides. Create `local/` and put your `.conf` and other files here. Upgrades do not overwrite `local/`.
- **Indexes** — Index definitions live in `indexes.conf` (under an app’s `default/` or `local/`). Index data is stored in the path specified by `homePath` / `coldPath` (often under `$SPLUNK_HOME/var/lib/splunk/`).

---

## 2. Installing and managing apps and add-ons

- **Install from Splunkbase:** In Splunk Web: **Apps → Find more apps**, or download the `.spl` (or `.tgz`) and install via **Apps → Install app from file**.
- **Install via CLI:**  
  `$SPLUNK_HOME/bin/splunk install app <path-to-spl-or-tgz> -auth <user>:<password>`
- **App location after install:** The app is unpacked under `$SPLUNK_HOME/etc/apps/<app_name>/`.
- **Upgrade:** Install the new version over the existing app; your `local/` directory is preserved. Review release notes for breaking changes.
- **Enable/disable:** In `app.conf` under the app’s `local/`, set `state = disabled` to disable; remove or set `state = enabled` to enable. Restart Splunk (or reload the app) when changing.

---

## 3. Configuring inputs

Inputs define what data Splunk collects. They are configured in **`inputs.conf`** in an app’s `default/` (shipped) or **`local/`** (your overrides).

### 3.1 Where to put inputs.conf

- **App-scoped (recommended):**  
  `$SPLUNK_HOME/etc/apps/<YourApp>/local/inputs.conf`  
  Use an app that represents the use case or data source (e.g. the TA for that technology).
- **System-wide (avoid when possible):**  
  `$SPLUNK_HOME/etc/system/local/inputs.conf`  
  Only for inputs that truly apply to the whole instance.

### 3.2 File and directory monitoring

```ini
[monitor:///var/log/myapp/*.log]
sourcetype = myapp
index = main
disabled = 0
```

- Use **`local/inputs.conf`** in the appropriate app.
- After editing, run:  
  `$SPLUNK_HOME/bin/splunk restart`  
  or **Settings → Data inputs** in Splunk Web to enable/disable without full restart where supported.

### 3.3 Scripted inputs

Scripted inputs run a script on a schedule; stdout is indexed as events.

**Example `inputs.conf` stanza:**

```ini
[script://$SPLUNK_HOME/etc/apps/MyApp/bin/collect_metrics.sh]
interval = 300
sourcetype = myapp:metrics
index = main
disabled = 0
```

- **Script path:** Prefer a path under the app (e.g. `$SPLUNK_HOME/etc/apps/MyApp/bin/`) so the app can be deployed with the script.
- **Interval:** `interval = 300` = run every 5 minutes. Use `cron.schedule` for cron-style scheduling if needed.
- **Sourcetype:** Set a clear `sourcetype` so the use case’s SPL can target it.
- **Script content:** The script should print one event per line (or use a format your props/transforms expect). See the use case’s **Script example** (if present) or **View more detailed instructions** for a concrete example.

**Script best practices:**

- Use a shebang (e.g. `#!/usr/bin/env bash` or `#!/usr/bin/env python3`).
- Ensure the script is executable (`chmod +x`).
- Prefer key-value or structured output (e.g. `key=value`) so fields can be extracted.
- Avoid writing secrets into the script; use Splunk’s password storage or environment provided by the deployment.

### 3.4 Windows inputs (Event Log, WMI, etc.)

- Event Log: e.g. `[WinEventLog://Security]` in `inputs.conf` (often in the Windows TA’s `local/`).
- Configure on the forwarder or indexer as appropriate. Many use cases assume the relevant TA is installed and inputs are enabled in **Settings → Data inputs**.

---

## 4. Where searches, reports, alerts, and dashboards live

- **Searches / reports / alerts:** Stored as knowledge objects in the **search** app (or another app you assign). In the UI: **Search → Save as** (Report, Alert, or Dashboard panel). On disk they live under `$SPLUNK_HOME/etc/apps/search/local/` (e.g. `savedsearches.conf`, `reportbuilder.conf`).
- **Dashboards:** Stored in the same app (e.g. `search` or a custom app). Simple XML / Dashboard Studio definitions under `local/data/ui/views/` or equivalent.
- **Deployment:** To move searches/alerts/dashboards to another instance, copy the app (including `local/`) or use export/import (e.g. **Settings → Export** / deploy the app bundle).

---

## 5. Restart and reload

- **Inputs / props / transforms:** A full **restart** of Splunk (`$SPLUNK_HOME/bin/splunk restart`) is the most reliable after changing `inputs.conf` or index settings. Some input types can be enabled/disabled from the UI without restart.
- **Searches / dashboards / lookups:** Changes to knowledge objects and many config changes take effect after **reload** (e.g. **Settings → Reload** in the UI) or on next restart; no index restart needed for saved searches alone.

---

## 6. Linking from use cases

In the dashboard, each use case’s **View more detailed instructions** includes a link to this guide for:

- App installation and the Splunk directory
- Configuring inputs (including scripted inputs) and `inputs.conf`
- Where to create and store searches, reports, and alerts

Use this guide for the **common steps**; use the use case’s Implementation and SPL for the **specific** data source, search, and thresholds.
