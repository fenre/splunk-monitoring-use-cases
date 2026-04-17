#!/usr/bin/env bash
# Package the ITSI content pack as a .spl archive suitable for
# installation into Splunk ITSI search heads.
#
# Usage:  scripts/package_itsi.sh [output_dir]
#   default output_dir: dist/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUT_DIR="${1:-${REPO_ROOT}/dist}"
APP_DIR="${REPO_ROOT}/ta/DA-ITSI-monitoring-use-cases"

if [ ! -d "${APP_DIR}" ]; then
    echo "error: ${APP_DIR} not found" >&2
    exit 1
fi

mkdir -p "${OUT_DIR}"

VERSION="$(python3 -c 'import json; d=json.load(open("ta/DA-ITSI-monitoring-use-cases/app.manifest")); print(d["info"]["id"]["version"])' 2>/dev/null || echo "unknown")"
OUT_FILE="${OUT_DIR}/DA-ITSI-monitoring-use-cases-${VERSION}.spl"

TMP_STAGE="$(mktemp -d)"
trap 'rm -rf "${TMP_STAGE}"' EXIT

cp -R "${APP_DIR}" "${TMP_STAGE}/DA-ITSI-monitoring-use-cases"
rm -rf "${TMP_STAGE}/DA-ITSI-monitoring-use-cases/local"
find "${TMP_STAGE}/DA-ITSI-monitoring-use-cases" -name ".DS_Store" -delete
find "${TMP_STAGE}/DA-ITSI-monitoring-use-cases" -name "__pycache__" -type d -prune -exec rm -rf {} +

tar -C "${TMP_STAGE}" -czf "${OUT_FILE}" DA-ITSI-monitoring-use-cases

if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${OUT_FILE}" | awk '{print $1}' > "${OUT_FILE}.sha256"
elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${OUT_FILE}" | awk '{print $1}' > "${OUT_FILE}.sha256"
fi

echo "Packaged ${OUT_FILE}"
echo "  size: $(wc -c < "${OUT_FILE}") bytes"
if [ -f "${OUT_FILE}.sha256" ]; then
    echo "  sha256: $(cat "${OUT_FILE}.sha256")"
fi
