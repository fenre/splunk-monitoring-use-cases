#!/usr/bin/env python3
"""
List procedure names from Splunk IT Essentials Learn app (if you have the app unpacked).

The public docs do not list the 60+ procedure names. Use this script after:
  1. Downloading the app from https://splunkbase.splunk.com/app/5390/
  2. Unpacking the .spl (it's a zip) or copying the app from $SPLUNK_HOME/etc/apps/

Usage:
  python3 list_ite_learn_procedures.py [ path_to_ITE_Learn_app ]

Example:
  python3 list_ite_learn_procedures.py /opt/splunk/etc/apps/Splunk_IT_Essentials_Learn
  python3 list_ite_learn_procedures.py ./Splunk_IT_Essentials_Learn

If no path is given, prints instructions and optional places to look.
"""

from __future__ import print_function

import os
import re
import sys
import json

# Common places where procedure-like content might live in the app
PROCEDURE_CANDIDATES = [
    "default/data/ui/views/*.xml",
    "lookups/*.csv",
    "default/*.conf",
    "metadata/default.meta",
]


def main():
    app_dir = (sys.argv[1] if len(sys.argv) > 1 else "").strip()
    if not app_dir or not os.path.isdir(app_dir):
        print("Usage: list_ite_learn_procedures.py <path_to_ITE_Learn_app>")
        print()
        print("To get the procedure list:")
        print("  1. Download IT Essentials Learn from https://splunkbase.splunk.com/app/5390/")
        print("  2. Unzip the .spl file (rename to .zip and unzip, or use 'unzip app.spl')")
        print("  3. Run this script with the path to the unpacked app directory")
        print()
        print("Alternatively, in the Splunk UI open the IT Essentials Learn app,")
        print("go to the Investigate tab, and note the procedure titles listed there.")
        sys.exit(0)

    found = []
    for root, dirs, files in os.walk(app_dir):
        for f in files:
            path = os.path.join(root, f)
            rel = os.path.relpath(path, app_dir)
            # Look for view titles or procedure-like names in XML/CSV
            if f.endswith(".xml") and ("view" in root or "view" in f):
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                        text = fp.read()
                    # Simple extraction of title or label
                    for pat in [r'<title>([^<]+)</title>', r'label="([^"]+)"', r'<label>([^<]+)</label>']:
                        for m in re.finditer(pat, text):
                            title = m.group(1).strip()
                            if title and len(title) > 3 and (("procedure" in rel.lower()) or ("investigate" in rel.lower())):
                                found.append((rel, title))
                except Exception:
                    pass
            if f.endswith(".csv") and "lookup" in root:
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                        head = fp.readline()
                    if "procedure" in head.lower() or "title" in head.lower() or "name" in head.lower():
                        found.append((rel, "(CSV) " + head.strip()))
                except Exception:
                    pass

    if found:
        print("Possible procedure-related entries (file -> title/label):")
        for rel, title in found[:200]:
            print("  ", rel, "->", title[:80])
    else:
        print("No procedure-like content found in expected places.")
        print("The app may store procedure list in a different structure (e.g. REST or JS).")
        print("Use the Investigate tab in the app UI to copy procedure names manually.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
