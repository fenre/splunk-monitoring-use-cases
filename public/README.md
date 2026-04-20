# public/

Files in this directory are copied verbatim into `dist/` by
`tools/build/build.py` (the `public` stage in
`tools/build/build.py:_stage_public`).

Use this directory for assets that don't go through the fingerprinting
pipeline:

* `favicon.ico`, `favicon.svg`, `icon-*.png`
* `robots.txt`
* `.nojekyll` (required so GitHub Pages doesn't process the site as Jekyll)
* `CNAME` (if you serve the site on a custom domain)
* `.well-known/security.txt`
* OpenGraph fallback images
* Any third-party file that must keep its exact filename

Don't put fingerprinted assets here — those live under `src/` and are
hashed by `render_assets.py`. Don't put generated files here — those
live in `dist/` only.
