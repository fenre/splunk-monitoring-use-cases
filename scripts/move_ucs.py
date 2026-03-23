#!/usr/bin/env python3
"""Move misplaced use cases to their correct categories.

Moves are defined as (source_file, uc_id, target_file, target_subcategory).
- Extracts UC blocks from source files (leaving numbering gaps).
- Appends to target subcategory with next available number.
- Handles within-file moves and empty-section cleanup.
"""

import re
import os
import sys
from collections import defaultdict

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'use-cases')

# (source_stem, uc_id, target_stem, target_sub_prefix)
MOVES = [
    # ── Cat 1 Windows → proper functional homes ──────────────────────
    ("cat-01-server-compute", "1.2.14", "cat-08-application-infrastructure", "8.1"),   # IIS web
    ("cat-01-server-compute", "1.2.85", "cat-08-application-infrastructure", "8.1"),   # IIS app pool
    ("cat-01-server-compute", "1.2.74", "cat-02-virtualization", "2.2"),               # Hyper-V
    ("cat-01-server-compute", "1.2.80", "cat-06-storage-backup", "6.3"),               # Backup
    ("cat-01-server-compute", "1.2.18", "cat-09-identity-access-management", "9.1"),   # AD replication
    ("cat-01-server-compute", "1.2.75", "cat-09-identity-access-management", "9.1"),   # ADCS
    ("cat-01-server-compute", "1.2.99", "cat-08-application-infrastructure", "8.3"),   # MSMQ

    # ── Cat 3 cloud serverless → Cat 4 ───────────────────────────────
    ("cat-03-containers-orchestration", "3.5.4", "cat-04-cloud-infrastructure", "4.1"),  # Fargate → AWS
    ("cat-03-containers-orchestration", "3.5.5", "cat-04-cloud-infrastructure", "4.2"),  # ACI → Azure
    ("cat-03-containers-orchestration", "3.5.6", "cat-04-cloud-infrastructure", "4.3"),  # Cloud Run → GCP

    # ── Cat 5 ISE → Cat 17 NAC ───────────────────────────────────────
    ("cat-05-network-infrastructure", "5.8.6", "cat-17-network-security-zero-trust", "17.1"),

    # ── Cat 8 mail UCs → Cat 11 (repurposed 11.4) ───────────────────
    ("cat-08-application-infrastructure", "8.6.3",  "cat-11-email-collaboration", "11.4"),
    ("cat-08-application-infrastructure", "8.6.4",  "cat-11-email-collaboration", "11.4"),
    ("cat-08-application-infrastructure", "8.6.5",  "cat-11-email-collaboration", "11.4"),
    ("cat-08-application-infrastructure", "8.6.6",  "cat-11-email-collaboration", "11.4"),
    ("cat-08-application-infrastructure", "8.6.7",  "cat-11-email-collaboration", "11.4"),
    ("cat-08-application-infrastructure", "8.6.8",  "cat-11-email-collaboration", "11.4"),
    ("cat-08-application-infrastructure", "8.6.9",  "cat-11-email-collaboration", "11.4"),
    ("cat-08-application-infrastructure", "8.6.15", "cat-11-email-collaboration", "11.4"),

    # ── Cat 8 ThousandEyes → Cat 5.9 (consolidate) ──────────────────
    ("cat-08-application-infrastructure", "8.7.1",  "cat-05-network-infrastructure", "5.9"),
    ("cat-08-application-infrastructure", "8.7.2",  "cat-05-network-infrastructure", "5.9"),
    ("cat-08-application-infrastructure", "8.7.3",  "cat-05-network-infrastructure", "5.9"),
    ("cat-08-application-infrastructure", "8.7.4",  "cat-05-network-infrastructure", "5.9"),
    ("cat-08-application-infrastructure", "8.7.5",  "cat-05-network-infrastructure", "5.9"),
    ("cat-08-application-infrastructure", "8.7.6",  "cat-05-network-infrastructure", "5.9"),
    ("cat-08-application-infrastructure", "8.7.7",  "cat-05-network-infrastructure", "5.9"),
    ("cat-08-application-infrastructure", "8.7.8",  "cat-05-network-infrastructure", "5.9"),
    ("cat-08-application-infrastructure", "8.7.9",  "cat-05-network-infrastructure", "5.9"),
    ("cat-08-application-infrastructure", "8.7.10", "cat-05-network-infrastructure", "5.9"),
    ("cat-08-application-infrastructure", "8.7.11", "cat-05-network-infrastructure", "5.9"),
    ("cat-08-application-infrastructure", "8.7.12", "cat-05-network-infrastructure", "5.9"),

    # ── Cat 11 Jira → Cat 8 app servers ──────────────────────────────
    ("cat-11-email-collaboration", "11.3.24", "cat-08-application-infrastructure", "8.2"),

    # ── Cat 11 Cisco Spaces → Cat 15 physical security ──────────────
    ("cat-11-email-collaboration", "11.4.1", "cat-15-data-center-physical-infrastructure", "15.3"),
    ("cat-11-email-collaboration", "11.4.2", "cat-15-data-center-physical-infrastructure", "15.3"),
    ("cat-11-email-collaboration", "11.4.3", "cat-15-data-center-physical-infrastructure", "15.3"),
    ("cat-11-email-collaboration", "11.4.4", "cat-15-data-center-physical-infrastructure", "15.3"),
    ("cat-11-email-collaboration", "11.4.5", "cat-15-data-center-physical-infrastructure", "15.3"),
    ("cat-11-email-collaboration", "11.4.6", "cat-15-data-center-physical-infrastructure", "15.3"),

    # ── Cat 13 ThousandEyes → Cat 5.9 ────────────────────────────────
    ("cat-13-observability-monitoring-stack", "13.3.15", "cat-05-network-infrastructure", "5.9"),
    ("cat-13-observability-monitoring-stack", "13.3.16", "cat-05-network-infrastructure", "5.9"),
    ("cat-13-observability-monitoring-stack", "13.3.17", "cat-05-network-infrastructure", "5.9"),
    ("cat-13-observability-monitoring-stack", "13.3.18", "cat-05-network-infrastructure", "5.9"),
    ("cat-13-observability-monitoring-stack", "13.3.19", "cat-05-network-infrastructure", "5.9"),
    ("cat-13-observability-monitoring-stack", "13.3.20", "cat-05-network-infrastructure", "5.9"),
    ("cat-13-observability-monitoring-stack", "13.3.21", "cat-05-network-infrastructure", "5.9"),
    ("cat-13-observability-monitoring-stack", "13.3.22", "cat-05-network-infrastructure", "5.9"),
    ("cat-13-observability-monitoring-stack", "13.3.23", "cat-05-network-infrastructure", "5.9"),

    # ── Cat 13 ServiceNow sync → Cat 16 ticketing ────────────────────
    ("cat-13-observability-monitoring-stack", "13.2.22", "cat-16-service-management-itsm", "16.1"),

    # ── Cat 14 DC power/access → Cat 15 ─────────────────────────────
    ("cat-14-iot-operational-technology-ot", "14.1.2", "cat-15-data-center-physical-infrastructure", "15.1"),
    ("cat-14-iot-operational-technology-ot", "14.1.3", "cat-15-data-center-physical-infrastructure", "15.1"),
    ("cat-14-iot-operational-technology-ot", "14.1.4", "cat-15-data-center-physical-infrastructure", "15.3"),
    ("cat-14-iot-operational-technology-ot", "14.3.8", "cat-15-data-center-physical-infrastructure", "15.2"),

    # ── Cat 12 Control-M → Cat 16 business process ──────────────────
    ("cat-12-devops-ci-cd", "12.2.13", "cat-16-service-management-itsm", "16.3"),

    # ── Cat 16 Shadow IT → Cat 10 SWG ────────────────────────────────
    ("cat-16-service-management-itsm", "16.2.11", "cat-10-security-infrastructure", "10.5"),

    # ── Within Cat 15: 15.3 → 15.1 / 15.2 ───────────────────────────
    ("cat-15-data-center-physical-infrastructure", "15.3.6",  "cat-15-data-center-physical-infrastructure", "15.1"),
    ("cat-15-data-center-physical-infrastructure", "15.3.9",  "cat-15-data-center-physical-infrastructure", "15.1"),
    ("cat-15-data-center-physical-infrastructure", "15.3.19", "cat-15-data-center-physical-infrastructure", "15.2"),

    # ── Within Cat 17: 17.3 → 17.1 / 17.2 ───────────────────────────
    ("cat-17-network-security-zero-trust", "17.3.9",  "cat-17-network-security-zero-trust", "17.1"),
    ("cat-17-network-security-zero-trust", "17.3.10", "cat-17-network-security-zero-trust", "17.2"),

    # ── Within Cat 6: 6.4 backup UCs → 6.3 ──────────────────────────
    ("cat-06-storage-backup", "6.4.7",  "cat-06-storage-backup", "6.3"),
    ("cat-06-storage-backup", "6.4.8",  "cat-06-storage-backup", "6.3"),
    ("cat-06-storage-backup", "6.4.9",  "cat-06-storage-backup", "6.3"),
    ("cat-06-storage-backup", "6.4.10", "cat-06-storage-backup", "6.3"),
    ("cat-06-storage-backup", "6.4.11", "cat-06-storage-backup", "6.3"),
]

