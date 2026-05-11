#!/usr/bin/env python3
"""audit_doc_regulations.py — regulation / standard name hallucination
sweep across the repository's prose documentation.

Why this script exists
----------------------

The cat-22 regulatory-compliance catalogue (`content/cat-22-*/UC-*.json`)
is the single source of truth for regulations the project claims to
cover.  Prose under `docs/`, however, regularly references regulations
and standards inline ("PCI DSS 4.0 Requirement 12.4.1", "NIS2 Article
21(2)(f)").  An LLM-generated draft can:

  * Cite a regulation acronym we never claim coverage for ("HMRC AML",
    "Singapore TRMG-2024").
  * Misspell a real one ("SOC-2 Type-3", "NIST CSFv3").
  * Invent a clause / article / section number outside the document's
    real range ("GDPR Article 124", which does not exist — GDPR ends
    at Article 99).

This audit walks every Markdown file under `docs/` and at the repo
root, extracts every UPPERCASE token that looks like a regulation
acronym (3-12 chars, allowing digits / dots / dashes / slashes),
cross-checks against the union of acronyms found in the cat-22
catalogue plus a curated set of well-known industry acronyms, and
reports the unmatched mentions for human review.

This is a **report-only** detector — it does not modify any markdown
or auto-edit references.  Suspicious tokens are written to
`data/doc-regulation-mentions.json` and printed to stdout grouped by
frequency.  A second list summarises tokens that DO match the
catalogue but appear with what looks like an out-of-range clause
number (very conservative — only the regulations whose clause space
we explicitly bound here).

Stdlib-only.  Imports nothing from outside the standard library.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STATUS_PATH = REPO / "data" / "doc-regulation-mentions.json"

DOCS_DIR = REPO / "docs"
DEFAULT_EXTRA = [
    "AGENTS.md",
    "AGENTS-EXAMPLES.md",
    "CHANGELOG.md",
    "CODEBASE-DIAGRAM.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "README.md",
    "LEGAL.md",
    "api/README.md",
]
CAT_DIR = REPO / "content" / "cat-22-regulatory-compliance"

FENCE_RE = re.compile(r"^([ \t]{0,3})```[^\n]*\n.*?\n\1```", re.S | re.M)
INLINE_CODE_RE = re.compile(r"`{1,3}[^`]+`{1,3}", re.S)
FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.S)
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")
# The auto-generated references footer is a flat list of bibliography
# entries we already validated separately; do not double-count it.
AUTOGEN_RE = re.compile(
    r"<!-- BEGIN AUTOGEN: references -->.*?<!-- END AUTOGEN: references -->",
    re.S,
)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def collect_docs() -> list[Path]:
    out: list[Path] = []
    if DOCS_DIR.is_dir():
        for p in DOCS_DIR.rglob("*.md"):
            if p.is_file():
                out.append(p)
    for rel in DEFAULT_EXTRA:
        p = REPO / rel
        if p.is_file():
            out.append(p)
    return sorted({p.resolve() for p in out})


def clean_prose(text: str) -> str:
    text = FRONTMATTER_RE.sub("", text)
    text = AUTOGEN_RE.sub("", text)
    text = FENCE_RE.sub(lambda m: " " * (m.end() - m.start()), text)
    text = INLINE_CODE_RE.sub(lambda m: " " * (m.end() - m.start()), text)
    text = HTML_TAG_RE.sub(" ", text)
    text = MARKDOWN_LINK_RE.sub(r"\1", text)
    return text


# ---------------------------------------------------------------- catalogue seed
# Acronyms that show up in the cat-22 corpus are part of the project's
# advertised coverage and are by definition "known".  We rebuild this
# every run from the JSON SSOT so the audit stays in step with the
# catalogue rather than drifting behind a hard-coded list.
#
# Token shape: at least four UPPERCASE letters somewhere in the run.
# A leading capital plus 3+ uppercase letters keeps SOX / GDPR / NIST
# style acronyms while filtering out ISO clause references
# ("A.5.15", "A.8.28"), OWASP IDs ("A01"), and short single-letter
# fragments.  This trades recall for precision — recall is provided
# by the clause-overshoot detector below.
ACRONYM_RE = re.compile(r"\b[A-Z]{4,12}(?:[0-9]{1,4})?\b")


def load_catalog_acronyms() -> Counter[str]:
    counts: Counter[str] = Counter()
    if not CAT_DIR.is_dir():
        return counts
    for fp in sorted(CAT_DIR.glob("UC-*.json")):
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        fields: list[str] = []
        for key in (
            "title", "description", "value", "implementation",
            "visualization",
        ):
            v = d.get(key)
            if isinstance(v, str):
                fields.append(v)
        aliases = d.get("aliases")
        if isinstance(aliases, list):
            fields.extend(str(a) for a in aliases)
        # `tags` and `complianceTags` collect framework / regulation
        # identifiers explicitly — most reliable seed.
        for key in ("tags", "complianceTags", "frameworks"):
            v = d.get(key)
            if isinstance(v, list):
                fields.extend(str(a) for a in v)
        text = " ".join(fields)
        for m in ACRONYM_RE.finditer(text):
            counts[m.group(0)] += 1
    return counts


# Generic industry / technology acronyms that frequently sit next to
# regulation acronyms in prose but are NOT regulations themselves.
# Including them in the "known" set keeps the unknown list focused on
# actual regulation candidates.
GENERIC_NON_REG = {
    # Computing & data
    "API", "REST", "JSON", "YAML", "XML", "CSV", "HTML", "URL",
    "URI", "URN", "DNS", "DHCP", "TCP", "UDP", "TLS", "SSL", "MTLS",
    "SSH", "SMB", "FTP", "SFTP", "SMTP", "IMAP", "POP3", "LDAP",
    "SAML", "OIDC", "OAUTH", "JWT", "SAML2", "SQL", "NoSQL",
    "CIDR", "IPv4", "IPv6", "ARP", "BGP", "OSPF", "EIGRP", "ISIS",
    "MPLS", "VPN", "VXLAN", "NAT", "PAT", "DMZ", "WAN", "LAN",
    # Cloud
    "AWS", "GCP", "EC2", "S3", "IAM", "EKS", "GKE", "AKS", "RDS",
    "VPC", "ALB", "NLB", "ELB", "CDN", "STS", "KMS", "WAF",
    "AAD", "AAD-DS", "AKS", "GCP", "GKE", "VPC", "IAM",
    # Containers / orchestration / observability
    "K8S", "K3S", "OCI", "OTEL", "RED", "USE", "SLI", "SLO",
    "SLA", "OPA", "CRD", "CNI", "CSI", "MTTR", "MTTC", "MTTD",
    "MTTI", "RPO", "RTO", "BCP", "DRP", "ITSM", "ITIL", "CI/CD",
    "CICD", "VCS", "SCM", "DAG", "ETL", "ELT", "ELK", "BI",
    # Splunk-specific surface
    "UC", "UCs", "UF", "HF", "SH", "IDX", "DS", "ES", "SOAR",
    "ESCU", "CIM", "MLTK", "ITSI", "DSDL", "SVD", "VLA", "VLAs",
    "TA", "TAs", "RBA", "SPL", "SPL2", "ABAC", "RBAC", "FBA",
    "UEBA", "CISO", "CIO", "CTO", "DPO", "GRC", "OT", "ICS",
    "IIOT", "IIoT", "IoT", "SCADA", "PLC", "RTU", "DCS", "HMI",
    "MES", "ERP", "CRM", "PIM", "CMDB", "AD", "AAD", "M365",
    "MFA", "SSO", "JIT", "PAM", "PIM", "AC", "WIDS", "IDS", "IPS",
    "SIEM", "EDR", "XDR", "MDR", "NDR", "TDIR", "SecOps",
    "DevOps", "DevSecOps", "FinOps", "AIOps", "GitOps",
    # Geo / org abbreviations widely used in prose
    "EU", "US", "USA", "UK", "GB", "DE", "FR", "IT", "ES", "JP",
    "CN", "IN", "AU", "CA", "BR", "MX", "AE", "SA", "QA", "BH",
    "KW", "OM", "TR", "EEA", "EFTA", "ASEAN", "NATO", "OECD",
    "G7", "G20", "BRICS",
    # Cardinal numbers / single-letter ranges that the regex picks up
    "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "A1", "B1", "C1", "L1", "L2", "L3", "L4", "L5", "L6", "L7",
    "T1", "T2", "T3",
    # Misc operational
    "FAQ", "HOWTO", "TOC", "PR", "PRs", "WIP", "TODO", "RFC",
    "FAQ", "NDA", "MoU", "MOU", "SOW", "RFP", "RFQ", "RFI",
    "POC", "PoC", "MVP", "Q1", "Q2", "Q3", "Q4", "YOY", "MoM",
    "HR", "PR", "QA", "QC", "RD", "R&D", "M&A", "PnL",
    # Acronyms that appear next to versions and counts
    "AI", "ML", "LLM", "GPT", "RAG", "ASR", "TTS", "NLP", "OCR",
    "GPU", "CPU", "RAM", "ROM", "SSD", "HDD", "NIC", "TPU",
}


# Common malformed forms we may want to allow because they appear in
# real published documents (joined by hyphen, slash, version suffix).
EXTRA_KNOWN_REGS = {
    # Often-used short / long forms not in cat-22 sidecars but used
    # for context in prose ("ITGC", "SOC", "SOC 2", "SOC2", …)
    "ISO", "IEC", "ANSI", "BSI", "ENISA", "NIST", "NCSC", "CISA",
    "EBA", "ESMA", "EIOPA", "FINRA", "FDA", "EMA", "FCA", "OFCOM",
    "FCC", "BAFIN", "BAFin", "FINMA", "MAS", "JFSA", "PRA",
    "PCI", "DSS", "PCI-DSS", "PCI/DSS", "SOX", "GDPR", "UK-GDPR",
    "CCPA", "CPRA", "CPA", "VCDPA", "PIPL", "PDPA", "LGPD",
    "HIPAA", "HITRUST", "GLBA", "FFIEC", "FERPA", "COPPA",
    "DORA", "NIS2", "NIS", "TIBER-EU", "TIBER",
    "CMMC", "FISMA", "FedRAMP", "ITAR", "EAR", "NERC", "CIP",
    "TSA", "ICS-CERT", "TLP", "GRC", "ISO27001", "ISO27002",
    "ISO27017", "ISO27018", "ISO27701", "ISO27036",
    "ISO9001", "ISO22301", "ISO31000", "SOC", "SOC1", "SOC2",
    "SOC3", "SSAE", "SSAE-18", "SSAE18",
    "CSF", "RMF", "OSCAL", "SCAP", "ISA", "IEC62443",
    "IEC-62443", "ICS-OT", "MITRE", "ATT&CK", "CAPEC",
    "DISA-STIG", "STIG", "CIS", "OWASP", "SANS",
    "FAIR", "OCTAVE", "TARA", "PMP", "PRINCE2",
    "OFAC", "FATF", "AML", "KYC", "CFT", "MIFID",
    "MIFID2", "MIFID-II", "MIFIR", "PSD2", "EMIR",
    "CRD", "CRR", "CRD4", "CRD5", "CRD6", "Basel",
    "Basel-III", "Basel-IV", "BCBS-239", "BCBS239",
    "MAR", "CSDR", "DGS", "BRRD", "BRRD2",
    "EU-AI-ACT", "AI-ACT", "EU-AI", "EUAIACT",
    "TRMG", "TRM", "MAS-TRMG", "MAS-TRM",
    "OPM-RMF",
    "OPM", "POPIA", "APRA", "CPS", "CPS-234", "CPS234",
    "CRA",  # EU Cyber Resilience Act
    "DPA",  # Data Protection Act
    "DPDPA",  # India Digital Personal Data Protection Act
    "PDPB",
    "BAIT", "BSI-GS",
}


def build_known_set() -> set[str]:
    cat = load_catalog_acronyms()
    known = set(cat.keys())
    known |= GENERIC_NON_REG
    known |= EXTRA_KNOWN_REGS
    # Case-insensitive variants
    known |= {k.upper() for k in known}
    return known


# Regulations whose top-level clause/article space we know to be
# bounded.  Used to flag obvious overshoots ("GDPR Article 124" — GDPR
# ends at Article 99) for human review.  Be **extremely** conservative
# — only encode boundaries that are widely cited.
REGULATION_CLAUSE_BOUNDS: dict[str, tuple[str, int]] = {
    # acronym -> (clause keyword, max index)
    "GDPR": ("Article", 99),       # full text ends at Article 99
    "UK-GDPR": ("Article", 99),
    "NIS2": ("Article", 46),       # Directive (EU) 2022/2555, 46 articles
    "DORA": ("Article", 64),       # Regulation (EU) 2022/2554, 64 articles
    "CRA": ("Article", 71),        # EU Cyber Resilience Act, 71 articles
    "AI-ACT": ("Article", 113),    # Regulation (EU) 2024/1689
}

CLAUSE_REFERENCE_RE = re.compile(
    r"\b(GDPR|UK-GDPR|NIS2|DORA|CRA|AI-ACT)\b\s+(?:Article|Art\.?)\s*(\d+)",
    re.I,
)


def audit(docs: list[Path]) -> dict:
    known = build_known_set()
    mentions: defaultdict[str, list[dict]] = defaultdict(list)
    clause_overshoots: list[dict] = []
    for p in docs:
        text = p.read_text(encoding="utf-8", errors="ignore")
        prose = clean_prose(text)
        # Acronym sweep
        for m in ACRONYM_RE.finditer(prose):
            token = m.group(0)
            if token in known:
                continue
            line = prose.count("\n", 0, m.start()) + 1
            mentions[token].append({
                "path": p.relative_to(REPO).as_posix(),
                "line": line,
            })
        # Clause-overshoot sweep
        for m in CLAUSE_REFERENCE_RE.finditer(prose):
            acronym_canon = m.group(1).upper().replace("UK GDPR", "UK-GDPR")
            num = int(m.group(2))
            spec = REGULATION_CLAUSE_BOUNDS.get(acronym_canon)
            if not spec:
                continue
            keyword, max_idx = spec
            if num > max_idx:
                line = prose.count("\n", 0, m.start()) + 1
                clause_overshoots.append({
                    "path": p.relative_to(REPO).as_posix(),
                    "line": line,
                    "regulation": acronym_canon,
                    "clause": f"{keyword} {num}",
                    "max_documented": max_idx,
                })
    return {
        "_meta": {
            "tool": "scripts/audit_doc_regulations.py",
            "schema": 1,
            "docs_scanned": len(docs),
            "unknown_acronyms": len(mentions),
            "clause_overshoots": len(clause_overshoots),
        },
        "unknown_acronyms": {
            tok: {"count": len(occ), "samples": occ[:5]}
            for tok, occ in mentions.items()
        },
        "clause_overshoots": clause_overshoots,
    }


def write_status(payload: dict) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def summarise(payload: dict, top: int) -> None:
    print(f"Scanned {payload['_meta']['docs_scanned']} markdown files.")
    print()
    ua = payload["unknown_acronyms"]
    print(f"Unknown regulation-like acronyms: {len(ua)}")
    items = sorted(ua.items(), key=lambda kv: -kv[1]["count"])[:top]
    if not items:
        print("  (none — every acronym matched the catalogue or the "
              "generic-non-regulation allowlist)")
    else:
        for tok, info in items:
            print(f"  {info['count']:5d}  {tok}")
            for s in info["samples"][:3]:
                print(f"        {s['path']}:{s['line']}")
    print()
    co = payload["clause_overshoots"]
    print(f"Clause-overshoot suspects (over documented article count): {len(co)}")
    for entry in co[:50]:
        print(f"  {entry['path']}:{entry['line']}  "
              f"{entry['regulation']} {entry['clause']} "
              f"(max documented: {entry['max_documented']})")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--top", type=int, default=40,
                   help="Show this many unknown acronyms in the summary "
                        "(default 40).")
    args = p.parse_args(argv)
    docs = collect_docs()
    print(f"Scanning {len(docs)} markdown files ...\n")
    payload = audit(docs)
    write_status(payload)
    summarise(payload, args.top)
    print(f"\nStatus written -> {STATUS_PATH.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
