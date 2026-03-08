# Infrastructure & Security Use Case Library (IMUCL) — Splunk App

**Version 0.0.1** — Sample app that embeds the Use Case Library dashboard inside Splunk (Option B from [splunk-app-design.md](../docs/splunk-app-design.md)).

## What this app does

- Adds an app **"Infrastructure & Security Use Case Library"** to Splunk.
- The default view embeds the same dashboard as the repo’s `index.html` (browse use cases, filters, detail modals, SPL, implementation notes).

## Install and test

### Option 1: Install from app directory (development)

1. From the repo root, ensure the dashboard assets are in the app:
   ```bash
   ./build_app.sh
   ```
2. Copy or symlink the `imucl` folder into your Splunk apps directory:
   - **Linux/macOS:** `$SPLUNK_HOME/etc/apps/imucl` → symlink or copy from repo `imucl/`
   - Example: `ln -s /path/to/splunk-monitoring-use-cases/imucl $SPLUNK_HOME/etc/apps/imucl`
3. Restart Splunk or reload the app: **Settings → Apps → Infrastructure & Security Use Case Library → Reload**.
4. Open the app from the **App** menu. The Use Case Library view loads the embedded dashboard.

### Option 2: Install from .spl package

1. From the repo root:
   ```bash
   ./build_app.sh --package
   ```
2. This creates `imucl-0.0.1.spl` in the repo root.
3. In Splunk Web: **Apps → Install app from file** and choose `imucl-0.0.1.spl`.
4. Restart if prompted, then open the app from the App menu.

## App structure

```
imucl/
├── default/
│   ├── app.conf
│   └── data/ui/
│       ├── nav/default.xml
│       └── views/use_case_library.xml   # iframe → static dashboard
├── appserver/static/dashboard/
│   ├── index.html
│   ├── data.js
│   └── custom-text.js
├── metadata/default.meta
└── README.md (this file)
```

Dashboard assets in `appserver/static/dashboard/` are copied by `build_app.sh` from the repo root (after `build.py` runs).

## Rebuilding after use case changes

After editing `use-cases/*.md` or `INDEX.md`, run from repo root:

```bash
./build_app.sh
```

Then reload the app in Splunk (or reinstall the .spl if you use the package).

## If the dashboard is empty

1. **Try “Open Use Case Library in new tab”** at the top of the view. If that loads the dashboard, the iframe may be blocked by CSP or the path; the direct link should still work.
2. **Reinstall the app** after running `./build_app.sh --package` so the patched `index.html` (with base URL fix for iframe script loading) is in the package.
3. **Check the browser console** (F12 → Console) on the app page for 404s or script errors; ensure `data.js` and `custom-text.js` load from `.../static/dashboard/`.

## Requirements

- Splunk Enterprise or Cloud (tested with 9.x).
- No mandatory add-ons; the catalog references recommended TAs per use case.
