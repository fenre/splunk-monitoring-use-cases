#!/usr/bin/env bash
# Build the Splunk UI Toolkit (React) app and package as .spl
# Run from repo root: ./splunk_apps/build_uitoolkit_app.sh
# Uses parent repo for build.py and catalog.json. Requires: Node 18+, yarn or npm, python3

set -e
SPLUNK_APPS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SPLUNK_APPS_DIR/.." && pwd)"
UITOOLKIT="$SPLUNK_APPS_DIR/imucl_uitoolkit"
SPLUNK_APP="$UITOOLKIT/splunk_app"
STATIC="$SPLUNK_APP/appserver/static"

cd "$REPO_ROOT"

echo "1. Building use case data (build.py -> data.js + catalog.json)..."
python3 build.py

echo "2. Installing UI Toolkit app dependencies..."
cd "$UITOOLKIT"
if command -v yarn >/dev/null 2>&1; then
  yarn install
else
  npm install
fi

echo "3. Building React app (Vite -> dist/)..."
if command -v yarn >/dev/null 2>&1; then
  yarn build
else
  npm run build
fi

echo "4. Copying assets into Splunk app..."
mkdir -p "$STATIC"
cp "$REPO_ROOT/catalog.json" "$STATIC/"
cp -r dist/assets "$STATIC/"
cp dist/index.html "$STATIC/" 2>/dev/null || true
# Placeholder app icons (avoid 404 for appLogo.png / appIcon.png)
python3 << EOF
import base64, os
static = "$STATIC"
png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')
for name in ('appLogo.png', 'appIcon.png'):
    with open(os.path.join(static, name), 'wb') as f:
        f.write(png)
EOF
echo "  Added appLogo.png and appIcon.png (placeholders)."

echo "5. Packaging Splunk app (.spl)..."
SPL_NAME="imucl-uitoolkit-0.0.1.spl"
TAR_DIR=$(mktemp -d)
cp -R "$UITOOLKIT/splunk_app" "$TAR_DIR/imucl"
COPYFILE_DISABLE=1 tar --format ustar -cvzf "$SPLUNK_APPS_DIR/$SPL_NAME" -C "$TAR_DIR" imucl
rm -rf "$TAR_DIR"

echo "Done. Created: $SPLUNK_APPS_DIR/$SPL_NAME"
echo "Install in Splunk: Apps → Install app from file → $SPL_NAME"
