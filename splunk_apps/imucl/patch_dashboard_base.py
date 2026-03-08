#!/usr/bin/env python3
"""Patch app copy of index.html so relative script URLs resolve in iframe."""
import os
import sys

def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(repo_root, "imucl", "appserver", "static", "dashboard", "index.html")
    if len(sys.argv) > 1:
        path = sys.argv[1]
    base_tag = (
        '<base id="dashboard-base" href="">'
        '<script>(function(){var e=document.getElementById("dashboard-base");'
        'if(e)e.href=location.pathname.replace(/\\/[^/]*$/,"")||"/";})();<\\/script>'
    )
    with open(path) as f:
        c = f.read()
    if "<head>" + base_tag in c:
        print("index.html already patched.", file=sys.stderr)
        return
    c = c.replace("<head>", "<head>" + base_tag, 1)
    with open(path, "w") as f:
        f.write(c)
    print("Patched index.html for iframe base URL.")

if __name__ == "__main__":
    main()
