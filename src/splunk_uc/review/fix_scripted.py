"""``review-fix-scripted`` — mechanical fixes for UC review families (plan Phase 6a).

Only families whose fix needs no new facts are scripted. Each one removes or
normalises generated text; nothing here invents content:

* ``controltest-variant`` — "Variant N confirms zero alert rows ..." becomes
  "Confirm zero alert rows ...".
* ``purpose-built`` — drops the generated "Purpose-built for '<title>' in X
  workflows." sentence from ``description`` (skipped when the remainder would
  fall under the 120-character content-quality floor).
* ``premium-app-mismatch`` — removes a security-only premium app from a
  non-security UC unless the SPL or implementation text names that product
  or the entry carries a note explaining an optional integration.

Dry run by default: prints per-family counts and sample diffs. ``--apply``
rewrites the sidecars in their existing serialisation (indent, escaping and
key order preserved), so diffs show only the edited values. Use one family
per PR.

Usage::

    python -m splunk_uc review-fix-scripted --family controltest-variant --category cat-15
    python -m splunk_uc review-fix-scripted --family purpose-built --apply
"""

from __future__ import annotations

import argparse
import copy
import difflib
import json
import re
import sys
from collections import Counter
from collections.abc import Callable
from typing import Any

from splunk_uc.audits.text_quality import SECURITY_ONLY_PREMIUM_APPS
from splunk_uc.review._ledger import REPO_ROOT, iter_sidecars

DESCRIPTION_MIN = 120
NOTE_EXPLAINS_MIN = 12
VARIANT_RE = re.compile(r"\bVariant \d+ confirms zero alert rows")
PREMIUM_APP_MARKERS: dict[str, tuple[str, ...]] = {
    "Splunk Enterprise Security": (
        "enterprise security",
        "notable",
        "`risk",
        "index=risk",
        "correlation search",
    ),
    "Splunk User Behavior Analytics": ("user behavior analytics", "uba"),
    "Splunk SOAR": ("soar", "playbook"),
    "Splunk OT Security Add-on": ("ot security",),
}
SERIALISATIONS: tuple[tuple[int, bool], ...] = (
    (2, False),
    (2, True),
    (1, True),
    (1, False),
)

Fixer = Callable[[dict[str, Any]], tuple[dict[str, Any], str | None]]


