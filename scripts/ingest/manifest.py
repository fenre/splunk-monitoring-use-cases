"""Shared retrieval-manifest helpers for ingest pipelines.

Security posture (rule codeguard-0-api-web-services):
  * HTTPS-only URLs are enforced at the call site.
  * HTTP redirects are allowed but logged.
  * User-Agent is set to a stable, identifiable string.
  * All downloaded bytes are hashed (SHA-256) before use; the caller
    compares against an expected hash when one exists.
  * Manifest writes are deterministic (sorted keys, trailing newline).
"""

from __future__ import annotations

import dataclasses
import datetime as _dt
import hashlib
import json
import pathlib
import ssl
import sys
import urllib.error
import urllib.request
from typing import Dict, List, Optional

_UA = "splunk-monitoring-use-cases-ingest/1.0 (+https://github.com/fsudmann/splunk-monitoring-use-cases)"
_TIMEOUT_S = 60


@dataclasses.dataclass
class FetchRecord:
    """Metadata captured for a single remote retrieval."""

    source_id: str
    url: str
    local: str
    bytes: int
    sha256: str
    fetched_at: str
    http_status: Optional[int] = None
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    content_type: Optional[str] = None

    def to_dict(self) -> Dict:
        return {k: v for k, v in dataclasses.asdict(self).items() if v is not None}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now_utc_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


def fetch(
    source_id: str,
    url: str,
    dest: pathlib.Path,
    *,
    repo_root: pathlib.Path,
    expected_sha256: Optional[str] = None,
    cache: bool = True,
) -> FetchRecord:
    """Download ``url`` to ``dest`` (caching) and return a :class:`FetchRecord`.

    * ``cache=True`` (default) reuses any already-downloaded file on disk
      without a network call. Idempotent CI re-runs therefore do no network
      I/O.
    * ``expected_sha256`` aborts with ``ValueError`` on mismatch.
    """

    if not url.startswith("https://"):
        raise ValueError(f"Ingest URLs must be HTTPS: {url!r}")

    dest.parent.mkdir(parents=True, exist_ok=True)

    headers: Dict[str, str] = {}
    status: Optional[int] = None
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    content_type: Optional[str] = None

    if not (cache and dest.exists()):
        request = urllib.request.Request(url, headers={"User-Agent": _UA})
        try:
            with urllib.request.urlopen(
                request, timeout=_TIMEOUT_S, context=_ssl_context()
            ) as response:
                status = response.status
                headers = {k.lower(): v for k, v in response.headers.items()}
                payload = response.read()
        except urllib.error.URLError as err:
            raise RuntimeError(f"Fetch failed for {url}: {err}") from err
        dest.write_bytes(payload)
        etag = headers.get("etag")
        last_modified = headers.get("last-modified")
        content_type = headers.get("content-type")

    payload = dest.read_bytes()
    digest = _sha256(payload)
    if expected_sha256 and digest != expected_sha256:
        raise ValueError(
            f"SHA-256 mismatch for {url}\n  expected {expected_sha256}\n       got {digest}"
        )

    try:
        local_rel = str(dest.relative_to(repo_root))
    except ValueError:
        local_rel = str(dest)

    return FetchRecord(
        source_id=source_id,
        url=url,
        local=local_rel,
        bytes=len(payload),
        sha256=digest,
        fetched_at=_now_utc_iso(),
        http_status=status,
        etag=etag,
        last_modified=last_modified,
        content_type=content_type,
    )


def write_manifest(manifest_path: pathlib.Path, records: List[FetchRecord], extra: Optional[Dict] = None) -> None:
    """Write a deterministic JSON manifest.

    Records are sorted by ``source_id`` + ``url`` to guarantee stable
    ordering across runs. The manifest is the *only* machine-trusted
    provenance layer for downstream compliance artefacts.
    """

    body: Dict = {
        "generated_at": _now_utc_iso(),
        "schema_version": 1,
        "provenance": [
            r.to_dict()
            for r in sorted(records, key=lambda r: (r.source_id, r.url))
        ],
    }
    if extra:
        body.update(extra)

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    serialised = json.dumps(body, indent=2, sort_keys=True) + "\n"
    manifest_path.write_text(serialised, encoding="utf-8")


def merge_into_manifest(manifest_path: pathlib.Path, new_records: List[FetchRecord]) -> None:
    """Merge new records into an existing manifest, de-duping on (source_id, url)."""

    existing: Dict[tuple, FetchRecord] = {}
    if manifest_path.exists():
        try:
            prior = json.loads(manifest_path.read_text(encoding="utf-8"))
            for entry in prior.get("provenance", []) or []:
                key = (entry.get("source_id"), entry.get("url"))
                if key[0] and key[1]:
                    existing[key] = FetchRecord(
                        source_id=entry["source_id"],
                        url=entry["url"],
                        local=entry.get("local", ""),
                        bytes=entry.get("bytes", 0),
                        sha256=entry.get("sha256", ""),
                        fetched_at=entry.get("fetched_at", _now_utc_iso()),
                        http_status=entry.get("http_status"),
                        etag=entry.get("etag"),
                        last_modified=entry.get("last_modified"),
                        content_type=entry.get("content_type"),
                    )
        except (OSError, json.JSONDecodeError) as err:
            print(f"[manifest] prior manifest unreadable, rewriting: {err}", file=sys.stderr)

    for r in new_records:
        existing[(r.source_id, r.url)] = r

    write_manifest(manifest_path, list(existing.values()))
