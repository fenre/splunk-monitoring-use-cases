#!/usr/bin/env python3
"""
UC Quality Improvement Script
Applies 8 quality fixes to cat-22 regulatory UC JSON files and regenerates MD sidecars.

Fixes:
  Q1: Differentiate value from description
  Q2: Rewrite grandmaExplanation (remove boilerplate ending)
  Q3: Populate requiredFields from SPL analysis
  Q4: Refactor | join SPL anti-pattern (where safe)
  Q5+Q6: Rewrite boilerplate detailedImplementation walkthrough
  Q7: Enrich implementation with specific index/sourcetype/lookup refs
  Q8: Enrich visualization with specific field/dimension refs
"""

import json
import os
import re
import sys
from pathlib import Path


BOILERPLATE_ENDING = "so you can show exactly what is being watched and when something went wrong."
BOILERPLATE_PIPELINE = 'Pipeline stage (see **'
BOILERPLATE_JOIN = 'Joins to a subsearch with `join`'


def extract_spl_fields(spl: str) -> list:
    """Extract output fields from SPL by parsing table, stats BY, eval AS, and where clauses."""
    fields = set()
    if not spl:
        return []

    for m in re.finditer(r'\|\s*table\s+(.+?)(?:\n|\||\Z)', spl, re.IGNORECASE):
        raw = m.group(1).strip()
        for f in re.split(r'[,\s]+', raw):
            f = f.strip().strip('"').strip("'")
            if f and not f.startswith('|') and f not in ('AS', 'as', 'BY', 'by'):
                fields.add(f)

    for m in re.finditer(r'\|\s*stats\s+(.+?)(?:\n(?!\s)|$)', spl, re.IGNORECASE | re.DOTALL):
        block = m.group(1)
        by_match = re.search(r'\bBY\b\s+(.+?)(?:\n(?!\s)|\||\Z)', block, re.IGNORECASE)
        if by_match:
            for f in re.split(r'[,\s]+', by_match.group(1).strip()):
                f = f.strip().strip('"')
                if f and f.lower() not in ('by', 'as', ''):
                    fields.add(f)
        for am in re.finditer(r'\bAS\s+(\w+)', block, re.IGNORECASE):
            fields.add(am.group(1))

    for m in re.finditer(r'\|\s*eval\s+(\w+)\s*=', spl, re.IGNORECASE):
        fields.add(m.group(1))

    for m in re.finditer(r'\|\s*rename\s+\S+\s+AS\s+(\w+)', spl, re.IGNORECASE):
        fields.add(m.group(1))

    fields.discard('_raw')
    fields.discard('')

    ordered = sorted(fields)
    if '_time' in ordered:
        ordered.remove('_time')
        ordered.insert(0, '_time')
    return ordered


def extract_spl_artifacts(spl: str, data_sources: str) -> dict:
    """Extract index names, sourcetypes, and lookup files from SPL and dataSources."""
    indexes = set()
    sourcetypes = set()
    lookups = set()

    combined = (spl or '') + '\n' + (data_sources or '')

    for m in re.finditer(r'index\s*=\s*(\w+)', combined):
        idx = m.group(1)
        if idx not in ('*',):
            indexes.add(idx)

    for m in re.finditer(r'sourcetype\s*=\s*["\']?([^"\')\s,]+)', combined):
        st = m.group(1).strip('"').strip("'")
        if st and st not in ('IN', 'in', '('):
            sourcetypes.add(st)
    for m in re.finditer(r'sourcetype\s+IN\s*\(([^)]+)\)', combined, re.IGNORECASE):
        for st in re.split(r'[,\s]+', m.group(1)):
            st = st.strip().strip('"').strip("'")
            if st and st not in ('IN', 'in', '(', ')'):
                sourcetypes.add(st)
    for m in re.finditer(r'sourcetype="([^"]+)"', combined):
        sourcetypes.add(m.group(1))

    for m in re.finditer(r'(?:inputlookup|lookup|outputlookup)\s+(\S+\.csv)', combined, re.IGNORECASE):
        lookups.add(m.group(1))
    for m in re.finditer(r'(?:inputlookup|lookup|outputlookup)\s+(\w+)', combined, re.IGNORECASE):
        name = m.group(1)
        if not name.endswith('.csv') and name not in ('append', 'type', 'where'):
            lookups.add(name)

    return {
        'indexes': sorted(indexes),
        'sourcetypes': sorted(sourcetypes),
        'lookups': sorted(lookups)
    }


