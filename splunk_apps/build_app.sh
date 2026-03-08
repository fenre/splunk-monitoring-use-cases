#!/usr/bin/env bash
# Build the IMUCL Splunk app (v0.0.1): generate data.js, copy dashboard assets, optionally package .spl
# Run from repo root: ./splunk_apps/build_app.sh [--package]
# Uses parent repo for build.py, index.html, data.js, custom-text.js.

set -e
SPLUNK_APPS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SPLUNK_APPS_DIR/.." && pwd)"
APP_DIR="$SPLUNK_APPS_DIR/imucl"
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
python3 "$SPLUNK_APPS_DIR/imucl/patch_dashboard_base.py" "$DASHBOARD_DIR/index.html"

echo "App content ready at: $APP_DIR"

if [[ "$1" == "--package" ]]; then
  SPL_NAME="imucl-0.0.1.spl"
  echo "Packaging $SPL_NAME (tar.gz for Splunk)..."
  (cd "$SPLUNK_APPS_DIR" && COPYFILE_DISABLE=1 tar --format ustar -cvzf "$SPL_NAME" imucl)
  echo "Created: $SPLUNK_APPS_DIR/$SPL_NAME"
  echo "Install in Splunk: Apps → Install app from file → $SPL_NAME"
fi
