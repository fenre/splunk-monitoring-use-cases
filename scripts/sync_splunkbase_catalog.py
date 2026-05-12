#!/usr/bin/env python3
"""Sync ``data/splunkbase-catalog.json`` from the public Splunkbase REST API.

The recommender app (``splunk-uc-recommender``) and the v9.0 migration generator
(``python3 -m splunk_uc generate-splunkbase-mappings``) consume this catalog to render the
per-card "Required Splunkbase apps" section and to compute install-guidance
status. The catalog is checked into the repository so that:

- The recommender app does not have to call splunkbase.splunk.com at runtime
  (Splunk Cloud apps cannot reach arbitrary outbound origins).
- The audits (``tools/audits/splunkbase_ids.py``) run hermetically against the
  cached metadata.
- Diffs to the catalog are reviewable in regular pull requests.

Modes:
  --check   Default. Hermetic. Re-reads the catalog from disk, validates shape,
            applies overrides in ``data/splunkbase-catalog-overrides.json``, and
            exits 0 on a well-formed catalog. Safe to run in pull-request CI.
  --sync    Network-enabled. Paginates the public Splunkbase REST API at
            ``https://splunkbase.splunk.com/api/v1/app/`` (HTTPS, TLSv1.2+),
            throttles at 1 request/sec, honours ``Retry-After`` on HTTP 429,
            and writes only entries whose body actually changed (deterministic
            JSON, sorted keys). Intended for the scheduled GitHub Actions job
            ``.github/workflows/splunkbase-sync.yml``, which then opens a PR
            via ``peter-evans/create-pull-request@<pinned-sha>``.

Resilience contract:
  - On any ``URLError`` / non-2xx response / JSON-decode failure, the existing
    catalog is preserved, a diagnostic is written to stderr, and the script
    exits 0. We never fail CI on a Splunkbase outage; the cache is the single
    source of truth.
  - The script never writes ``$comment`` or ``schemaVersion`` mutations.
  - The script never makes outbound calls to anything other than
    ``splunkbase.splunk.com``.

Security posture (rule codeguard-0-api-web-services):
  - HTTPS-only. Hard-fail on any other scheme.
  - TLSv1.2+, default trust store, default certificate validation.
  - User-Agent identifies the project so Splunkbase ops can rate-limit per
    consumer.
  - Response size capped at ``MAX_RESPONSE_BYTES`` per page to bound memory.
  - Per-page sleep ``SLEEP_BETWEEN_REQUESTS`` plus 429 ``Retry-After`` honour
    means we never hammer the API.

Exit codes:
  0 = GREEN (catalog is valid, or sync completed / fell back to cache).
  1 = catalog is structurally invalid (e.g., the JSON file does not parse).
  2 = internal error (unhandled exception path).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "data" / "splunkbase-catalog.json"
OVERRIDES_PATH = REPO_ROOT / "data" / "splunkbase-catalog-overrides.json"

API_BASE = "https://splunkbase.splunk.com/api/v1/app/"
ALLOWED_HOST = "splunkbase.splunk.com"

USER_AGENT = (
    "splunk-monitoring-use-cases/splunkbase-catalog-sync/1.0 "
    "(+https://github.com/fsudmann/splunk-monitoring-use-cases)"
)
HTTP_TIMEOUT_SECONDS = 30
SLEEP_BETWEEN_REQUESTS = 1.0
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
# Splunkbase capped server-side ``limit`` at 100 in mid-2026; values above
# 100 now return ``HTTP 400 {"errors": ["limit may not exceed 100"]}``.
# Bumping ``MAX_PAGES`` keeps the 200-page upper-bound on total fetched
# apps (200 × 100 = 20,000) well above the live catalogue (~1,800 apps).
PAGE_SIZE = 100
MAX_PAGES = 200
MAX_RETRIES_PER_PAGE = 3

CANONICAL_FIELDS = (
    "id",
    "name",
    "displayName",
    "description",
    "url",
    "latestVersion",
    "vendor",
    "cloudVetted",
    "splunkVersionsSupported",
    "category",
    "numDownloads",
    "lastUpdated",
)


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def _read_json(path: pathlib.Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise SystemExit(f"[sync_splunkbase_catalog] {path}: {err}") from err


def _write_json(path: pathlib.Path, body: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialised = json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.write_text(serialised, encoding="utf-8")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Catalog shape helpers
# ---------------------------------------------------------------------------


def _empty_catalog() -> Dict[str, Any]:
    return {
        "$comment": "Curated Splunkbase app metadata. Refreshed by scripts/sync_splunkbase_catalog.py.",
        "schemaVersion": 1,
        "lastUpdated": _today(),
        "source": {
            "api": API_BASE,
            "syncScript": "scripts/sync_splunkbase_catalog.py",
            "overrides": "data/splunkbase-catalog-overrides.json",
        },
        "apps": {},
    }


def _validate_catalog(catalog: Dict[str, Any]) -> List[str]:
    """Return a list of structural error messages; empty list means valid."""
    errors: List[str] = []
    if not isinstance(catalog, dict):
        return ["catalog top level is not an object"]

    if catalog.get("schemaVersion") != 1:
        errors.append(f"schemaVersion must be 1; got {catalog.get('schemaVersion')!r}")
    apps = catalog.get("apps")
    if not isinstance(apps, dict):
        errors.append("'apps' must be an object keyed by string app id")
        return errors

    for key, entry in apps.items():
        if not key.isdigit():
            errors.append(f"app key {key!r} must be a numeric string")
            continue
        if not isinstance(entry, dict):
            errors.append(f"app {key} must be an object")
            continue
        if entry.get("id") != int(key):
            errors.append(f"app {key} 'id' field must equal {int(key)}")
        for required in ("id", "name", "displayName", "url"):
            if not entry.get(required):
                errors.append(f"app {key} missing required field {required!r}")
        url = entry.get("url") or ""
        if url and not url.startswith(f"https://{ALLOWED_HOST}/app/"):
            errors.append(
                f"app {key} url must start with https://{ALLOWED_HOST}/app/ ; got {url!r}"
            )
    return errors


def _apply_overrides(catalog: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Merge ``overrides`` on top of ``catalog``. Per-app shallow merge."""
    merged = json.loads(json.dumps(catalog))
    apps = merged.setdefault("apps", {})
    for key, entry in (overrides.get("apps") or {}).items():
        if not isinstance(entry, dict):
            continue
        if key not in apps:
            apps[key] = entry
            continue
        for field, value in entry.items():
            apps[key][field] = value
    return merged


