#!/usr/bin/env python3
"""Redistribute Meraki UCs from section 5.9 into their natural subcategories."""

import re, os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAT05 = os.path.join(BASE, 'use-cases', 'cat-05-network-infrastructure.md')
CAT09 = os.path.join(BASE, 'use-cases', 'cat-09-identity-access-management.md')
CAT14 = os.path.join(BASE, 'use-cases', 'cat-14-iot-operational-technology-ot.md')
CAT15 = os.path.join(BASE, 'use-cases', 'cat-15-data-center-physical-infrastructure.md')

# ── Mapping: old Meraki UC number → (target_file, target_sub, group_label) ──

WIRELESS = [1,2,3,4,5,6,7,8,10,12,13,14,15,16,17,18,19,20,21,22,106]
SWITCHING = [23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,101,102,103,104]
FIREWALL = [39,40,41,42,43,44,45,46,47,48,50,51,52,53,54,55,56,57,58,59,60,105]
DNSDHCP = [9,11,49,107,108]
MGMT = [61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,109,110]
CAMERAS = [76,77,78,79,80,81,82,83,84]
SENSORS = [85,86,87,88,89,90,91,92,93,94]
MDM = [95,96,97,98,99,100]


def parse_uc_blocks(lines):
    """Return dict mapping UC number (int) to list of lines (including the --- separator)."""
    blocks = {}
    current_num = None
    current_lines = []

    for line in lines:
        m = re.match(r'^### UC-5\.9\.(\d+) ', line)
        if m:
            if current_num is not None:
                blocks[current_num] = current_lines
            current_num = int(m.group(1))
            current_lines = [line]
        elif current_num is not None:
            current_lines.append(line)

    if current_num is not None:
        blocks[current_num] = current_lines

    return blocks


def renumber_block(lines, old_prefix, new_id):
    """Replace UC ID in a block. old_prefix like '5.9.23', new_id like '5.1.36'."""
    result = []
    for line in lines:
        result.append(line.replace(f'UC-{old_prefix}', f'UC-{new_id}'))
    return result


def find_section_end(lines, section_heading_pattern):
    """Find the line index just before the next ## heading after the matched section.
    Returns the index of the blank line before the next ## heading (insert point)."""
    in_section = False
    last_content = -1
    for i, line in enumerate(lines):
        if re.match(section_heading_pattern, line):
            in_section = True
            continue
        if in_section:
            if re.match(r'^## ', line):
                # Walk back past blank lines
                insert = i
                while insert > 0 and lines[insert-1].strip() == '':
                    insert -= 1
                return insert
            last_content = i
    # Section is at end of file
    return len(lines)


def build_insert_text(uc_blocks, uc_nums, target_sub, start_num):
    """Build the text to insert for a group of UCs being moved to target_sub."""
    result_lines = []
    for idx, num in enumerate(uc_nums):
        if num not in uc_blocks:
            print(f"  WARNING: UC-5.9.{num} not found in parsed blocks")
            continue
        new_num = start_num + idx
        new_id = f'{target_sub}.{new_num}'
        old_id = f'5.9.{num}'
        block = renumber_block(uc_blocks[num], old_id, new_id)
        # Ensure block ends with --- separator and blank line
        text = '\n'.join(block).rstrip()
        if not text.endswith('---'):
            text += '\n\n---'
        result_lines.append(text + '\n')
    return '\n'.join(result_lines)


