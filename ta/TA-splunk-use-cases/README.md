# TA-splunk-use-cases — Splunk Monitoring Use Cases

A Splunk Technology Add-on (TA) that packages the highest-impact "Quick
Start" use cases from the upstream
[splunk-monitoring-use-cases](https://github.com/fenre/splunk-monitoring-use-cases)
catalog as ready-to-enable saved searches, macros, and event types.

## What it contains

- **`default/savedsearches.conf`** — ~115 saved searches (one per Quick-Start
  UC across 23 technology domains).  All searches ship **disabled by default**
  and are not scheduled; an administrator must enable each one deliberately.
- **`default/macros.conf`** — Per-category `uc_index_<cat>` macros that
  default to `index=*`.  Override the definition in `local/macros.conf` to
  scope each category to the correct index in your environment.
- **`default/eventtypes.conf`** + **`default/tags.conf`** — Common sourcetype
  shortcuts (`uc_linux_cpu`, `uc_windows_sec`, `uc_aws_cloudtrail`, …) tagged
  for CIM compatibility where applicable.
- **`default/data/ui/nav/default.xml`** — Minimal navigation linking back
  to the upstream dashboard and source repository.
- **`metadata/default.meta`** — Default role-based access permissions
  (read for everyone, write for `admin`/`power`).
- **`app.manifest`** + **`default/app.conf`** — Splunkbase metadata and app
  descriptor for the current version (`5.2.0`).

## What it does **not** do

- It does **not** ingest any data.  You must install the appropriate
  technology add-ons (Splunk_TA_nix, Splunk_TA_windows,
  Splunk Add-on for Amazon Web Services, …) to populate the indexes that
  the saved searches read from.
- It does **not** modify your indexes, roles, or authentication
  configuration.
- It does **not** enable alerts automatically.  Every saved search is
  `disabled = 1` at install time — review, tune, and enable per search.

## Supported platforms

| Capability                  | Support                                  |
|-----------------------------|------------------------------------------|
| Splunk Enterprise           | 9.x, 10.x (AppInspect Cloud-compatible)   |
| Splunk Cloud Platform        | Yes (read-only knowledge objects only)   |
| Splunk Common Information Model | 5.3+ (aligned but does not bundle CIM)    |
| Deployment topology         | Search head(s), standalone, distributed   |

## Installation

1. Download `TA-splunk-use-cases-<version>.spl` from the
   [Releases page](https://github.com/fenre/splunk-monitoring-use-cases/releases).
2. In Splunk Web: *Apps → Manage Apps → Install app from file*.
3. Restart Splunk (or reload configuration — saved searches are read at
   search time so a full restart is not strictly required).
4. Install the upstream data source add-ons you actually use
   (Splunk_TA_nix, Splunk_TA_windows, Splunk_TA_aws, …).
5. **Override the index macros** in `local/macros.conf` to match your
   environment.  Example:

       [uc_index_os]
       definition = index=linux OR index=windows

6. Enable the individual saved searches you want to schedule.

## Upgrade path

Releases are semver-versioned (`MAJOR.MINOR.PATCH`).  Any change that
alters an existing saved search's SPL or default schedule bumps the
`MINOR` component.  Bug fixes (typos, metadata) bump `PATCH`.  Complete
content regenerations or schema changes bump `MAJOR`.

Because all saved searches live in `default/`, your customizations in
`local/` are preserved across upgrades.

## Regenerating TA content

The `default/*.conf` files are **generated** from `catalog.json` and
`use-cases/INDEX.md`.  Re-generate them with:

    python3 scripts/build_ta.py

## Support and upstream

- GitHub (content + bug reports):
  <https://github.com/fenre/splunk-monitoring-use-cases>
- License: MIT (see `LICENSE` in the repository root).
- This TA is a **community project** — not an officially supported Splunk
  product.  No warranty is implied.  Review every search against your
  environment before enabling.
