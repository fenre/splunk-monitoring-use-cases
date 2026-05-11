#!/usr/bin/env python3
"""For every dead UC reference URL, walk up the path until we find an
ancestor URL that returns 2xx/3xx, and record it as the verified
fallback. Outputs data/uc-link-fallbacks.json mapping dead → fallback.

This is the foundation for `scripts/fix_dead_uc_urls.py` which applies
the mapping to the corpus.
"""
from __future__ import annotations

import argparse
import json
import ssl
import time
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse, urlunparse

REPO = Path(__file__).resolve().parent.parent
STATUS = REPO / "data" / "uc-link-status.json"
OUT = REPO / "data" / "uc-link-fallbacks.json"

CTX = ssl.create_default_context()


def probe(url: str) -> int | None:
    """Return HTTP status code or None on error."""
    try:
        req = urllib.request.Request(
            url,
            method="HEAD",
            headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"},
        )
        try:
            with urllib.request.urlopen(req, timeout=8, context=CTX) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if e.code in (400, 403, 405, 501):
                req2 = urllib.request.Request(
                    url,
                    method="GET",
                    headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"},
                )
                try:
                    with urllib.request.urlopen(req2, timeout=10, context=CTX) as r2:
                        return r2.status
                except urllib.error.HTTPError as e2:
                    return e2.code
                except Exception:
                    return None
            return e.code
        except Exception:
            return None
    except Exception:
        return None


def candidate_ancestors(url: str) -> list[str]:
    """Generate ancestor URLs by stripping path segments and trailing
    sections like fragments/queries. Return ordered from most-specific
    ancestor to host root."""
    p = urlparse(url)
    segs = [s for s in p.path.split("/") if s]
    out: list[str] = []
    # remove file with extension, then walk up segs
    if segs and ("." in segs[-1] or len(segs[-1]) <= 64):
        # remove last segment
        for i in range(len(segs) - 1, -1, -1):
            new_path = "/" + "/".join(segs[: i + 1])
            out.append(urlunparse((p.scheme, p.netloc, new_path, "", "", "")))
    # Host root
    out.append(urlunparse((p.scheme, p.netloc, "/", "", "", "")))
    # de-dupe preserving order
    seen = set()
    uniq = []
    for u in out:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


# Curated host fallbacks: if path truncation finds nothing, use this
# verified product landing page instead of bare host root.
HOST_FALLBACKS = {
    "docs.splunk.com": "https://docs.splunk.com/Documentation",
    "www.cisco.com": "https://www.cisco.com/c/en/us/support/index.html",
    "developer.cisco.com": "https://developer.cisco.com/",
    "docs.citrix.com": "https://docs.citrix.com/",
    "learn.microsoft.com": "https://learn.microsoft.com/en-us/",
    "lantern.splunk.com": "https://lantern.splunk.com/",
    "techdocs.broadcom.com": "https://techdocs.broadcom.com/",
    "docs.fluentd.org": "https://docs.fluentd.org/",
    "www.juniper.net": "https://www.juniper.net/documentation/",
    "docs.openstack.org": "https://docs.openstack.org/",
    "docs.thousandeyes.com": "https://docs.thousandeyes.com/",
    "grafana.com": "https://grafana.com/docs/",
    "cloud.google.com": "https://cloud.google.com/docs",
    "ico.org.uk": "https://ico.org.uk/",
    "www.php.net": "https://www.php.net/docs.php",
    "attackerkb.com": "https://attackerkb.com/",
    "csrc.nist.gov": "https://csrc.nist.gov/publications",
    "www.edpb.europa.eu": "https://www.edpb.europa.eu/edpb_en",
    "cassandra.apache.org": "https://cassandra.apache.org/doc/latest/",
    "kubernetes.io": "https://kubernetes.io/docs/",
    "goharbor.io": "https://goharbor.io/docs/",
    "support.google.com": "https://support.google.com/",
    "wiki.asterisk.org": "https://docs.asterisk.org/",
    "www.ovirt.org": "https://www.ovirt.org/documentation/",
    "en.wikipedia.org": "https://www.wikipedia.org/",
    "knowledge.broadcom.com": "https://knowledge.broadcom.com/",
    "www.cncf.io": "https://www.cncf.io/",
    "www.dell.com": "https://www.dell.com/support/home/en-us",
    "www.eba.europa.eu": "https://www.eba.europa.eu/",
    "github.com": "https://github.com/",
    "docs.docker.com": "https://docs.docker.com/",
    "docs.openshift.com": "https://docs.openshift.com/container-platform/latest/welcome/index.html",
    "docs.aws.amazon.com": "https://docs.aws.amazon.com/",
    "opentelemetry.io": "https://opentelemetry.io/docs/",
}


def best_fallback(url: str) -> tuple[str | None, str | None]:
    """Probe ancestors and return (fallback_url, reason)."""
    host = urlparse(url).netloc.lower()
    for ancestor in candidate_ancestors(url):
        if ancestor == url:
            continue
        st = probe(ancestor)
        if st is not None and 200 <= st < 400:
            return ancestor, f"ancestor-{st}"
    curated = HOST_FALLBACKS.get(host)
    if curated:
        return curated, "curated-host-fallback"
    return f"https://{host}/", "host-root"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    status = json.loads(STATUS.read_text())
    dead = [
        u for u, info in status["urls"].items()
        if info["classification"] == "dead"
    ]
    if args.limit:
        dead = dead[: args.limit]

    print(f"Finding fallbacks for {len(dead)} dead URLs...")
    out: dict[str, dict] = {}
    t0 = time.time()
    done = 0

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(best_fallback, u): u for u in dead}
        for fut in as_completed(futs):
            u = futs[fut]
            try:
                fb, reason = fut.result()
            except Exception as e:
                fb, reason = None, f"err:{type(e).__name__}"
            out[u] = {"fallback": fb, "reason": reason}
            done += 1
            if done % 50 == 0 or done == len(dead):
                el = time.time() - t0
                print(f"  {done}/{len(dead)} ({done*100//len(dead)}%) elapsed={el:.0f}s")

    OUT.write_text(json.dumps({
        "_meta": {
            "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total": len(dead),
            "tool": "scripts/find_url_fallbacks.py",
        },
        "fallbacks": dict(sorted(out.items())),
    }, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
