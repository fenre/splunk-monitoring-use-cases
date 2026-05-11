"""Decompose PASS_NODATA results into NO_INPUT vs HIDDEN_HALLUCINATION.

For every PASS_NODATA UC in /tmp/meraki-sweep-report.json:

  1. Look up live event count for each sourcetype the SPL uses
     (via /tmp/meraki-st-counts.json — produced by the data-presence probe).
  2. Categorize:
       * If EVERY referenced sourcetype has count=0 -> NO_INPUT
         (the SPL is untestable here; conclusion deferred).
       * If ANY referenced sourcetype has count>0  -> POTENTIAL_BUG
         (the data is there but the SPL filtered it all out).
  3. For POTENTIAL_BUG cases, run a "leading-search" probe: take only the
     first search command (everything before the first `|`) and run it.
     If THAT returns rows, the bug is downstream (stats/where/eval). If
     even the leading search returns zero, the search filter itself is
     hallucinated (wrong field, wrong value, wrong sourcetype combo).

Writes /tmp/meraki-triage-report.json with the refined categorization
plus a markdown summary at /tmp/meraki-triage-report.md.

Usage:
    set -a; source secrets.env; set +a
    python3 scripts/_meraki_triage.py
"""

from __future__ import annotations

import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SWEEP_REPORT = Path("/tmp/meraki-sweep-report.json")
ST_COUNTS = Path("/tmp/meraki-st-counts.json")
TEST_PLAN = Path("/tmp/meraki-test-plan.jsonl")
OUT_JSON = Path("/tmp/meraki-triage-report.json")
OUT_MD = Path("/tmp/meraki-triage-report.md")
SEARCH_HEAD = os.getenv("SPLUNK_REST_HOST", "192.168.12.45")
SEARCH_PORT = int(os.getenv("SPLUNK_REST_PORT", "8089"))


def _ctx() -> ssl.SSLContext:
    c = ssl.create_default_context()
    c.check_hostname = False
    c.verify_mode = ssl.CERT_NONE
    return c


def run(spl: str, token: str, earliest: str = "-24h",
        timeout: int = 60) -> tuple[str, str, int]:
    """Return (category, detail, row_count)."""
    body = urllib.parse.urlencode({
        "search": spl, "exec_mode": "oneshot",
        "earliest_time": earliest, "latest_time": "now",
        "output_mode": "json", "count": 1, "max_count": 1,
    }).encode("ascii")
    req = urllib.request.Request(
        f"https://{SEARCH_HEAD}:{SEARCH_PORT}/services/search/jobs",
        data=body, method="POST",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, context=_ctx(), timeout=timeout + 5) as r:
            d = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            d = json.loads(e.read().decode())
        except Exception:
            return "FATAL", f"HTTP {e.code}", 0
    msgs = d.get("messages", [])
    fatals = [m.get("text", "") for m in msgs if m.get("type", "").upper() in ("FATAL", "ERROR")]
    if fatals:
        return "PARSE_ERROR", "; ".join(fatals)[:300], 0
    rows = d.get("results", [])
    return ("PASS_DATA" if rows else "PASS_NODATA"), f"{len(rows)} row(s)", len(rows)


def leading_search(spl: str) -> str:
    """Return the SPL up to but not including the first `|` (excluding `||`)."""
    s = spl.lstrip()
    if s.startswith("|"):
        # Already starts with a generating command (e.g. tstats); return up
        # to the next `|`.
        rest = s[1:]
        end = rest.find("|")
        return s if end < 0 else "|" + rest[:end]
    # Normal `search ...` form: trim at first pipe.
    end = s.find("|")
    if end < 0:
        return s
    head = s[:end].rstrip()
    if not head.startswith(("search ", "search\t")):
        head = "search " + head
    return head