UC_HEADING = re.compile(r'^### UC-(\d+(?:\.\d+)+)\s')
ANY_HEADING = re.compile(r'^#{2,3}\s')


def filepath(stem):
    return os.path.join(BASE, stem + '.md')


def read_lines(stem):
    with open(filepath(stem), encoding='utf-8') as f:
        return f.readlines()


def write_lines(stem, lines):
    with open(filepath(stem), 'w', encoding='utf-8') as f:
        f.writelines(lines)


def find_uc_block(lines, uc_id):
    """Return (start, end) line indices for a UC block. end is exclusive."""
    target = f'### UC-{uc_id}'
    start = None
    for i, line in enumerate(lines):
        if line.rstrip().startswith(target):
            rest = line[len(target):]
            if not rest.strip() or rest.strip().startswith('·') or rest.strip().startswith('—'):
                start = i
                break
    if start is None:
        return None
    end = start + 1
    while end < len(lines):
        if ANY_HEADING.match(lines[end]):
            break
        end += 1
    return (start, end)


def find_last_uc_num(lines, sub_prefix):
    """Find the highest UC number N in ### UC-{sub_prefix}.N headings."""
    pattern = re.compile(r'^### UC-' + re.escape(sub_prefix) + r'\.(\d+)\s')
    last = 0
    for line in lines:
        m = pattern.match(line)
        if m:
            n = int(m.group(1))
            if n > last:
                last = n
    return last


