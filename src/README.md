# `src/` — author-edited web assets

These are the v7 source-of-truth web assets. The build pipeline
(`tools/build/render_assets.py`) bundles, fingerprints, and inlines
them into `dist/` — sources here are NEVER served to end-users
verbatim.

## Layout

```
src/
├── styles/         5 hand-written CSS files, split by concern.
│                   Concatenated and fingerprinted into
│                   dist/assets/styles.<hash>.css.
│                   Critical (01-tokens + 02-base) is inlined into
│                   <style> in <head> for above-the-fold rendering.
│                   See src/styles/README.md.
│
├── scripts/        5 hand-written JS files, split by concern.
│                   Concatenated and fingerprinted into
│                   dist/assets/app.<hash>.js. Loaded via
│                   <script defer> at end of <body>.
│                   See src/scripts/README.md.
│
├── partials/       HTML fragments included by render_pages.py
│                   (planned; lands in ssg-per-uc-category todo).
│
├── pages/          HTML pages render_pages.py uses as templates
│                   (planned; lands in ssg-per-uc-category todo —
│                   landing, about, changelog, governance).
│
├── img/            author-supplied images. Copied to
│                   dist/assets/img/ verbatim. Fingerprinting and
│                   responsive-srcset emission lands in a future
│                   asset-pipeline iteration.
│
└── fonts/          self-hosted webfont files (woff2). Copied to
                    dist/assets/fonts/ verbatim. Currently empty —
                    Inter + Roboto Mono load via Google Fonts CDN.
```

## Stability

| Path                          | Public URL?              | Stable across builds? |
| ----------------------------- | ------------------------ | --------------------- |
| `src/styles/*.css`            | No (source only)         | Yes — names you pick  |
| `src/scripts/*.js`            | No (source only)         | Yes — names you pick  |
| `dist/assets/styles.<hash>.css` | **Yes** — `assets/styles.<hash>.css` | Filename embeds the SHA-256 of contents; immutable for the life of one build artefact |
| `dist/assets/app.<hash>.js`    | **Yes** — `assets/app.<hash>.js`     | Same — immutable per build |

Filenames in `src/` are NOT a public contract. The numeric prefix
(`01-`, `02-`, …) sets bundle order — see the per-directory READMEs.

## Don't put here

* Generated content (lives in `dist/` and `api/`).
* Third-party libraries (vendor into `vendor/` and load via
  documented CDN URLs from `src/scripts/`).
* Markdown content for use cases (lives in `content/`, see
  `content/README.md`).

## Local dev workflow

```sh
# Edit a stylesheet or script under src/styles/ or src/scripts/
$ vim src/styles/03-components.css

# Mirror into the legacy inline blocks in index.html for
# direct python -m http.server preview (transitional)
$ python3 tools/audits/asset_drift.py --fix

# Or build the v7 dist/ artefact and preview that
$ python3 tools/build/build.py --out dist
$ cd dist && python3 -m http.server 8000
```

CI runs `python3 tools/audits/asset_drift.py` and blocks PRs that
desynchronise `src/` from the legacy inline blocks. Once the
`cleanup-and-docs` todo lands and the source `index.html` is
deleted, the audit retires and `src/` becomes the only writable
surface.
