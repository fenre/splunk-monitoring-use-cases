# Equipment Table (Filter by “What You Have”)

The dashboard lets users **filter use cases by equipment** they have (e.g. “Windows servers”, “AWS”, “Palo Alto”). This is powered by an **equipment table** that maps **IT equipment / platforms** to **Splunk add-ons (TAs)** mentioned in use cases.

## How It Works

1. **Equipment table** (`EQUIPMENT` in `build.py`)  
   Each entry has:
   - **id** — slug used in the UI and in use case data (e.g. `windows`, `aws`).
   - **label** — user-facing name (e.g. “Windows servers & workstations”).
   - **tas** — list of substrings; if **any** of these appears in a use case’s **App/TA** field, that use case is considered relevant for this equipment.
   - **models** (optional) — for hardware, a list of models/variants (each with id, label, tas) so the main list stays short; matching use cases get compound ids in **`uc.em`**.

2. **Per–use case equipment tags**  
   When `build.py` runs, it sets **`uc.e`** (equipment ids) and **`uc.em`** (compound ids, e.g. hardware_bmc_idrac) for every use case by matching **`uc.t`** (App/TA text) against each equipment’s **tas** and each model's **tas**.

3. **UI**  
   The **Equipment** dropdown lets users pick one equipment type. For equipment with **models** (e.g. **Hardware / BMC**), a second **Model** dropdown (sub-search) appears so users can filter by a specific model (e.g. Dell iDRAC, HPE iLO). "All models" filters by **`uc.e`**; a chosen model filters by **`uc.em`**. The main content and header count update accordingly.

## Where the Table Is Defined

- **Source:** `build.py` — constant **`EQUIPMENT`** (list of `{id, label, tas}` and optional **models**).
- **Output:** Written to **`data.js`** as **`EQUIPMENT`**; each use case in **`DATA`** has **`e`** and **`em`** arrays.

## Adding or Changing Equipment

1. Edit **`EQUIPMENT`** in `build.py`.
2. Add or adjust entries, e.g.:
   - **id:** unique slug (e.g. `new_platform`).
   - **label:** name shown in the dropdown.
   - **tas:** list of substrings that appear in App/TA when a use case is relevant (e.g. `["Splunk_TA_foo", "Foo Bar"]`). Matching is case-insensitive.
   - **models** (optional): list of `{ "id": "model_slug", "label": "Display name", "tas": ["substring1", ...] }`. Use this for hardware (or other equipment) where you want a **sub-search** so the main equipment list doesn’t get too long. The UI shows a second "Model" dropdown when this equipment is selected.
3. Run **`python3 build.py`** to regenerate **`data.js`** (and **`catalog.json`**).

Use cases that mention any of the **tas** strings in their App/TA field will then get that equipment **id** in **`uc.e`** and appear when the user selects that equipment. If the equipment has **models**, matching use cases also get compound ids in **`uc.em`** (e.g. `hardware_bmc_idrac`) so users can filter by a specific model in the sub-dropdown.
