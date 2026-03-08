#!/usr/bin/env bash
# Build the IMUCL Splunk app (v0.0.1): generate data.js, copy dashboard assets, optionally package .spl
# Run from repo root: ./build_app.sh [--package]

set -e
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$REPO_ROOT/imucl"
DASHBOARD_DIR="$APP_DIR/appserver/static/dashboard"

cd "$REPO_ROOT"

echo "Building use case data (build.py)..."
python3 build.py

echo "Copying dashboard assets into app..."
mkdir -p "$DASHBOARD_DIR"
cp "$REPO_ROOT/index.html" "$DASHBOARD_DIR/"
cp "$REPO_ROOT/data.js" "$DASHBOARD_DIR/"
cp "$REPO_ROOT/custom-text.js" "$DASHBOARD_DIR/"

# Ensure relative script paths (data.js, custom-text.js) resolve when loaded in iframe
python3 "$REPO_ROOT/imucl/patch_dashboard_base.py" "$DASHBOARD_DIR/index.html"

echo "App content ready at: $APP_DIR"

if [[ "$1" == "--package" ]]; then
  SPL_NAME="imucl-0.0.1.spl"
  echo "Packaging $SPL_NAME (tar.gz for Splunk)..."
  # Splunk expects a compressed TAR archive (.spl / .tgz), not zip (see dev.splunk.com packaging docs)
  (cd "$REPO_ROOT" && COPYFILE_DISABLE=1 tar --format ustar -cvzf "$SPL_NAME" imucl)
  echo "Created: $REPO_ROOT/$SPL_NAME"
  echo "Install in Splunk: Apps → Install app from file → $SPL_NAME"
fi