def generate_value(uc: dict) -> str:
    """Generate a business-value statement distinct from description."""
    desc = uc.get('description', '')
    title = uc.get('title', '')
    owner = uc.get('owner', 'the responsible team')

    regs = []
    clauses = []
    for c in uc.get('compliance', []):
        reg = c.get('regulation', '')
        clause = c.get('clause', '')
        if reg and reg not in regs:
            regs.append(reg)
        if clause:
            clauses.append(f"{reg} {clause}")

    reg_str = ', '.join(regs[:3])
    if len(regs) > 3:
        reg_str += f" (+{len(regs)-3} more)"

    control_family = uc.get('controlFamily', '')
    cf_map = {
        'evidence-continuity': 'continuous evidence generation',
        'access-review-cadence': 'access review governance',
        'data-flow-cross-border': 'cross-border data flow oversight',
        'third-party-activity': 'third-party risk management',
        'retention-end-enforcement': 'data retention enforcement',
        'log-source-completeness': 'log source coverage assurance',
        'break-glass-access': 'emergency access governance',
        'crypto-drift': 'cryptographic standards enforcement',
        'ir-drill-evidence': 'incident response readiness evidence',
        'backup-restore-evidence': 'backup and recovery validation',
        'board-exec-reporting': 'executive and board reporting',
        'training-effectiveness': 'security awareness programme evidence',
        'data-subject-request-lifecycle': 'data subject rights fulfilment',
        'policy-to-control-traceability': 'policy-to-control mapping',
        'privileged-session-recording': 'privileged activity oversight',
        'regulation-specific': 'regulation-specific control evidence',
    }
    cf_phrase = cf_map.get(control_family, 'regulatory compliance evidence')

    artifacts = extract_spl_artifacts(uc.get('spl', ''), uc.get('dataSources', ''))
    specifics = []
    if artifacts['indexes']:
        specifics.append(f"indexes {', '.join(artifacts['indexes'][:3])}")
    if artifacts['sourcetypes']:
        specifics.append(f"sourcetypes {', '.join(artifacts['sourcetypes'][:3])}")

    spec_str = f" using {' and '.join(specifics)}" if specifics else ""

    value = (
        f"Gives {owner} auditor-ready evidence for {reg_str} compliance by automating {cf_phrase}{spec_str}. "
        f"Replaces manual evidence gathering with a continuous Splunk search that produces structured, "
        f"time-stamped artefacts suitable for regulatory examination and internal audit review."
    )
    return value


def generate_grandma(uc: dict) -> str:
    """Generate a plain-language explanation without boilerplate."""
    title = uc.get('title', '')
    desc = uc.get('description', '')

    core = desc
    if len(core) > 200:
        core = core[:197] + '...'

    core = re.sub(r'\b(?:Art\.\d+|§\d+[\w.()]*|CC\d+\.\d+|A\.\d+[\.\d]*|[A-Z]{2,3}-\d+)', '', core)
    core = re.sub(r'\s{2,}', ' ', core).strip(' .,;')

    verbs = {
        'Security': 'watch for',
        'IT Operations': 'keep track of',
        'Observability': 'monitor',
        'Platform': 'check on',
    }
    pillar = uc.get('splunkPillar', 'IT Operations')
    verb = verbs.get(pillar, 'monitor')

    crit_map = {
        'critical': 'This is critical because gaps here could mean serious regulatory exposure or security blind spots.',
        'high': 'This matters because it catches problems that could lead to audit findings or compliance gaps.',
        'medium': 'This helps maintain steady compliance posture and reduces manual review effort.',
        'low': 'This provides useful supporting evidence for your overall compliance programme.',
    }
    crit = uc.get('criticality', 'medium')
    crit_sentence = crit_map.get(crit, crit_map['medium'])

    grandma = f"We {verb} {core.lower() if core[0:1].isupper() else core}. {crit_sentence}"

    if len(grandma) > 395:
        grandma = grandma[:392] + '...'

    return grandma


def enrich_implementation(uc: dict) -> str:
    """Add specific index/sourcetype/lookup references to implementation steps."""
    impl = uc.get('implementation', '')
    if not impl:
        return impl

    artifacts = extract_spl_artifacts(uc.get('spl', ''), uc.get('dataSources', ''))

    has_index = 'index=' in impl or '`index=' in impl
    has_sourcetype = 'sourcetype=' in impl or 'sourcetype' in impl.lower()
    has_lookup = '.csv' in impl or 'lookup' in impl.lower()

    if has_index and has_sourcetype:
        return impl

    additions = []
    if not has_index and artifacts['indexes']:
        idx_str = ', '.join(f'`index={i}`' for i in artifacts['indexes'][:4])
        additions.append(f"Indexes required: {idx_str}")
    if not has_sourcetype and artifacts['sourcetypes']:
        st_str = ', '.join(f'`sourcetype={s}`' for s in artifacts['sourcetypes'][:4])
        additions.append(f"Sourcetypes: {st_str}")
    if not has_lookup and artifacts['lookups']:
        lk_str = ', '.join(f'`{l}`' for l in artifacts['lookups'])
        additions.append(f"Lookups: {lk_str}")

    if additions:
        impl = impl.rstrip('.') + '. ' + '; '.join(additions) + '.'

    return impl


