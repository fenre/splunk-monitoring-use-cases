#!/usr/bin/env python3
"""Execute UC SPL against sample events and assert on results.

Workflow
========
For every ``samples/UC-<id>/`` directory that has a ``positive.log``:

1.  Load ``manifest.yaml`` and the UC's SPL from ``catalog.json``.
2.  Rewrite each raw event's timestamp to ``now - jitter`` so it falls in
    Splunk's default search window.
3.  HEC-ingest ``positive.log`` into the index + sourcetype from the
    manifest, using ``source = manifest.source``.
4.  HEC-ingest ``negative.log`` (if present) into the same index with a
    distinct ``source`` so the post-run delete is scoped.
5.  Poll ``services/search/jobs`` until the data is searchable.
6.  Run the UC's SPL (``q``) via ``services/search/jobs/export`` with the
    manifest's ``timerange``.
7.  Assert on ``expected.min_count``, ``expected.max_count`` and any
    ``expected.fields``. A positive assertion failure or a negative-log
    match counts as a test failure.
8.  Delete the ingested fixtures so the instance is reusable.

The script writes a JUnit XML report to ``test-results/uc-tests.xml`` so
GitHub Actions can surface per-test failures.

Inputs
------
Environment variables:
    SPLUNK_URL         e.g. https://splunk:8089 (default http://localhost:8089)
    SPLUNK_HEC_URL     e.g. https://splunk:8088
    SPLUNK_HEC_TOKEN   a pre-provisioned HEC token with allowed index
    SPLUNK_USER        defaults to "admin"
    SPLUNK_PASSWORD    required; used for REST + search API
    SPLUNK_VERIFY_TLS  "1" to verify TLS (default 0)

CLI flags:
    --uc UC-1.1.1      run only the given UC (repeatable)
    --filter pattern   only UCs whose directory matches glob pattern
    --dry-run          parse + plan only, do not touch Splunk
    --junit path       override default test-results/uc-tests.xml
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from samples_index import _load_yaml, scan_samples, _load_catalog_ids  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = REPO_ROOT / "samples"
CATALOG_PATH = REPO_ROOT / "catalog.json"
JUNIT_DEFAULT = REPO_ROOT / "test-results" / "uc-tests.xml"

# -------------------------------------------------------- timestamp rewriting
TS_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # ISO-8601 with optional trailing Z or offset
    (
        "iso",
        re.compile(
            r"\b(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\b"
        ),
    ),
    # RFC 3164 syslog (Apr 16 08:00:00)
    (
        "rfc3164",
        re.compile(
            r"\b([A-Z][a-z]{2} [ 0-9]\d \d{2}:\d{2}:\d{2})\b"
        ),
    ),
    # US-style Windows eventlog (04/16/2026 08:10:15 AM)
    (
        "win",
        re.compile(
            r"\b(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2} (?:AM|PM))\b"
        ),
    ),
    # Splunk splunkd (04-16-2026 08:00:02.123)
    (
        "splunkd",
        re.compile(
            r"\b(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}\.\d+ [+-]\d{4})\b"
        ),
    ),
]


def rewrite_timestamp(line: str, now: dt.datetime) -> str:
    """Replace the first recognised timestamp in *line* with *now*."""
    for kind, rx in TS_PATTERNS:
        m = rx.search(line)
        if not m:
            continue
        if kind == "iso":
            replacement = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        elif kind == "rfc3164":
            replacement = now.strftime("%b %d %H:%M:%S").replace(" 0", "  ")[:15]
        elif kind == "win":
            replacement = now.strftime("%m/%d/%Y %I:%M:%S %p")
        elif kind == "splunkd":
            replacement = now.strftime("%m-%d-%Y %H:%M:%S.") + f"{now.microsecond // 1000:03d} +0000"
        else:
            continue
        return line[: m.start()] + replacement + line[m.end() :]
    return line


def split_events(raw: str) -> list[str]:
    """Best-effort event splitter.

    For simplicity: blank-line separated blocks, else one event per line.
    """
    blocks = [b.strip() for b in re.split(r"\n\s*\n", raw.strip()) if b.strip()]
    if len(blocks) > 1:
        return blocks
    return [ln for ln in raw.splitlines() if ln.strip()]


# ------------------------------------------------------------------- Splunk client
class SplunkClient:
    """Tiny stdlib-only client for the subset of REST we need."""

    def __init__(self, mgmt_url: str, hec_url: str, hec_token: str,
                 user: str, password: str, verify_tls: bool) -> None:
        self.mgmt_url = mgmt_url.rstrip("/")
        self.hec_url = hec_url.rstrip("/")
        self.hec_token = hec_token
        self.user = user
        self.password = password
        self.verify_tls = verify_tls
        self._session_key: str | None = None
        self._ctx = ssl.create_default_context()
        if not verify_tls:
            self._ctx.check_hostname = False
            self._ctx.verify_mode = ssl.CERT_NONE

    # ------- auth
    def _login(self) -> str:
        if self._session_key:
            return self._session_key
        data = urllib.parse.urlencode({
            "username": self.user,
            "password": self.password,
        }).encode()
        req = urllib.request.Request(
            f"{self.mgmt_url}/services/auth/login?output_mode=json",
            data=data,
            method="POST",
        )
        with urllib.request.urlopen(req, context=self._ctx, timeout=30) as resp:
            body = json.loads(resp.read().decode())
        self._session_key = body["sessionKey"]
        return self._session_key

    def _mgmt_get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        key = self._login()
        qs = urllib.parse.urlencode(params or {})
        url = f"{self.mgmt_url}{path}?output_mode=json" + (f"&{qs}" if qs else "")
        req = urllib.request.Request(url, headers={"Authorization": f"Splunk {key}"})
        with urllib.request.urlopen(req, context=self._ctx, timeout=60) as resp:
            return json.loads(resp.read().decode())

    # ------- search
    def run_oneshot(self, spl: str, earliest: str, latest: str = "now") -> list[dict[str, Any]]:
        key = self._login()
        data = urllib.parse.urlencode({
            "search": "search " + spl if not spl.lstrip().startswith(("|", "search")) else spl,
            "earliest_time": earliest,
            "latest_time": latest,
            "output_mode": "json",
            "exec_mode": "oneshot",
        }).encode()
        req = urllib.request.Request(
            f"{self.mgmt_url}/services/search/jobs",
            data=data,
            headers={"Authorization": f"Splunk {key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, context=self._ctx, timeout=120) as resp:
            body = json.loads(resp.read().decode())
        return list(body.get("results", []))

    # ------- HEC raw ingest
    def hec_post_event(self, event: str, index: str, sourcetype: str,
                       source: str | None, host: str | None) -> None:
        payload = {
            "event": event,
            "sourcetype": sourcetype,
            "index": index,
        }
        if source:
            payload["source"] = source
        if host:
            payload["host"] = host
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.hec_url}/services/collector/event",
            data=data,
            headers={
                "Authorization": f"Splunk {self.hec_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, context=self._ctx, timeout=30) as resp:
            resp.read()

    def delete_ingested(self, source_tag: str, index: str) -> None:
        self.run_oneshot(
            f'index={index} source="{source_tag}" | delete',
            earliest="-1d",
            latest="+1h",
        )


# ------------------------------------------------------------------- test runner
@dataclass
class TestResult:
    uc_id: str
    passed: bool
    duration_s: float
    message: str = ""
    stdout: str = ""
    failures: list[str] = field(default_factory=list)


def _get_uc_spl(uc_id: str) -> str | None:
    with CATALOG_PATH.open("r", encoding="utf-8") as fh:
        cat = json.load(fh)
    for c in cat.get("DATA", []):
        for sc in c.get("s", []):
            for uc in sc.get("u", []):
                if uc.get("i") == uc_id:
                    return uc.get("q") or uc.get("qs") or ""
    return None


def _assert_expected(results: list[dict[str, Any]], manifest: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = manifest.get("expected") or {}
    min_count = int(expected.get("min_count") or 0)
    max_count = expected.get("max_count")
    n = len(results)
    if n < min_count:
        failures.append(f"expected min_count={min_count}, got {n}")
    if max_count is not None and n > int(max_count):
        failures.append(f"expected max_count={max_count}, got {n}")
    for field_spec in expected.get("fields") or []:
        name = field_spec.get("name")
        if not name:
            continue
        values_seen = [r.get(name) for r in results]
        if "values" in field_spec:
            want = set(str(v) for v in field_spec["values"])
            got = set(str(v) for v in values_seen if v is not None)
            if not (want & got):
                failures.append(f"field {name}: expected one of {sorted(want)}, saw {sorted(got)[:5]}")
        if "min" in field_spec or "max" in field_spec:
            numeric = []
            for v in values_seen:
                try:
                    numeric.append(float(v))
                except (TypeError, ValueError):
                    continue
            if not numeric:
                failures.append(f"field {name}: no numeric values in {n} results")
                continue
            if "min" in field_spec and min(numeric) < float(field_spec["min"]):
                failures.append(f"field {name}: min={min(numeric)} < expected.min={field_spec['min']}")
            if "max" in field_spec and max(numeric) > float(field_spec["max"]):
                failures.append(f"field {name}: max={max(numeric)} > expected.max={field_spec['max']}")
        if "regex" in field_spec:
            pat = re.compile(field_spec["regex"])
            if not any(pat.search(str(v)) for v in values_seen if v is not None):
                failures.append(f"field {name}: no value matched regex {field_spec['regex']}")
    return failures


def run_uc_test(client: SplunkClient, uc_id: str, sample_dir: Path, dry_run: bool) -> TestResult:
    started = time.time()
    manifest_path = sample_dir / "manifest.yaml"
    manifest = _load_yaml(manifest_path)
    spl = _get_uc_spl(uc_id)
    if not spl:
        return TestResult(uc_id, False, 0, message=f"UC-{uc_id} not found in catalog.json")

    pos_path = sample_dir / "positive.log"
    neg_path = sample_dir / "negative.log"
    if not pos_path.exists():
        return TestResult(uc_id, False, 0, message="positive.log missing")

    index = manifest["index"]
    sourcetype = manifest["sourcetype"]
    source = manifest.get("source") or f"uc-tests/{uc_id}/positive"
    host = manifest.get("host")
    timerange = manifest.get("timerange") or "-24h"

    if dry_run:
        return TestResult(uc_id, True, 0, message=f"(dry-run) would run SPL against index={index} sourcetype={sourcetype}")

    now = dt.datetime.now(dt.timezone.utc)
    positive_events = [rewrite_timestamp(ev, now) for ev in split_events(pos_path.read_text("utf-8"))]
    for ev in positive_events:
        client.hec_post_event(ev, index, sourcetype, source, host)

    if neg_path.exists() and neg_path.stat().st_size > 0:
        neg_source = f"uc-tests/{uc_id}/negative"
        negative_events = [rewrite_timestamp(ev, now) for ev in split_events(neg_path.read_text("utf-8"))]
        for ev in negative_events:
            client.hec_post_event(ev, index, sourcetype, neg_source, host)

    # Wait for indexing to complete.
    deadline = time.time() + 60
    while time.time() < deadline:
        probe = client.run_oneshot(
            f'index={index} source="{source}" | stats count as n',
            earliest="-5m",
        )
        if probe and int(probe[0].get("n", 0)) >= len(positive_events):
            break
        time.sleep(2)

    results = client.run_oneshot(spl, earliest=timerange)
    failures = _assert_expected(results, manifest)
    passed = not failures
    duration = time.time() - started
    return TestResult(
        uc_id=uc_id,
        passed=passed,
        duration_s=duration,
        stdout=json.dumps(results[:10], indent=2),
        failures=failures,
    )


# ------------------------------------------------------------------- junit
def write_junit(path: Path, results: list[TestResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element("testsuites")
    suite = ET.SubElement(
        root,
        "testsuite",
        name="uc-tests",
        tests=str(len(results)),
        failures=str(sum(1 for r in results if not r.passed)),
        time=f"{sum(r.duration_s for r in results):.2f}",
    )
    for r in results:
        tc = ET.SubElement(suite, "testcase",
                           classname="splunk-monitoring-use-cases",
                           name=f"UC-{r.uc_id}",
                           time=f"{r.duration_s:.2f}")
        if not r.passed:
            msg = "; ".join(r.failures) or r.message or "test failed"
            f = ET.SubElement(tc, "failure", message=msg, type="AssertionError")
            f.text = r.stdout
    tree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)


# ------------------------------------------------------------------- cli
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uc", action="append", help="Limit to specific UC id (repeatable).")
    parser.add_argument("--filter", default=None, help="Glob on UC directory names.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--junit", default=str(JUNIT_DEFAULT))
    args = parser.parse_args()

    if not CATALOG_PATH.exists():
        print("catalog.json missing — run build.py first.", file=sys.stderr)
        return 2

    statuses = scan_samples(_load_catalog_ids())
    eligible = [s for s in statuses if s.has_positive and not s.errors]
    if args.uc:
        wanted = {u.lstrip("UC-") for u in args.uc}
        eligible = [s for s in eligible if s.uc_id in wanted]
    if args.filter:
        import fnmatch
        eligible = [s for s in eligible if fnmatch.fnmatch(f"UC-{s.uc_id}", args.filter)]

    if not eligible:
        print("No sample fixtures eligible to run.", file=sys.stderr)
        return 0

    client: SplunkClient | None = None
    if not args.dry_run:
        mgmt = os.environ.get("SPLUNK_URL", "https://localhost:8089")
        hec = os.environ.get("SPLUNK_HEC_URL", "https://localhost:8088")
        tok = os.environ.get("SPLUNK_HEC_TOKEN")
        user = os.environ.get("SPLUNK_USER", "admin")
        pwd = os.environ.get("SPLUNK_PASSWORD")
        if not tok or not pwd:
            print("SPLUNK_HEC_TOKEN and SPLUNK_PASSWORD must be set (or pass --dry-run).", file=sys.stderr)
            return 2
        verify = os.environ.get("SPLUNK_VERIFY_TLS", "0") == "1"
        client = SplunkClient(mgmt, hec, tok, user, pwd, verify)

    results: list[TestResult] = []
    for s in eligible:
        sample_dir = SAMPLES_DIR / f"UC-{s.uc_id}"
        print(f"-> UC-{s.uc_id}", flush=True)
        if client is None:
            r = run_uc_test(None, s.uc_id, sample_dir, dry_run=True)  # type: ignore[arg-type]
        else:
            try:
                r = run_uc_test(client, s.uc_id, sample_dir, dry_run=False)
            except Exception as exc:  # noqa: BLE001
                r = TestResult(s.uc_id, False, 0, message=f"runner error: {exc}")
        results.append(r)
        status = "OK" if r.passed else "FAIL"
        tail = " — " + (r.message or "; ".join(r.failures)) if not r.passed else ""
        print(f"   [{status}] {r.duration_s:.1f}s{tail}")

    write_junit(Path(args.junit), results)
    print(f"\nJUnit XML: {args.junit}")
    passed = sum(1 for r in results if r.passed)
    print(f"Summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