def find_subcategory_insert_point(lines, sub_prefix):
    """Find the line index where new UCs should be appended for a subcategory.

    This is the line just before the next subcategory heading (### X.Y or ## X.Y)
    that is NOT a UC heading and NOT part of the current subcategory.
    """
    cat_num = sub_prefix.split('.')[0]
    sub_num = sub_prefix.split('.')[1]

    sub_heading_patterns = [
        re.compile(r'^### ' + re.escape(sub_prefix) + r'\s'),
        re.compile(r'^## ' + re.escape(sub_prefix) + r'\s'),
    ]
    sub_start = None
    for i, line in enumerate(lines):
        for pat in sub_heading_patterns:
            if pat.match(line):
                sub_start = i
                break
        if sub_start is not None:
            break

    if sub_start is None:
        print(f"  WARNING: Could not find subcategory heading for {sub_prefix}")
        return len(lines)

    next_sub = re.compile(
        r'^#{2,3}\s+' + re.escape(cat_num) + r'\.(\d+)\s'
    )
    for i in range(sub_start + 1, len(lines)):
        m = next_sub.match(lines[i])
        if m:
            found_sub = m.group(1)
            if found_sub != sub_num:
                return i
    return len(lines)


def renumber_block(block_lines, old_id, new_id):
    """Replace UC-{old_id} with UC-{new_id} in the header line."""
    result = []
    for line in block_lines:
        if line.startswith(f'### UC-{old_id}'):
            line = line.replace(f'UC-{old_id}', f'UC-{new_id}', 1)
        result.append(line)
    return result


def ensure_trailing_separator(block_lines):
    """Ensure the block ends with a --- separator and blank line."""
    text = ''.join(block_lines).rstrip()
    if not text.endswith('---'):
        text += '\n\n---\n'
    else:
        text += '\n'
    return text.split('\n')


