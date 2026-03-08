# Use Case Library — Splunk UI Toolkit (React) App

This app is built with **React** and **Vite** and runs as a single-page app inside a Splunk view (no iframe). It loads the use case catalog from `catalog.json` and renders categories and use case detail with a dark theme. The structure is ready for **Splunk UI Toolkit** (`@splunk/react-ui`) components if you add them via the official `npx @splunk/create` scaffold and migrate the views.

## Requirements

- **Node.js** 18+
- **Python 3** (for `build.py` to generate `catalog.json`)
- **yarn** or **npm**

## Build and package (from repo root)

```bash
./splunk_apps/build_uitoolkit_app.sh
```

This will:

1. Run `build.py` (in repo root) to generate `data.js` and **`catalog.json`**
2. Install dependencies in `splunk_apps/imucl_uitoolkit/` (React, Vite)
3. Build the React app with Vite → `imucl_uitoolkit/dist/`
4. Copy `catalog.json` and `dist/assets/*` into `splunk_app/appserver/static/`
5. Package the Splunk app as **`imucl-uitoolkit-0.0.1.spl`** in `splunk_apps/` (tar.gz)

Then install in Splunk: **Apps → Install app from file** → choose `splunk_apps/imucl-uitoolkit-0.0.1.spl`.

## Develop locally (without Splunk)

From `imucl_uitoolkit/`:

```bash
yarn install
yarn dev
```

Open http://localhost:5173. The app will try to load `../static/catalog.json`, which won’t exist there. For local dev you can copy `catalog.json` from repo root into `public/` and change `App.jsx` to fetch `catalog.json` from `./catalog.json`, or run a small static server that serves the repo root.

## Structure

- **src/App.jsx** — Loads catalog, renders category list + detail.
- **src/CategoryList.jsx** — Categories and use case list (Splunk UI components).
- **src/UseCaseDetail.jsx** — Detail panel for selected use case (name, SPL, implementation).
- **splunk_app/** — Splunk app shell (app.conf, nav, view that loads the React bundle).
- **splunk_app/appserver/static/** — Filled by build: `catalog.json` + Vite `assets/`.

The Splunk view does **not** run the React script inside the dashboard (Splunk strips or blocks `<script>` in HTML panels). Instead the view embeds an **iframe** that loads the full page `../static/index.html`. That page is a normal HTML document; its `<script type="module">` runs in the browser, so the React app loads and fetches `catalog.json` from the same directory.