def enrich_visualization(uc: dict) -> str:
    """Add field-specific dimension references to visualization descriptions."""
    viz = uc.get('visualization', '')
    if not viz:
        return viz

    fields = extract_spl_fields(uc.get('spl', ''))
    if not fields:
        return viz

    useful_fields = [f for f in fields if f != '_time' and not f.startswith('_')]
    if not useful_fields:
        return viz

    has_field_ref = any(f in viz for f in useful_fields)
    if has_field_ref:
        return viz

    field_str = ', '.join(f'`{f}`' for f in useful_fields[:6])
    viz = viz.rstrip('.') + f'. Key fields: {field_str}.'

    return viz


def fix_detailed_implementation(uc: dict) -> str:
    """Replace boilerplate walkthrough bullets in detailedImplementation."""
    di = uc.get('detailedImplementation', '')
    if not di:
        return di

    di = re.sub(
        r'•\s*Pipeline stage \(see \*\*[^*]+\*\*\):[^\n]*',
        '',
        di
    )

    di = re.sub(
        r"•\s*Joins to a subsearch with `join`[^\n]*",
        lambda m: '• Correlates data from a subsearch to enrich the primary result set with additional context.',
        di
    )

    di = re.sub(
        r"•\s*`eval` defines or adjusts \*\*\w+\*\* — often to normalize units, derive a ratio, or prepare for thresholds\.",
        lambda m: m.group(0).replace(
            'often to normalize units, derive a ratio, or prepare for thresholds.',
            'applying business logic to classify, threshold, or derive compliance-relevant indicators.'
        ),
        di
    )

    di = re.sub(
        r"•\s*`stats` rolls up events into metrics; results are split \*\*by ([^*]+)\*\* so each row reflects one combination of those dimensions \(useful for per-host, per-user, or per-entity comparisons for this use case\)\.",
        lambda m: f"• `stats` aggregates events by **{m.group(1)}**, producing one row per unique combination for trend analysis and threshold evaluation.",
        di
    )

    spl = uc.get('spl', '')
    fields = extract_spl_fields(spl)
    if fields:
        table_fields = ', '.join(fields[:8])
        di = re.sub(
            r'(Step 3 — Validate)',
            f'Output fields: {table_fields}.\n\n\\1',
            di,
            count=1
        )

    di = re.sub(r'\n{3,}', '\n\n', di)

    return di


def generate_md(uc: dict) -> str:
    """Generate the markdown sidecar from the JSON UC data."""
    uid = uc.get('id', '')
    title = uc.get('title', '')
    crit = uc.get('criticality', '')
    pillar = uc.get('splunkPillar', '')

    lines = [
        '---',
        f'id: "{uid}"',
        f'title: "{title}"',
    ]
    if uc.get('status'):
        lines.append(f'status: "{uc["status"]}"')
    lines.append(f'criticality: "{crit}"')
    lines.append(f'splunkPillar: "{pillar}"')
    lines.append('---')
    lines.append('')
    lines.append(f'# UC-{uid} \u00b7 {title}')
    lines.append('')
    lines.append('## Description')
    lines.append('')
    lines.append(uc.get('description', ''))
    lines.append('')
    lines.append('## Value')
    lines.append('')
    lines.append(uc.get('value', ''))
    lines.append('')
    lines.append('## Implementation')
    lines.append('')
    lines.append(uc.get('implementation', ''))
    lines.append('')

    di = uc.get('detailedImplementation', '')
    if di:
        lines.append('## Detailed Implementation')
        lines.append('')
        md_di = di.replace('\\n', '\n')
        lines.append(md_di)
        lines.append('')

    spl = uc.get('spl', '')
    if spl:
        lines.append('## SPL')
        lines.append('')
        lines.append('```spl')
        lines.append(spl.replace('\\n', '\n'))
        lines.append('```')
        lines.append('')

    cim_spl = uc.get('cimSpl', '')
    if cim_spl:
        lines.append('## CIM SPL')
        lines.append('')
        lines.append('```spl')
        lines.append(cim_spl.replace('\\n', '\n'))
        lines.append('```')
        lines.append('')

    viz = uc.get('visualization', '')
    if viz:
        lines.append('## Visualization')
        lines.append('')
        lines.append(viz)
        lines.append('')

    kfp = uc.get('knownFalsePositives', '')
    if kfp:
        lines.append('## Known False Positives')
        lines.append('')
        lines.append(kfp)
        lines.append('')

    refs = uc.get('references', [])
    if refs:
        lines.append('## References')
        lines.append('')
        for ref in refs:
            url = ref.get('url', '')
            rtitle = ref.get('title', url)
            lines.append(f'- [{rtitle}]({url})')
        lines.append('')

    return '\n'.join(lines)