# ---------------------------------------------------------------------------
# Splunkbase API client
# ---------------------------------------------------------------------------


def _ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


def _validate_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Splunkbase URLs must be HTTPS; got {url!r}")
    if parsed.hostname != ALLOWED_HOST:
        raise ValueError(
            f"Splunkbase URLs must target {ALLOWED_HOST!r}; got host {parsed.hostname!r}"
        )


def _fetch_page(offset: int, page_size: int) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Fetch one page of ``/api/v1/app/``.

    Returns ``(body, error_message)``. ``body`` is None on any failure path so
    the caller can decide whether to abort the sync (and keep the cache) or
    surface a partial-page diagnostic.
    """

    params = urllib.parse.urlencode(
        {"limit": page_size, "offset": offset, "order": "latest"}
    )
    url = f"{API_BASE}?{params}"
    try:
        _validate_url(url)
    except ValueError as err:
        return None, f"refusing to fetch non-allow-listed URL: {err}"

    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )

    last_error: Optional[str] = None
    for attempt in range(1, MAX_RETRIES_PER_PAGE + 1):
        try:
            with urllib.request.urlopen(
                request, timeout=HTTP_TIMEOUT_SECONDS, context=_ssl_context()
            ) as response:
                if response.status != 200:
                    last_error = f"HTTP {response.status} on offset {offset}"
                    return None, last_error
                payload = response.read(MAX_RESPONSE_BYTES + 1)
                if len(payload) > MAX_RESPONSE_BYTES:
                    return None, f"response from offset {offset} exceeds {MAX_RESPONSE_BYTES} bytes"
                try:
                    return json.loads(payload.decode("utf-8")), None
                except (json.JSONDecodeError, UnicodeDecodeError) as err:
                    return None, f"malformed JSON at offset {offset}: {err}"
        except urllib.error.HTTPError as err:
            if err.code == 429 and attempt < MAX_RETRIES_PER_PAGE:
                retry_after_raw = err.headers.get("Retry-After", "") if err.headers else ""
                try:
                    retry_after = max(1.0, min(120.0, float(retry_after_raw)))
                except ValueError:
                    retry_after = SLEEP_BETWEEN_REQUESTS * (2 ** attempt)
                print(
                    f"[sync_splunkbase_catalog] offset {offset}: 429; "
                    f"sleeping {retry_after:.1f}s before retry {attempt + 1}",
                    file=sys.stderr,
                )
                time.sleep(retry_after)
                continue
            last_error = f"HTTP {err.code} on offset {offset}: {err.reason}"
            return None, last_error
        except urllib.error.URLError as err:
            last_error = f"network error on offset {offset}: {err.reason}"
            return None, last_error
        except (TimeoutError, OSError) as err:
            last_error = f"transport error on offset {offset}: {err}"
            return None, last_error
    return None, last_error or f"exceeded retries on offset {offset}"


def _normalise_entry(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Translate a Splunkbase API result into the catalog shape.

    Returns ``None`` if the upstream entry is unusable (missing id/name).
    The Splunkbase API shifted field names in mid-2026: the legacy
    ``appid`` field, which was a numeric id, was renamed to ``uid`` and
    ``appid`` was repurposed as the kebab-case string slug. ``title``
    became the display name (was ``displayName``); ``path`` became the
    canonical URL (was ``appurl``/``appUrl``/``url``); ``download_count``
    was already present but is now the only download stat. We accept
    both shapes so the function stays backward-compatible with the
    legacy 2024-era catalogs.
    """

    # New API: ``uid`` carries the numeric id; legacy: ``appid`` did.
    # Try numeric fields first so the new ``appid`` (string slug) does
    # not short-circuit the int cast.
    candidates = (raw.get("uid"), raw.get("id"), raw.get("appid"))
    app_id: Optional[int] = None
    for raw_value in candidates:
        if raw_value is None:
            continue
        try:
            candidate = int(raw_value)
        except (TypeError, ValueError):
            continue
        if candidate > 0:
            app_id = candidate
            break
    if app_id is None:
        return None

    appid_slug = raw.get("appid")
    if isinstance(appid_slug, int):
        appid_slug = None  # legacy shape; not the slug
    name = (
        raw.get("appName")
        or raw.get("appname")
        or raw.get("name")
        or appid_slug
        or ""
    )
    display_name = raw.get("title") or raw.get("displayName") or name or f"app {app_id}"
    description = (raw.get("description") or "").strip()

    latest = raw.get("latest") if isinstance(raw.get("latest"), dict) else {}
    latest_version = latest.get("name") or raw.get("latest_version") or None
    splunk_versions = latest.get("splunk_version_compatibility")
    if not isinstance(splunk_versions, list):
        splunk_versions = []
    splunk_versions = [str(v) for v in splunk_versions if isinstance(v, (str, int, float))]

    vendor = ""
    license_obj = raw.get("license")
    if isinstance(license_obj, dict):
        vendor = license_obj.get("vendor") or ""
    if not vendor:
        vendor = raw.get("vendor") or raw.get("created_by") or ""

    # New API exposes Cloud-deployability via ``install_method_distributed``:
    # values ``appmgmt_phase`` and ``self_service`` mean the app is
    # accepted for Splunk Cloud distributed deployments; ``rejected``
    # explicitly is not. Fall back to the legacy explicit boolean fields.
    install_dist = str(raw.get("install_method_distributed") or "").lower()
    cloud_vetted = bool(
        install_dist in ("appmgmt_phase", "self_service")
        or raw.get("is_supported_for_cloud")
        or raw.get("isCloudReady")
        or raw.get("cloudCompatible")
    )

    category_raw = raw.get("category") or raw.get("appCategory") or raw.get("type") or ""
    if isinstance(category_raw, list) and category_raw:
        category_raw = category_raw[0]
    if isinstance(category_raw, dict):
        category_raw = category_raw.get("name") or ""
    category = str(category_raw or "").lower() or "data-source"

    num_downloads_raw = raw.get("download_count") or raw.get("numDownloads")
    try:
        num_downloads = int(num_downloads_raw) if num_downloads_raw is not None else None
    except (TypeError, ValueError):
        num_downloads = None

    last_updated = (
        raw.get("updated_time")
        or raw.get("modified_at")
        or raw.get("modified")
        or raw.get("lastUpdated")
    )
    if isinstance(last_updated, str) and last_updated:
        last_updated = last_updated.split("T", 1)[0]
    elif not isinstance(last_updated, str):
        last_updated = None

    url = (
        raw.get("path")
        or raw.get("appurl")
        or raw.get("appUrl")
        or raw.get("url")
        or f"https://{ALLOWED_HOST}/app/{app_id}"
    )
    # ``path`` may carry a trailing slash (``/app/7633/``); the legacy
    # canonical form omits it. Normalise so diffs stay clean.
    if isinstance(url, str):
        url = url.rstrip("/")
    if not url.startswith(f"https://{ALLOWED_HOST}/app/"):
        url = f"https://{ALLOWED_HOST}/app/{app_id}"

    return {
        "id": app_id,
        "name": str(name).strip() or f"app-{app_id}",
        "displayName": str(display_name).strip(),
        "description": description,
        "url": url,
        "latestVersion": latest_version if isinstance(latest_version, str) else None,
        "vendor": str(vendor).strip(),
        "cloudVetted": cloud_vetted,
        "splunkVersionsSupported": splunk_versions,
        "category": category,
        "numDownloads": num_downloads,
        "lastUpdated": last_updated,
    }


