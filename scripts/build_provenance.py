#!/usr/bin/env python3
"""Generate a per-UC provenance ledger from catalog.json.

For every use case the script extracts the URLs from the ``refs`` field,
classifies each URL into a source category, then derives a single
*primary origin* per UC using a deterministic priority ladder.

Origin categories (most to least authoritative):

1. ``splunk-official``   — docs.splunk.com, lantern.splunk.com, dev.splunk.com,
                           research.splunk.com, splunkbase.splunk.com
2. ``vendor-official``   — primary documentation portal of the product vendor
                           (Microsoft, Cisco, AWS, Palo Alto, Fortinet, …)
3. ``mitre-attack``      — attack.mitre.org (adversary TTPs)
4. ``nist-compliance``   — nist.gov, cisecurity.org, iso.org, pcisecuritystandards.org
5. ``threat-intel``      — vendor threat-research blogs + community TTP projects
                           (Mandiant, CrowdStrike, Talos, DFIR Report, LOLBAS, …)
6. ``splunk-blog``       — splunk.com/en_us/blog, splunk.com/blogs
7. ``community``         — github.com, medium.com, stackexchange.com, dev.to, personal blogs
8. ``contributor``       — authored for this repo; no external citation

Outputs
-------
- ``provenance.json``   — machine-readable ledger for dashboards / APIs
- ``docs/provenance-coverage.md`` — human-readable summary per category

The resulting JSON is consumed by the dashboard (``index.html``) to render
a small origin badge + tooltip on every UC card, making the source trail
visible at a glance.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "catalog.json"
PROVENANCE_PATH = REPO_ROOT / "provenance.json"
PROVENANCE_JS_PATH = REPO_ROOT / "provenance.js"
DOC_PATH = REPO_ROOT / "docs" / "provenance-coverage.md"

# Markdown-style `[text](url)` extractor.  Also accepts bare URLs.
_MD_LINK_RE = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)\)")
_BARE_URL_RE = re.compile(r"(?<!\])\bhttps?://[^\s,;\)\]\"']+")


@dataclass(frozen=True)
class HostRule:
    category: str
    hosts: tuple[str, ...]  # domain suffix match (no leading dot)
    label: str  # human-friendly label for reporting


# Ordered most → least authoritative. The **first** matching rule wins when
# classifying a URL; ties at UC level are broken by priority (lower index
# = higher priority).
HOST_RULES: list[HostRule] = [
    HostRule("splunk-official", (
        "docs.splunk.com", "lantern.splunk.com", "dev.splunk.com",
        "research.splunk.com", "splunkbase.splunk.com", "conf.splunk.com",
    ), "Splunk (official docs / Splunkbase)"),
    HostRule("vendor-official", (
        "learn.microsoft.com", "docs.microsoft.com", "www.microsoft.com",
        "microsoft.com", "msrc.microsoft.com", "techcommunity.microsoft.com",
        "azure.microsoft.com",
        "docs.cisco.com", "www.cisco.com", "cisco.com",
        "docs.aws.amazon.com", "aws.amazon.com",
        "docs.paloaltonetworks.com", "live.paloaltonetworks.com",
        "docs.fortinet.com", "kb.fortinet.com",
        "kubernetes.io",
        "cloud.google.com", "cloud.google", "support.google.com",
        "docs.oracle.com",
        "www.postgresql.org", "dev.mysql.com", "www.mongodb.com",
        "nvidia.com", "docs.nvidia.com",
        "www.ibm.com",
        "www.vmware.com", "docs.vmware.com",
        "www.checkpoint.com", "checkpoint.com", "supportcenter.checkpoint.com",
        "developer.okta.com", "help.okta.com",
        "docs.elastic.co",
        "techdocs.broadcom.com",
        "support.sophos.com", "docs.sophos.com",
        "help.sap.com",
        "docs.crowdstrike.com", "falcon.crowdstrike.com",
        "docs.pulsesecure.net",
        "www.juniper.net",
        "docs.arista.com",
        "docs.nginx.com", "nginx.com",
        "httpd.apache.org",
        "redhat.com", "access.redhat.com", "www.redhat.com",
        "docs.docker.com",
        "docs.python.org",
        "docs.github.com", "support.github.com",
        "docs.gitlab.com",
        "docs.zerofox.com", "docs.proofpoint.com",
        "docs.censys.com",
        "docs.snowflake.com",
        "www.fortinet.com",
        "help.zscaler.com",
    ), "Vendor (official product docs)"),
    HostRule("mitre-attack", (
        "attack.mitre.org", "cwe.mitre.org", "capec.mitre.org",
    ), "MITRE (ATT&CK / CWE / CAPEC)"),
    HostRule("nist-compliance", (
        "nist.gov", "csrc.nist.gov", "www.nist.gov",
        "www.cisecurity.org", "cisecurity.org",
        "www.iso.org", "iso.org",
        "www.pcisecuritystandards.org", "pcisecuritystandards.org",
        "owasp.org", "www.owasp.org",
        "cisa.gov", "us-cert.cisa.gov", "www.cisa.gov",
        "cert.gov.ua",  # Ukrainian CERT
        "www.enisa.europa.eu",
        "tools.ietf.org", "datatracker.ietf.org", "www.rfc-editor.org",
    ), "Standards (NIST / CIS / ISO / PCI / OWASP / CERTs / IETF)"),
    HostRule("threat-intel", (
        # Vendor threat-research blogs
        "thedfirreport.com",
        "www.mandiant.com", "mandiant.com",
        "blog.talosintelligence.com", "talosintelligence.com",
        "unit42.paloaltonetworks.com",
        "redcanary.com", "www.redcanary.com",
        "www.trendmicro.com",
        "www.crowdstrike.com",
        "news.sophos.com",
        "www.welivesecurity.com",  # ESET
        "www.trustwave.com",
        "www.rapid7.com", "blog.rapid7.com",
        "www.bleepingcomputer.com",
        "blog.palantir.com",
        "www.sentinelone.com", "labs.sentinelone.com",
        "www.securonix.com",
        "www.kaspersky.com", "securelist.com",
        "www.huntress.com",
        "www.virustotal.com",
        "www.malwarebytes.com", "blog.malwarebytes.com",
        "www.varonis.com",
        "www.joesandbox.com",
        "www.cybereason.com",
        "www.truesec.com",
        "www.blackhillsinfosec.com",
        "rhinosecuritylabs.com",
        "labs.watchtowr.com",
        "isc.sans.edu", "www.sans.org",
        "book.hacktricks.xyz", "hacktricks.xyz",
        "media.defense.gov",  # NSA/CISA joint advisories
        "www.hackingarticles.in",
        "specterops.io",
        # Community TTP / tradecraft projects
        "lolbas-project.github.io",
        "gtfobins.github.io",
        "strontic.github.io",
        "adsecurity.org",
        "posts.specterops.io",
        "www.ired.team", "ired.team",
        "powersploit.readthedocs.io",
        "pentestlab.blog",
        # Malware sandboxes / catalogues
        "app.any.run", "any.run",
        "malpedia.caad.fkie.fraunhofer.de",
        "bazaar.abuse.ch", "feodotracker.abuse.ch", "urlhaus.abuse.ch",
        # Social-media CTI
        "twitter.com", "x.com",
    ), "Threat intel (vendor research + community TTP projects)"),
    HostRule("splunk-blog", (
        "www.splunk.com", "splunk.com",
    ), "Splunk (blog / marketing)"),
    HostRule("community", (
        "github.com", "medium.com", "dev.to",
        "stackoverflow.com", "serverfault.com",
        "www.reddit.com",
        "en.wikipedia.org", "wikipedia.org",
        "web.archive.org",
        "www.googlecloudcommunity.com",
    ), "Community (blogs / repos / forums)"),
]

ORIGIN_PRIORITY = {
    "splunk-official": 10,
    "vendor-official": 9,
    "mitre-attack": 8,
    "nist-compliance": 7,
    "threat-intel": 6,
    "splunk-blog": 5,
    "community": 4,
    "unclassified": 3,
    "contributor": 1,
}

BADGE_LABEL = {
    "splunk-official": "Splunk official",
    "vendor-official": "Vendor official",
    "mitre-attack": "MITRE ATT&CK",
    "nist-compliance": "Standards",
    "threat-intel": "Threat intel",
    "splunk-blog": "Splunk blog",
    "community": "Community",
    "unclassified": "Other",
    "contributor": "Contributor",
}


def _classify_host(netloc: str) -> str:
    """Return the category for a given hostname, or ``unclassified``."""
    host = netloc.lower().lstrip(".")
    for rule in HOST_RULES:
        for suffix in rule.hosts:
            if host == suffix or host.endswith("." + suffix):
                return rule.category
    return "unclassified"


def _extract_urls(refs_raw: str) -> list[str]:
    if not refs_raw:
        return []
    urls: list[str] = []
    seen = set()
    for m in _MD_LINK_RE.finditer(refs_raw):
        url = m.group(1).strip().rstrip(".,;")
        if url and url not in seen:
            seen.add(url)
            urls.append(url)
    # Also catch bare URLs outside markdown link syntax.
    for m in _BARE_URL_RE.finditer(refs_raw):
        url = m.group(0).strip().rstrip(".,;")
        if url and url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def _primary_origin(url_categories: list[str]) -> str:
    if not url_categories:
        return "contributor"
    ranked = sorted(set(url_categories), key=lambda c: -ORIGIN_PRIORITY.get(c, 0))
    return ranked[0]


def build_ledger() -> dict:
    if not CATALOG_PATH.exists():
        print("catalog.json missing — run build.py first.", file=sys.stderr)
        sys.exit(2)

    with CATALOG_PATH.open("r", encoding="utf-8") as fh:
        cat = json.load(fh)

    entries: dict[str, dict] = {}
    origin_counts: Counter[str] = Counter()
    per_category: dict[str, Counter[str]] = defaultdict(Counter)

    data = cat.get("DATA", [])
    for cat_entry in data:
        cat_num = str(cat_entry.get("i", ""))
        for sc in cat_entry.get("s", []):
            for uc in sc.get("u", []):
                uc_id = uc.get("i") or ""
                refs_raw = uc.get("refs") or ""
                urls = _extract_urls(refs_raw)
                classified: list[dict] = []
                url_cats: list[str] = []
                for url in urls:
                    try:
                        netloc = urlparse(url).netloc
                    except Exception:
                        netloc = ""
                    cat_name = _classify_host(netloc)
                    classified.append({"url": url, "category": cat_name})
                    url_cats.append(cat_name)
                origin = _primary_origin(url_cats)
                origin_counts[origin] += 1
                per_category[cat_num][origin] += 1
                entries[uc_id] = {
                    "uc_id": uc_id,
                    "origin": origin,
                    "origin_label": BADGE_LABEL[origin],
                    "references": classified,
                    "last_reviewed": uc.get("reviewed") or None,
                    "status": uc.get("status") or None,
                }

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_ucs": len(entries),
        "origin_counts": dict(origin_counts),
        "per_category": {k: dict(v) for k, v in per_category.items()},
        "entries": entries,
    }


def render_coverage_doc(ledger: dict) -> str:
    total = ledger["total_ucs"]
    counts = ledger["origin_counts"]

    def pct(n: int) -> str:
        return f"{n:,} ({n / total * 100:.1f}%)" if total else f"{n}"

    # Order rows by priority for display
    ordered_origins = sorted(counts.keys(),
                             key=lambda c: -ORIGIN_PRIORITY.get(c, 0))

    lines = [
        "# Provenance coverage",
        "",
        "Auto-generated by `scripts/build_provenance.py`. Do not edit by hand.",
        "",
        f"_Generated {ledger['generated_at']} — {total:,} use cases audited._",
        "",
        "## How provenance is classified",
        "",
        "Every UC's `References` field is parsed for URLs; each URL is tagged",
        "with a source category and the UC's *primary origin* is the most",
        "authoritative category among its citations. The priority ladder is:",
        "",
        "| Rank | Category | Description |",
        "| ---- | -------- | ----------- |",
    ]
    for cat in sorted(ORIGIN_PRIORITY.keys(), key=lambda c: -ORIGIN_PRIORITY[c]):
        desc = next((r.label for r in HOST_RULES if r.category == cat),
                    "No external citation — authored by contributors"
                    if cat == "contributor"
                    else "URL not matching any known vendor / standards body")
        lines.append(f"| {ORIGIN_PRIORITY[cat]} | `{cat}` | {desc} |")

    lines.extend([
        "",
        "## Overall coverage",
        "",
        "| Origin | UCs |",
        "| ------ | --- |",
    ])
    for origin in ordered_origins:
        lines.append(f"| {BADGE_LABEL[origin]} (`{origin}`) | {pct(counts[origin])} |")

    lines.extend([
        "",
        "## Coverage by top-level category",
        "",
        "| Category | Total | Splunk | Vendor | MITRE | Standards | Threat-intel | Blog | Community | Other | Contributor |",
        "| -------- | ----- | ------ | ------ | ----- | --------- | ------------ | ---- | --------- | ----- | ----------- |",
    ])
    for cat_num in sorted(ledger["per_category"].keys(),
                          key=lambda x: int(x) if x.isdigit() else 9999):
        per = ledger["per_category"][cat_num]
        tot = sum(per.values())
        row = [
            f"Cat {cat_num}",
            f"{tot:,}",
            f"{per.get('splunk-official', 0):,}",
            f"{per.get('vendor-official', 0):,}",
            f"{per.get('mitre-attack', 0):,}",
            f"{per.get('nist-compliance', 0):,}",
            f"{per.get('threat-intel', 0):,}",
            f"{per.get('splunk-blog', 0):,}",
            f"{per.get('community', 0):,}",
            f"{per.get('unclassified', 0):,}",
            f"{per.get('contributor', 0):,}",
        ]
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero if > 10%% of UCs fall back to 'contributor'.")
    parser.add_argument("--no-write", action="store_true",
                        help="Do not write outputs (diagnostic dry-run).")
    args = parser.parse_args()

    ledger = build_ledger()

    if not args.no_write:
        PROVENANCE_PATH.write_text(
            json.dumps(ledger, indent=2, ensure_ascii=False) + "\n",
            "utf-8",
        )
        print(f"Wrote {PROVENANCE_PATH}")

        DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
        DOC_PATH.write_text(render_coverage_doc(ledger), "utf-8")
        print(f"Wrote {DOC_PATH}")

        # Compact JS payload for the dashboard.  Only a short origin
        # code per UC is exported (the dashboard already has URLs via
        # `refs` in catalog.json).  Total size ~180KB for 6k UCs.
        # The full JSON remains available at /provenance.json for API
        # consumers.
        origin_code = {
            "splunk-official": "SO",
            "vendor-official": "VO",
            "mitre-attack":    "MA",
            "nist-compliance": "NC",
            "threat-intel":    "TI",
            "splunk-blog":     "SB",
            "community":       "CO",
            "unclassified":    "UN",
            "contributor":     "CT",
        }
        compact = {
            uc_id: origin_code.get(e["origin"], "CT")
            for uc_id, e in ledger["entries"].items()
        }
        labels_by_code = {origin_code[k]: BADGE_LABEL[k] for k in origin_code}
        PROVENANCE_JS_PATH.write_text(
            "// Auto-generated by scripts/build_provenance.py — do not edit\n"
            "window.PROVENANCE = "
            + json.dumps(compact, separators=(",", ":"), ensure_ascii=False)
            + ";\n"
            "window.PROVENANCE_LABELS = "
            + json.dumps(labels_by_code, separators=(",", ":"))
            + ";\n",
            "utf-8",
        )
        print(f"Wrote {PROVENANCE_JS_PATH}")

    total = ledger["total_ucs"]
    counts = ledger["origin_counts"]
    print(f"Provenance indexed: {total:,} UCs")
    for origin in sorted(counts.keys(),
                         key=lambda c: -ORIGIN_PRIORITY.get(c, 0)):
        print(f"  {origin:<20} {counts[origin]:>5,}")

    if args.strict:
        contrib = counts.get("contributor", 0)
        if total and contrib / total > 0.10:
            print(f"ERROR: {contrib / total * 100:.1f}% of UCs fall back to "
                  "'contributor' (>10% threshold).", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
