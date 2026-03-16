# Category files and display names

## Why there are more markdown files than categories

The build only turns a file into a **category** if its first `# N.` or `## N.` heading is a **top-level** category (e.g. `## 10. Security Infrastructure`). One file is intentionally **not** a category and is **skipped** by the build:

| File | Reason it's skipped |
|------|----------------------|
| **cat-00-preamble.md** | No category heading. It's the repo intro and legend (field descriptions). |

So: **20 category files** (cat-01 through cat-20) produce the 20 categories in the dashboard; **cat-00** is the only extra markdown file that does not become a category.

---

## Why markdown filenames don't match the names in the dashboard

The **dashboard (HTML)** shows category names like **"Server & Compute"** and **"Application Infrastructure"**.  
The **markdown files** are named like `cat-01-server-compute.md` and `cat-08-application-infrastructure.md`.

They differ on purpose:

| Where | Form | Example |
|-------|------|--------|
| **Filename** | Slug: lowercase, hyphens, no spaces or `&` | `cat-08-application-infrastructure.md` |
| **Dashboard** | Human-readable: from the first heading in the file | `## 8. Application Infrastructure` → "Application Infrastructure" |

- **Filenames** must be safe for every filesystem and URL (no spaces, no `&`, etc.). The slug (e.g. `application-infrastructure`) is just a stable, readable hint for which file is which.
- **Display names** are taken from the **first line of each category file**: the `# N. Category Name` or `## N. Category Name` heading. The build never uses the filename for the label.

So the "name" of the category for the UI is **whatever you put in that first heading**. If you rename the category in the markdown (e.g. change `## 8. Application Infrastructure` to `## 8. Web & Application Infrastructure`), the dashboard will show the new text after you run `build.py`. The file can stay named `cat-08-application-infrastructure.md` unless you choose to rename it for consistency.

## Convention

Keeping the **filename slug** aligned with the **category name** (lowercase, spaces → hyphens, `&` → omitted or `and`) makes it easier to find the right file. Examples:

- "Server & Compute" → `cat-01-server-compute.md`
- "Identity & Access Management" → `cat-09-identity-access-management.md`
- "IoT & Operational Technology (OT)" → `cat-14-iot-operational-technology-ot.md`

The build only requires that the file matches `cat-[0-9]*.md` and that the first heading matches `# N.` or `## N.`; the rest of the filename is for humans.