def _extract_results(page: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Splunkbase REST has used both ``results`` and ``apps`` over time."""
    for key in ("results", "apps", "objects", "data"):
        value = page.get(key)
        if isinstance(value, list):
            return value
    return []


def _diff_entries(old: Optional[Dict[str, Any]], new: Dict[str, Any]) -> bool:
    """Return True iff the canonical body differs (so we should write)."""
    if not isinstance(old, dict):
        return True
    return tuple(old.get(f) for f in CANONICAL_FIELDS) != tuple(
        new.get(f) for f in CANONICAL_FIELDS
    )


# ---------------------------------------------------------------------------
# Drivers
# ---------------------------------------------------------------------------


def cmd_check() -> int:
    catalog = _read_json(CATALOG_PATH) or _empty_catalog()
    overrides = _read_json(OVERRIDES_PATH) or {"schemaVersion": 1, "apps": {}}

    base_errors = _validate_catalog(catalog)
    overrides_errors = _validate_catalog(_apply_overrides(catalog, overrides))

    errors = []
    errors.extend(f"catalog: {e}" for e in base_errors)
    for e in overrides_errors:
        if not any(e == ce.split("catalog: ", 1)[-1] for ce in errors):
            errors.append(f"catalog+overrides: {e}")

    if errors:
        for err in errors:
            print(f"[sync_splunkbase_catalog] {err}", file=sys.stderr)
        return 1

    print(
        f"[sync_splunkbase_catalog] catalog OK ({len(catalog.get('apps', {}))} entries; "
        f"{len((overrides.get('apps') or {}))} overrides)"
    )
    return 0


def cmd_sync(*, dry_run: bool = False) -> int:
    existing = _read_json(CATALOG_PATH) or _empty_catalog()
    if "apps" not in existing or not isinstance(existing["apps"], dict):
        existing = _empty_catalog()

    fetched: Dict[str, Dict[str, Any]] = {}
    for page_index in range(MAX_PAGES):
        offset = page_index * PAGE_SIZE
        page, err = _fetch_page(offset, PAGE_SIZE)
        if err is not None or page is None:
            print(
                f"[sync_splunkbase_catalog] sync aborted at offset {offset}: {err}; "
                "keeping existing catalog (cached fallback).",
                file=sys.stderr,
            )
            return 0
        results = _extract_results(page)
        if not results:
            break
        for raw in results:
            entry = _normalise_entry(raw)
            if entry is None:
                continue
            fetched[str(entry["id"])] = entry
        time.sleep(SLEEP_BETWEEN_REQUESTS)
    else:
        print(
            f"[sync_splunkbase_catalog] reached MAX_PAGES={MAX_PAGES} without an empty page; "
            "consider raising the cap.",
            file=sys.stderr,
        )

    if not fetched:
        print(
            "[sync_splunkbase_catalog] live API returned zero results; "
            "keeping existing catalog (cached fallback).",
            file=sys.stderr,
        )
        return 0

    new_apps: Dict[str, Dict[str, Any]] = {}
    changed = 0
    for key, entry in fetched.items():
        prior = existing.get("apps", {}).get(key)
        if _diff_entries(prior, entry):
            new_apps[key] = entry
            changed += 1
        else:
            new_apps[key] = prior

    body: Dict[str, Any] = json.loads(json.dumps(existing))
    body.setdefault(
        "$comment",
        "Curated Splunkbase app metadata. Refreshed by scripts/sync_splunkbase_catalog.py.",
    )
    body["schemaVersion"] = 1
    body["source"] = {
        "api": API_BASE,
        "syncScript": "scripts/sync_splunkbase_catalog.py",
        "overrides": "data/splunkbase-catalog-overrides.json",
    }
    body["apps"] = new_apps
    if changed > 0:
        body["lastUpdated"] = _today()

    errors = _validate_catalog(body)
    if errors:
        for err in errors:
            print(f"[sync_splunkbase_catalog] post-sync invalid: {err}", file=sys.stderr)
        print(
            "[sync_splunkbase_catalog] refusing to overwrite a valid catalog with invalid output; "
            "keeping existing cache.",
            file=sys.stderr,
        )
        return 0

    if dry_run:
        print(
            f"[sync_splunkbase_catalog] dry-run: {changed} entries would change "
            f"out of {len(new_apps)} fetched."
        )
        return 0

    _write_json(CATALOG_PATH, body)
    print(
        f"[sync_splunkbase_catalog] wrote {CATALOG_PATH.relative_to(REPO_ROOT)} "
        f"({len(new_apps)} apps; {changed} changed)."
    )
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sync data/splunkbase-catalog.json from the public Splunkbase REST API.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="Hermetic. Validate the existing catalog (default).",
    )
    mode.add_argument(
        "--sync",
        action="store_true",
        help="Network-enabled. Refresh the catalog from splunkbase.splunk.com.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --sync, print the change count but do not write the file.",
    )
    args = parser.parse_args(argv)

    if args.sync:
        return cmd_sync(dry_run=args.dry_run)
    return cmd_check()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as err:  # pragma: no cover - last-resort fallback
        print(f"[sync_splunkbase_catalog] internal error: {err}", file=sys.stderr)
        raise SystemExit(2) from err