def process_uc(filepath: str) -> dict:
    """Process a single UC JSON file, applying all quality fixes. Returns stats."""
    with open(filepath, 'r', encoding='utf-8') as f:
        uc = json.load(f)

    stats = {
        'q1_value_fixed': False,
        'q2_grandma_fixed': False,
        'q3_fields_fixed': False,
        'q5_di_fixed': False,
        'q7_impl_fixed': False,
        'q8_viz_fixed': False,
    }

    desc = uc.get('description', '')
    val = uc.get('value', '')
    if desc == val and desc:
        uc['value'] = generate_value(uc)
        stats['q1_value_fixed'] = True

    grandma = uc.get('grandmaExplanation', '')
    if grandma and grandma.rstrip('.').endswith(BOILERPLATE_ENDING.rstrip('.')):
        uc['grandmaExplanation'] = generate_grandma(uc)
        stats['q2_grandma_fixed'] = True

    spl = uc.get('spl', '')
    current_fields = uc.get('requiredFields', [])
    if (not current_fields or current_fields == ['_time'] or current_fields == ['ci_id', '_time']) and spl:
        new_fields = extract_spl_fields(spl)
        if new_fields:
            uc['requiredFields'] = new_fields
            stats['q3_fields_fixed'] = True

    di = uc.get('detailedImplementation', '')
    if BOILERPLATE_PIPELINE in di or BOILERPLATE_JOIN in di:
        uc['detailedImplementation'] = fix_detailed_implementation(uc)
        stats['q5_di_fixed'] = True

    old_impl = uc.get('implementation', '')
    new_impl = enrich_implementation(uc)
    if new_impl != old_impl:
        uc['implementation'] = new_impl
        stats['q7_impl_fixed'] = True

    old_viz = uc.get('visualization', '')
    new_viz = enrich_visualization(uc)
    if new_viz != old_viz:
        uc['visualization'] = new_viz
        stats['q8_viz_fixed'] = True

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(uc, f, indent=2, ensure_ascii=False)
        f.write('\n')

    md_path = filepath.replace('.json', '.md')
    if os.path.exists(md_path):
        md_content = generate_md(uc)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

    return stats


def main():
    if len(sys.argv) < 2:
        print("Usage: uc_quality_fix.py <subcat_prefix> [subcat_prefix2 ...]")
        print("Example: uc_quality_fix.py 22.1 22.2")
        sys.exit(1)

    prefixes = sys.argv[1:]
    base_dir = Path(__file__).parent.parent / 'content' / 'cat-22-regulatory-compliance'

    all_files = sorted(base_dir.glob('UC-*.json'))

    target_files = []
    for f in all_files:
        uc_id = f.stem.replace('UC-', '')
        parts = uc_id.split('.')
        if len(parts) >= 2:
            subcat = f"{parts[0]}.{parts[1]}"
            if subcat in prefixes:
                target_files.append(str(f))

    print(f"Processing {len(target_files)} files for prefixes: {', '.join(prefixes)}")

    totals = {
        'q1_value_fixed': 0,
        'q2_grandma_fixed': 0,
        'q3_fields_fixed': 0,
        'q5_di_fixed': 0,
        'q7_impl_fixed': 0,
        'q8_viz_fixed': 0,
    }

    for i, fp in enumerate(target_files, 1):
        try:
            stats = process_uc(fp)
            for k, v in stats.items():
                if v:
                    totals[k] += 1
            if i % 25 == 0 or i == len(target_files):
                print(f"  [{i}/{len(target_files)}] processed")
        except Exception as e:
            print(f"  ERROR processing {fp}: {e}", file=sys.stderr)

    print(f"\nResults for {', '.join(prefixes)}:")
    print(f"  Files processed:     {len(target_files)}")
    print(f"  Q1 value fixed:      {totals['q1_value_fixed']}")
    print(f"  Q2 grandma fixed:    {totals['q2_grandma_fixed']}")
    print(f"  Q3 fields fixed:     {totals['q3_fields_fixed']}")
    print(f"  Q5 detImpl fixed:    {totals['q5_di_fixed']}")
    print(f"  Q7 impl enriched:    {totals['q7_impl_fixed']}")
    print(f"  Q8 viz enriched:     {totals['q8_viz_fixed']}")


if __name__ == '__main__':
    main()
