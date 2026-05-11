#!/usr/bin/env python3
"""Probe every reference URL in content/cat-*/UC-*.json and emit
data/uc-link-status.json with classification (ok / redirect / 404 / err).

Parallel via threading; rate-limited per host.
"""
from __future__ import annotations

import argparse
import json
import ssl
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"
OUT = REPO / "data" / "uc-link-status.json"

CTX = ssl.create_default_context()


def collect_urls() -> dict[str, list[str]]:
    urls: dict[str, set[str]] = defaultdict(set)
    for p in sorted(CONTENT.glob("cat-*/UC-*.json")):
        try:
            d = json.load(p.open())
        except Exception:
            continue
        for ref in d.get("references", []) or []:
            if isinstance(ref, dict):
                u = ref.get("url")
                if isinstance(u, str) and u.startswith(("http://", "https://")):
                    u = u.strip()
                    while u and u[-1] in '.,;\\':
                        u = u[:-1]
                    urls[u].add(p.name)
    return {u: sorted(v) for u, v in urls.items()}


def probe(url: str) -> tuple[int | str, str | None]:
    """Return (status, final_url) for the URL."""
    try:
        req = urllib.request.Request(
            url,
            method="HEAD",
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; UC-link-probe/1.0)",
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10, context=CTX) as r:
                return r.status, r.geturl()
        except urllib.error.HTTPError as e:
            if e.code in (400, 403, 405, 501):
                req2 = urllib.request.Request(
                    url,
                    method="GET",
                    headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"},
                )
                try:
                    with urllib.request.urlopen(req2, timeout=15, context=CTX) as r2:
                        return r2.status, r2.geturl()
                except urllib.error.HTTPError as e2:
                    return e2.code, None
                except Exception as e2:
                    return f"err:{type(e2).__name__}", None
            return e.code, None
        except urllib.error.URLError as e:
            return f"err:URLError:{e.reason.__class__.__name__}", None
    except Exception as e:
        return f"err:{type(e).__name__}", None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--limit", type=int, default=0,
                        help="If >0, only probe this many URLs")
    parser.add_argument("--rps", type=float, default=0.2,
                        help="Min delay between requests to the same host (s)")
    args = parser.parse_args()

    urls = collect_urls()
    items = sorted(urls.items())
    if args.limit:
        items = items[: args.limit]
    total = len(items)
    print(f"Probing {total} URLs with {args.workers} workers...", file=sys.stderr)

    # Per-host rate limiting via dict of last-call timestamps
    host_last: dict[str, float] = {}
    host_lock = defaultdict(float)
    import threading
    host_mutex = threading.Lock()

    def throttle(host: str):
        with host_mutex:
            now = time.time()
            last = host_last.get(host, 0)
            wait = max(0, args.rps - (now - last))
            host_last[host] = now + wait
        if wait > 0:
            time.sleep(wait)

    results: dict[str, dict] = {}
    done = 0
    t0 = time.time()

    def task(url: str, files: list[str]):
        host = urlparse(url).netloc.lower()
        throttle(host)
        status, final = probe(url)
        return url, host, files, status, final

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(task, u, f) for u, f in items]
        for fut in as_completed(futs):
            url, host, files, status, final = fut.result()
            cls = classify(status)
            results[url] = {
                "url": url,
                "host": host,
                "sources": files,
                "status": status if isinstance(status, int) else None,
                "status_raw": status,
                "classification": cls,
                "final_url": final,
            }
            done += 1
            if done % 100 == 0 or done == total:
                elapsed = time.time() - t0
                rate = done / max(elapsed, 0.001)
                eta = (total - done) / max(rate, 0.001)
                print(
                    f"  {done}/{total} ({done * 100 // total}%) "
                    f"elapsed={elapsed:.0f}s eta={eta:.0f}s",
                    file=sys.stderr,
                )

    summary = defaultdict(int)
    for r in results.values():
        summary[r["classification"]] += 1
    summary = dict(summary)

    out = {
        "_meta": {
            "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "elapsedSeconds": round(time.time() - t0, 1),
            "totalChecked": total,
            "summary": summary,
            "tool": "scripts/probe_all_uc_urls.py",
        },
        "urls": dict(sorted(results.items())),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nDone. {summary}", file=sys.stderr)
    print(f"Wrote {OUT.relative_to(REPO)}", file=sys.stderr)
    return 0


def classify(status) -> str:
    if isinstance(status, int):
        if 200 <= status < 300:
            return "ok"
        if 300 <= status < 400:
            return "redirect"
        if status == 404 or status == 410:
            return "dead"
        if 400 <= status < 500:
            if status == 403:
                return "bot_blocked"
            if status == 429:
                return "rate_limited"
            return "client_error"
        if 500 <= status < 600:
            return "server_error"
    return "error"


if __name__ == "__main__":
    sys.exit(main())
