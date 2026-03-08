# Splunk apps (deprecated)

This folder contains **all Splunk app–related content** that was previously at the repo root. It is **deprecated** in this project. The plan is to spin it off into a **separate project** later.

## Contents

| Path | Description |
|------|-------------|
| **imucl/** | Classic Splunk app (iframe embedding the static dashboard). See [imucl/README.md](imucl/README.md). |
| **imucl_uitoolkit/** | React-based Splunk app (Vite + iframe to static/index.html). See [imucl_uitoolkit/README.md](imucl_uitoolkit/README.md). |
| **build_app.sh** | Build and optionally package the classic app. Run from **repo root**: `./splunk_apps/build_app.sh [--package]`. |
| **build_uitoolkit_app.sh** | Build and package the UI Toolkit app. Run from **repo root**: `./splunk_apps/build_uitoolkit_app.sh`. |
| **splunk-app-design.md** | Design doc (UCC-based layout, catalog, saved searches). For reference when creating the new project. |

## Build scripts and parent repo

Both build scripts assume they are run from the **parent repo root** (e.g. `./splunk_apps/build_app.sh`). They use the parent repo for:

- `build.py` (generates `data.js`, `catalog.json`)
- `index.html`, `data.js`, `custom-text.js` (classic app)
- `catalog.json` (UI Toolkit app)

Generated `.spl` packages are written into **this folder** (`splunk_apps/`).

## Future standalone project

When you create the new project, you can copy this folder (or parts of it) and:

1. Adjust build scripts to either depend on this use-case repo as a submodule/data source or ship a static catalog.
2. Use [splunk-app-design.md](splunk-app-design.md) for the target architecture (UCC, catalog lookup, saved searches).