def main():
    # ── Step 1: Parse cat-05 and extract 5.9 UC blocks ──
    with open(CAT05, 'r') as f:
        cat05_text = f.read()
    cat05_lines = cat05_text.split('\n')

    # Find 5.9 section boundaries
    sec59_start = None
    sec59_end = None
    for i, line in enumerate(cat05_lines):
        if re.match(r'^## 5\.9 ', line):
            sec59_start = i
        elif sec59_start is not None and re.match(r'^## 5\.10 ', line):
            sec59_end = i
            break

    if sec59_start is None or sec59_end is None:
        print("ERROR: Could not find section 5.9 boundaries")
        return

    print(f"Section 5.9: lines {sec59_start+1}-{sec59_end}")
    sec59_lines = cat05_lines[sec59_start:sec59_end]
    uc_blocks = parse_uc_blocks(sec59_lines)
    print(f"Parsed {len(uc_blocks)} UC blocks from 5.9")

    # Verify all UCs are accounted for
    all_mapped = set(WIRELESS + SWITCHING + FIREWALL + DNSDHCP + MGMT + CAMERAS + SENSORS + MDM)
    all_found = set(uc_blocks.keys())
    missing = all_found - all_mapped
    if missing:
        print(f"WARNING: Unmapped UCs: {sorted(missing)}")
    not_found = all_mapped - all_found
    if not_found:
        print(f"WARNING: Expected but not found: {sorted(not_found)}")

    # ── Step 2: Remove section 5.9 from cat-05 ──
    # Walk back from sec59_start to remove preceding blank lines
    trim_start = sec59_start
    while trim_start > 0 and cat05_lines[trim_start-1].strip() == '':
        trim_start -= 1

    new_cat05_lines = cat05_lines[:trim_start] + ['\n'] + cat05_lines[sec59_end:]
    print(f"Removed 5.9 section ({sec59_end - trim_start} lines)")

    # ── Step 3: Renumber 5.10 → 5.9, 5.11 → 5.10 in cat-05 ──
    new_cat05_text = '\n'.join(new_cat05_lines)
    # Section headings
    new_cat05_text = new_cat05_text.replace('## 5.10 Cisco ThousandEyes', '## 5.9 Cisco ThousandEyes')
    new_cat05_text = new_cat05_text.replace('## 5.11 Carrier and Service Provider Signaling', '## 5.10 Carrier and Service Provider Signaling')
    # UC IDs: 5.10.X → 5.9.X
    for i in range(1, 50):
        new_cat05_text = new_cat05_text.replace(f'UC-5.10.{i} ', f'UC-5.9.{i} ')
        new_cat05_text = new_cat05_text.replace(f'UC-5.10.{i}·', f'UC-5.9.{i}·')
    # UC IDs: 5.11.X → 5.10.X
    for i in range(1, 20):
        new_cat05_text = new_cat05_text.replace(f'UC-5.11.{i} ', f'UC-5.10.{i} ')
        new_cat05_text = new_cat05_text.replace(f'UC-5.11.{i}·', f'UC-5.10.{i}·')
    print("Renumbered 5.10 → 5.9, 5.11 → 5.10")

    # ── Step 4: Insert UCs into cat-05 target sections ──
    new_cat05_lines = new_cat05_text.split('\n')

    insertions = [
        (WIRELESS, '5.4', 12, r'^## 5\.4 '),
        (SWITCHING, '5.1', 36, r'^## 5\.1 '),
        (FIREWALL, '5.2', 19, r'^## 5\.2 '),
        (DNSDHCP, '5.6', 13, r'^## 5\.6 '),
        (MGMT, '5.8', 9, r'^## 5\.8 '),
    ]

    # Process insertions from bottom to top to preserve line numbers
    insert_points = []
    for uc_nums, target_sub, start_num, pattern in insertions:
        insert_text = build_insert_text(uc_blocks, uc_nums, target_sub, start_num)
        # Find end of target section
        end_idx = find_section_end(new_cat05_lines, pattern)
        insert_points.append((end_idx, insert_text, target_sub, len(uc_nums)))

    # Sort by position descending to insert from bottom up
    insert_points.sort(key=lambda x: x[0], reverse=True)

    for idx, text, sub, count in insert_points:
        insert_lines = text.split('\n')
        new_cat05_lines = new_cat05_lines[:idx] + ['', ''] + insert_lines + new_cat05_lines[idx:]
        print(f"Inserted {count} UCs into {sub} at line {idx}")

    # Clean up excessive blank lines
    final_text = '\n'.join(new_cat05_lines)
    while '\n\n\n\n' in final_text:
        final_text = final_text.replace('\n\n\n\n', '\n\n\n')

    with open(CAT05, 'w') as f:
        f.write(final_text)
    print(f"Wrote {CAT05}")

    # ── Step 5: Insert cameras into cat-15 section 15.3 ──
    with open(CAT15, 'r') as f:
        cat15_text = f.read()

    camera_text = build_insert_text(uc_blocks, CAMERAS, '15.3', 22)
    # Find end of file (15.3 is the last section)
    cat15_lines = cat15_text.split('\n')
    # Strip trailing blanks
    while cat15_lines and cat15_lines[-1].strip() == '':
        cat15_lines.pop()
    cat15_lines.append('')
    cat15_lines.append('')
    cat15_lines.extend(camera_text.split('\n'))
    cat15_lines.append('')

    cat15_final = '\n'.join(cat15_lines)
    while '\n\n\n\n' in cat15_final:
        cat15_final = cat15_final.replace('\n\n\n\n', '\n\n\n')
    with open(CAT15, 'w') as f:
        f.write(cat15_final)
    print(f"Inserted {len(CAMERAS)} camera UCs into cat-15 section 15.3")

    # ── Step 6: Insert sensors into cat-14 section 14.1 ──
    with open(CAT14, 'r') as f:
        cat14_text = f.read()
    cat14_lines = cat14_text.split('\n')

    sensor_text = build_insert_text(uc_blocks, SENSORS, '14.1', 15)
    # Find end of section 14.1 (before ### 14.2)
    insert_idx = None
    for i, line in enumerate(cat14_lines):
        if re.match(r'^### 14\.2 ', line):
            insert_idx = i
            while insert_idx > 0 and cat14_lines[insert_idx-1].strip() == '':
                insert_idx -= 1
            break
    if insert_idx is None:
        print("WARNING: Could not find 14.2, appending sensors at end of 14.1")
        insert_idx = len(cat14_lines)

    sensor_lines = sensor_text.split('\n')
    cat14_lines = cat14_lines[:insert_idx] + ['', ''] + sensor_lines + ['', ''] + cat14_lines[insert_idx:]
    cat14_final = '\n'.join(cat14_lines)
    while '\n\n\n\n' in cat14_final:
        cat14_final = cat14_final.replace('\n\n\n\n', '\n\n\n')
    with open(CAT14, 'w') as f:
        f.write(cat14_final)
    print(f"Inserted {len(SENSORS)} sensor UCs into cat-14 section 14.1")

    # ── Step 7: Create 9.6 Endpoint Management in cat-09 ──
    with open(CAT09, 'r') as f:
        cat09_text = f.read()
    cat09_lines = cat09_text.split('\n')

    # Strip trailing blanks
    while cat09_lines and cat09_lines[-1].strip() == '':
        cat09_lines.pop()

    mdm_text = build_insert_text(uc_blocks, MDM, '9.6', 1)
    new_section = [
        '',
        '',
        '### 9.6 Endpoint & Mobile Device Management',
        '',
        '**Primary App/TA:** Cisco Meraki Systems Manager, MDM API integrations',
        '',
        '---',
        '',
    ]
    cat09_lines.extend(new_section)
    cat09_lines.extend(mdm_text.split('\n'))
    cat09_lines.append('')

    cat09_final = '\n'.join(cat09_lines)
    while '\n\n\n\n' in cat09_final:
        cat09_final = cat09_final.replace('\n\n\n\n', '\n\n\n')
    with open(CAT09, 'w') as f:
        f.write(cat09_final)
    print(f"Created section 9.6 with {len(MDM)} MDM UCs in cat-09")

    # ── Summary ──
    total = len(WIRELESS) + len(SWITCHING) + len(FIREWALL) + len(DNSDHCP) + len(MGMT) + len(CAMERAS) + len(SENSORS) + len(MDM)
    print(f"\nRedistribution complete: {total} UCs moved")
    print(f"  → 5.4 Wireless: {len(WIRELESS)}")
    print(f"  → 5.1 Switching: {len(SWITCHING)}")
    print(f"  → 5.2 Firewalls: {len(FIREWALL)}")
    print(f"  → 5.6 DNS/DHCP: {len(DNSDHCP)}")
    print(f"  → 5.8 Management: {len(MGMT)}")
    print(f"  → 15.3 Cameras: {len(CAMERAS)}")
    print(f"  → 14.1 Sensors: {len(SENSORS)}")
    print(f"  → 9.6 MDM: {len(MDM)}")
    print(f"  5.10 ThousandEyes → 5.9")
    print(f"  5.11 Carrier → 5.10")


if __name__ == '__main__':
    main()