def fix_controltest_variant(uc: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    ct = uc.get("controlTest")
    if not isinstance(ct, dict):
        return uc, None
    out = copy.deepcopy(uc)
    changed = False
    for key in ("positiveScenario", "negativeScenario"):
        text = ct.get(key)
        if isinstance(text, str) and VARIANT_RE.search(text):
            out["controlTest"][key] = VARIANT_RE.sub("Confirm zero alert rows", text)
            changed = True
    return (out, "controlTest") if changed else (uc, None)


def _purpose_built_re(title: str) -> re.Pattern[str]:
    quoted = re.escape(title) if title else r"[^']*"
    return re.compile(rf"\s*Purpose-built for '{quoted}'(?: in [^.]*? workflows)?\.")


def fix_purpose_built(uc: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    description = uc.get("description")
    if not isinstance(description, str) or "Purpose-built for" not in description:
        return uc, None
    pattern = _purpose_built_re(str(uc.get("title", "")))
    if not pattern.search(description):
        pattern = _purpose_built_re("")
    new = re.sub(r"\s{2,}", " ", pattern.sub("", description)).strip()
    if new == description.strip() or len(new) < DESCRIPTION_MIN:
        return uc, None
    out = copy.deepcopy(uc)
    out["description"] = new
    return out, "description"


def _app_name(entry: Any) -> str:
    if isinstance(entry, dict):
        return str(entry.get("name", ""))
    return str(entry)


def fix_premium_app_mismatch(uc: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    pillar = uc.get("splunkPillar")
    apps = uc.get("premiumApps")
    if not pillar or pillar == "Security" or not isinstance(apps, list):
        return uc, None
    haystack = " ".join(
        str(uc.get(k, "")) for k in ("spl", "cimSpl", "implementation", "detailedImplementation")
    ).lower()
    keep = []
    for entry in apps:
        name = _app_name(entry)
        markers = PREMIUM_APP_MARKERS.get(name, ())
        note = str(entry.get("note", "")) if isinstance(entry, dict) else ""
        explained = len(note.strip()) > NOTE_EXPLAINS_MIN
        if (
            name in SECURITY_ONLY_PREMIUM_APPS
            and not explained
            and not any(m in haystack for m in markers)
        ):
            continue
        keep.append(entry)
    if len(keep) == len(apps):
        return uc, None
    out = copy.deepcopy(uc)
    if keep:
        out["premiumApps"] = keep
    else:
        del out["premiumApps"]
    return out, "premiumApps"


FAMILIES: dict[str, Fixer] = {
    "controltest-variant": fix_controltest_variant,
    "purpose-built": fix_purpose_built,
    "premium-app-mismatch": fix_premium_app_mismatch,
}
#: deterministic check id (audit-text-quality) closed by each family.
FAMILY_CHECKS = {
    "controltest-variant": "template_v2:v2_controlTest_variant",
    "purpose-built": "template_v2:v2_description_purpose_built",
    "premium-app-mismatch": "premium_app_pillar_mismatch",
}


def serialise_like(raw: str, data: dict[str, Any]) -> str:
    """Serialise ``data`` with the same indent / escaping / trailing newline as ``raw``."""
    original = json.loads(raw)
    trailing = "\n" if raw.endswith("\n") else ""
    for indent, ensure_ascii in SERIALISATIONS:
        if json.dumps(original, indent=indent, ensure_ascii=ensure_ascii) + trailing == raw:
            return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii) + trailing
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def run(
    family: str,
    *,
    files: list[str] | None,
    category: str | None,
    apply: bool,
    samples: int,
) -> dict[str, Any]:
    fixer = FAMILIES[family]
    changed: list[str] = []
    fields: Counter[str] = Counter()
    diffs: list[str] = []
    scanned = 0
    for path, uc in iter_sidecars(files=files, category=category):
        scanned += 1
        new, field = fixer(uc)
        if field is None:
            continue
        raw = path.read_text(encoding="utf-8")
        text = serialise_like(raw, new)
        rel = str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT) else str(path)
        changed.append(rel)
        fields[field] += 1
        if len(diffs) < samples:
            diffs.append(
                "".join(
                    difflib.unified_diff(
                        raw.splitlines(keepends=True),
                        text.splitlines(keepends=True),
                        fromfile=f"a/{rel}",
                        tofile=f"b/{rel}",
                        n=0,
                    )
                )
            )
        if apply:
            path.write_text(text, encoding="utf-8")
    return {
        "family": family,
        "closes_check": FAMILY_CHECKS[family],
        "scanned": scanned,
        "changed": len(changed),
        "fields": dict(fields),
        "applied": apply,
        "files": changed,
        "sample_diffs": diffs,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m splunk_uc review-fix-scripted",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--family", choices=sorted(FAMILIES), required=True)
    parser.add_argument("--files", nargs="*")
    parser.add_argument("--category", help="Category prefix, e.g. cat-15")
    parser.add_argument("--apply", action="store_true", help="Write the fixed sidecars")
    parser.add_argument("--samples", type=int, default=3, help="Sample diffs to print")
    parser.add_argument("--json", action="store_true", help="Print the full result as JSON")
    args = parser.parse_args(argv)

    result = run(
        args.family,
        files=args.files,
        category=args.category,
        apply=args.apply,
        samples=args.samples,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for diff in result["sample_diffs"]:
            print(diff)
        verb = "changed" if args.apply else "would change"
        print(
            f"review-fix-scripted {args.family}: {verb} {result['changed']} of "
            f"{result['scanned']} UCs ({result['fields']})",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