def main() -> int:
    token = os.environ.get("SPLUNK_REST_TOKEN")
    if not token:
        print("error: source secrets.env first", file=sys.stderr)
        return 2

    sweep = json.load(open(SWEEP_REPORT))
    st_counts = json.load(open(ST_COUNTS))
    plan = {json.loads(l)["uc_id"]: json.loads(l)
            for l in TEST_PLAN.read_text().splitlines()
            if l.strip().startswith("{")}

    pass_nodata = [r for r in sweep["results"] if r["category"] == "PASS_NODATA"]
    print(f"Triaging {len(pass_nodata)} PASS_NODATA UCs...", file=sys.stderr)

    sys.path.insert(0, str(ROOT / "scripts"))
    from _meraki_sweep import normalize_spl  # type: ignore

    refined = []
    for n, r in enumerate(pass_nodata, 1):
        spl = plan[r["uc_id"]]["spl"]
        norm = normalize_spl(spl)
        head_spl = leading_search(norm)

        # Identify the PRIMARY sourcetype (the one in the leading search,
        # not in append/join subsearches). If we can't extract it from the
        # leading search, fall back to the first listed sourcetype.
        m = re.search(r'sourcetype\s*=\s*"?([\w:.-]+)"?', head_spl, re.I)
        primary_st = m.group(1).lower() if m else (r["sourcetypes"][0] if r["sourcetypes"] else "")
        primary_count = st_counts.get(primary_st, 0)

        per_st = [(st, st_counts.get(st, 0)) for st in r["sourcetypes"]]

        if primary_count == 0:
            # Leading search targets a sourcetype with no data. The SPL is
            # untestable from this lab regardless of what other sourcetypes
            # are referenced in subsearches.
            refined.append({
                **r, "refined_category": "NO_INPUT",
                "primary_sourcetype": primary_st,
                "primary_24h_count": primary_count,
                "per_sourcetype_24h": dict(per_st),
                "leading_probe": (f"primary sourcetype `{primary_st}` has 0 "
                                   "events in the last 24h on this Splunk"),
            })
            print(f"  [{n:>3d}/{len(pass_nodata)}] UC-{r['uc_id']:<10s} "
                   f"NO_INPUT  (primary={primary_st})", file=sys.stderr)
            continue

        # Primary sourcetype has data. Run the leading search.
        cat, detail, count = run(head_spl, token)

        if cat == "PARSE_ERROR":
            verdict = "LEADING_PARSE_ERROR"
            note = f"leading search itself fails to parse: {detail}"
        elif cat == "PASS_DATA":
            verdict = "DOWNSTREAM_FILTER_BUG"
            note = (f"leading search returns {count} row(s); the issue is "
                    "in stats/where/eval/rename downstream — likely a fake "
                    "field referenced after the search.")
        else:
            verdict = "SEARCH_FILTER_FAIL"
            note = ("leading search returns 0 rows even though primary "
                    f"sourcetype `{primary_st}` has {primary_count} events. "
                    "The search-time filter (type=, signature=, field=value) "
                    "either is hallucinated OR the test data legitimately "
                    "lacks matching values. Manual inspection required.")

        refined.append({
            **r, "refined_category": verdict,
            "primary_sourcetype": primary_st,
            "primary_24h_count": primary_count,
            "per_sourcetype_24h": dict(per_st),
            "leading_search": head_spl,
            "leading_probe": note,
        })
        print(f"  [{n:>3d}/{len(pass_nodata)}] UC-{r['uc_id']:<10s} {verdict}",
              file=sys.stderr)

    summary = {
        "input_pass_nodata": len(pass_nodata),
        "no_input": sum(1 for x in refined if x["refined_category"] == "NO_INPUT"),
        "search_filter_fail": sum(1 for x in refined if x["refined_category"] == "SEARCH_FILTER_FAIL"),
        "downstream_filter_bug": sum(1 for x in refined if x["refined_category"] == "DOWNSTREAM_FILTER_BUG"),
        "leading_parse_error": sum(1 for x in refined if x["refined_category"] == "LEADING_PARSE_ERROR"),
    }
    OUT_JSON.write_text(json.dumps({"summary": summary, "results": refined}, indent=2))

    # Markdown report
    lines = [
        "# Meraki UC live-fire triage",
        "",
        f"Decomposes {len(pass_nodata)} `PASS_NODATA` results from "
        f"`reports/meraki-sweep-report.json`.",
        "",
        "## Summary",
        "",
        f"* `NO_INPUT` (primary sourcetype not ingested in this Splunk): "
        f"**{summary['no_input']}**",
        f"* `SEARCH_FILTER_FAIL` (primary sourcetype has data, leading search "
        f"returns 0 rows — possible hallucination OR legit no-match): "
        f"**{summary['search_filter_fail']}**",
        f"* `DOWNSTREAM_FILTER_BUG` (leading search returned rows, downstream "
        f"stage zeroed): **{summary['downstream_filter_bug']}**",
        f"* `LEADING_PARSE_ERROR` (leading search itself failed): "
        f"**{summary['leading_parse_error']}**",
        "",
    ]
    for cat in ("DOWNSTREAM_FILTER_BUG", "LEADING_PARSE_ERROR", "SEARCH_FILTER_FAIL"):
        rows = [x for x in refined if x["refined_category"] == cat]
        if not rows:
            continue
        lines.append(f"## {cat}")
        lines.append("")
        for x in rows:
            lines.append(f"### UC-{x['uc_id']} — {x['title']}")
            lines.append("")
            lines.append(f"**Sourcetypes (24h counts):** "
                          f"{x['per_sourcetype_24h']}")
            lines.append("")
            lines.append(f"**Triage:** {x['leading_probe']}")
            lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"\nWrote {OUT_JSON} and {OUT_MD}", file=sys.stderr)
    print(f"\n=== TRIAGE SUMMARY ===", file=sys.stderr)
    for k, v in summary.items():
        print(f"  {k:<22s} {v}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