def main():
    # Collect all affected files
    all_stems = set()
    for src, uid, tgt, tsub in MOVES:
        all_stems.add(src)
        all_stems.add(tgt)

    # Read all files
    files = {}
    for stem in all_stems:
        files[stem] = read_lines(stem)
        print(f"Read {stem}: {len(files[stem])} lines")

    # ─── Phase 1: Extract all UC blocks ──────────────────────────────
    extracted = {}
    for src, uid, tgt, tsub in MOVES:
        result = find_uc_block(files[src], uid)
        if result is None:
            print(f"  ERROR: Could not find UC-{uid} in {src}")
            sys.exit(1)
        start, end = result
        block = files[src][start:end]
        extracted[(src, uid)] = block
        print(f"  Extracted UC-{uid} from {src} (lines {start+1}–{end})")

    # ─── Phase 2: Remove all extracted blocks from source files ──────
    removals_by_file = defaultdict(set)
    for src, uid, tgt, tsub in MOVES:
        removals_by_file[src].add(uid)

    for stem, uc_ids in removals_by_file.items():
        lines = files[stem]
        ranges = []
        for uid in uc_ids:
            result = find_uc_block(lines, uid)
            if result:
                ranges.append(result)
        ranges.sort(reverse=True)
        for start, end in ranges:
            del lines[start:end]
        files[stem] = lines
        print(f"  Removed {len(ranges)} UC blocks from {stem}")

    # ─── Phase 3: Special cases ──────────────────────────────────────

    # Cat 11.4: all Cisco Spaces UCs removed → rename section header
    cat11 = files["cat-11-email-collaboration"]
    for i, line in enumerate(cat11):
        if '11.4 Cisco Spaces' in line:
            cat11[i] = '### 11.4 Mail Transport & Relay Infrastructure\n'
            # Remove the "Primary App/TA" line and blank lines after the header
            j = i + 1
            while j < len(cat11) and (cat11[j].strip() == '' or
                    cat11[j].startswith('**Primary App/TA')):
                j += 1
            # Replace with a new Primary App/TA line
            cat11[i+1:j] = [
                '\n',
                '**Primary App/TA:** Postfix, Sendmail, Microsoft Exchange, '
                'Cisco Email Security Appliance (ESA), generic SMTP/MTA logs\n',
                '\n',
                '---\n',
                '\n',
            ]
            print(f"  Renamed 11.4 section to 'Mail Transport & Relay Infrastructure'")
            break

    # Cat 8.7: all ThousandEyes UCs removed → remove empty section header
    cat8 = files["cat-08-application-infrastructure"]
    for i, line in enumerate(cat8):
        if '8.7' in line and 'ThousandEyes' in line and line.startswith('###'):
            # Remove the section header and any preamble lines until the next
            # section or end of file
            j = i
            while j < len(cat8):
                if j > i and cat8[j].startswith('###'):
                    break
                j += 1
            del cat8[i:j]
            print(f"  Removed empty 8.7 ThousandEyes section header from cat-08")
            break

    # ─── Phase 4: Insert blocks into target files ────────────────────

    # Group moves by (target_file, target_sub) preserving order
    insertions = defaultdict(list)
    for src, uid, tgt, tsub in MOVES:
        block = extracted[(src, uid)]
        insertions[(tgt, tsub)].append((uid, block))

    for (tgt, tsub), items in insertions.items():
        lines = files[tgt]
        last_num = find_last_uc_num(lines, tsub)
        insert_point = find_subcategory_insert_point(lines, tsub)

        new_blocks_text = []
        for uid, block in items:
            last_num += 1
            new_id = f"{tsub}.{last_num}"
            renamed = renumber_block(block, uid, new_id)
            block_text = ''.join(renamed).rstrip('\n') + '\n'
            if not block_text.rstrip().endswith('---'):
                block_text = block_text.rstrip('\n') + '\n\n---\n'
            new_blocks_text.append(block_text)
            print(f"  UC-{uid} → UC-{new_id} in {tgt}")

        insert_text = '\n' + '\n'.join(new_blocks_text) + '\n'
        insert_lines = insert_text.split('\n')
        insert_lines = [l + '\n' for l in insert_lines[:-1]]  # re-add newlines

        files[tgt][insert_point:insert_point] = insert_lines

    # ─── Phase 5: Write all files ────────────────────────────────────
    for stem in all_stems:
        write_lines(stem, files[stem])
        print(f"Wrote {stem}: {len(files[stem])} lines")

    print(f"\nDone. Moved {len(MOVES)} use cases.")


if __name__ == '__main__':
    main()
