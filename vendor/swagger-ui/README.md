# Swagger UI 5.17.14 — vendored assets

These files are pinned copies of the upstream
[Swagger UI](https://github.com/swagger-api/swagger-ui) release `v5.17.14`
used by `/api-docs.html`.

Files are vendored (rather than loaded from a CDN) so that:

- the dashboard keeps working if the CDN is unreachable;
- every asset served by GitHub Pages is auditable via
  `shasum -a 256 vendor/swagger-ui/*` (see `checksums.txt`);
- there is no network dependency on third-party JavaScript for users
  who browse the API docs page.

## Licence

Swagger UI is distributed under the Apache License 2.0; the upstream
licence text is preserved in `LICENSE`.  The project's trademark policy
applies to the Swagger name and logos, which remain property of
[SmartBear Software](https://smartbear.com/).

## Refresh procedure

```bash
# 1. Pick the new version
VER=5.17.14  # or whatever you want to upgrade to

# 2. Download the three files
for f in swagger-ui.css swagger-ui-bundle.js swagger-ui-standalone-preset.js; do
  curl -sL -o "vendor/swagger-ui/${f}" \
    "https://cdn.jsdelivr.net/npm/swagger-ui-dist@${VER}/${f}"
done

# 3. Refresh the LICENSE
curl -sL -o vendor/swagger-ui/LICENSE \
  "https://raw.githubusercontent.com/swagger-api/swagger-ui/v${VER}/LICENSE"

# 4. Regenerate checksums
shasum -a 256 vendor/swagger-ui/*.js vendor/swagger-ui/*.css \
  > vendor/swagger-ui/checksums.txt

# 5. Update the version string in api-docs.html's header banner.
```
