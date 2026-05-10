# Inventory & Sizing — User Guide

Two related catalogue features that work together:

1. **My Inventory** + **Equipment filter** — tell the catalogue what
   hardware/vendors you have, and it filters to use cases that *actually
   apply to your stack*.
2. **Data Sizing Assessment (DSA)** — a back-of-the-envelope ingest
   sizing estimator for the inventory you've selected.

For the developer-facing equipment registry (`equipment[]` field, slug
conventions, API endpoints), see [Equipment Table](equipment-table.md).

## My Inventory

### What it is

A persistent shortlist of equipment slugs (vendors, products, OS
families, network gear, OT controllers) attached to your browser. The
catalogue uses it as an **opt-in narrowing filter**: when active, only
UCs whose `equipment[]` overlaps your inventory are shown.

### Opening the inventory modal

Click **My Inventory** in the header. The modal shows:

- **Selected** count + clear button.
- A **search input** that filters the equipment list.
- **Categories** (Networking / Security / Compute / OS / OT / SaaS / …)
  with collapsible groups.
- For each equipment slug: a checkbox, the human name, the vendor, and
  a count of UCs in the catalogue tagged for that equipment.
- Bottom action bar: **Import JSON**, **Export JSON**, **Apply Filter**,
  **Estimate Sizing →**.

### Selecting equipment

Tick the checkboxes for everything you actually have or plan to deploy.
The catalogue stores the selection in `localStorage` so it survives
across visits. Clicking **Apply Filter** dismisses the modal and
applies the inventory as a catalogue filter — UCs without an
intersection with your inventory are hidden.

The **Equipment** dropdown in the header is a quick-pick variant of the
same filter — choose any single slug to filter without opening the
modal.

When an equipment vendor has multiple **models** (e.g. Cisco Catalyst
9300 vs 9500), a secondary **Model** dropdown appears once you pick the
vendor.

### Import / export

The modal's **Import JSON** and **Export JSON** buttons round-trip the
selection through a small file. Useful for:

- Sharing your inventory with a colleague to compare relevant UCs.
- Versioning your inventory in git alongside other site assets.
- Bootstrapping the same inventory across multiple browsers.

The shape is a simple list:

```json
{
  "version": 1,
  "selected": ["cisco-catalyst", "cisco-ise", "vmware-vsphere", "fortinet-fortigate"]
}
```

## Equipment filter on the catalogue

Once an inventory is active, the catalogue:

- Adds a **My Inventory** badge with the count of selected items in the header.
- Filters every tab (Categories, Subcategories, Use Cases, Quick wins,
  Recently added, Quality) to UCs that match.
- Surfaces an **inventory-specific roadmap band** in the implementation
  roadmap collapsible — crawl/walk/run sequenced for *your* stack.
- Marks each UC card with the matching equipment chips so you can see
  which vendor triggered the inclusion.

Inventory is opt-in — until you apply it, the catalogue shows
everything.

## Data Sizing Assessment (DSA)

A standalone web app under `tools/data-sizing/` that estimates the
ingest volume (events-per-second, GB/day, indexer/storage) of a Splunk
deployment for a given set of data sources.

### Two ways in

1. **From My Inventory** — click **Estimate Sizing →** in the inventory
   modal. The tool opens with your selected equipment pre-loaded as
   data sources at sensible defaults.
2. **Direct** — visit `/tools/data-sizing/` (in-product) or the
   **Data Sizing** link in the catalogue footer. You'll start with an
   empty workload and add sources by hand.

### What it computes

- **Events per second (EPS)** per source and aggregated.
- **GB / day** of raw ingest at typical event sizes.
- **Indexer count** and **hot-storage / cold-storage** at the retention
  you specify.
- A **summary report** that you can copy to clipboard or download as a
  shareable file.

### What it knows about

The source catalogue covers:

- **Security**: AD, EDR, firewalls, IDS/IPS, DNS/DHCP, email security, VPN.
- **IT**: Linux, Windows, vSphere, Kubernetes, Docker, OpenShift, application servers.
- **OT**: Modbus, OPC-UA, MQTT, SNMP, BACnet, Edge Hub.
- **Network**: NetFlow, IPFIX, Zeek, Stream, packet capture.
- **Protocols**: syslog, JSON-over-TCP, HEC.
- **Business**: SaaS audit logs, ITSM events, identity events.
- **Cisco vendor stack** and **OT vendor stack** — pre-loaded with sane
  per-endpoint rates derived from typical field deployments.

### Interpreting the output

The numbers are *reference defaults*. They're useful for:

- Initial proposals and design documents.
- Comparing alternative collection strategies.
- Scoping a Splunk Cloud subscription tier.
- Spotting the dominant source in a workload (it's almost never what
  customers expect).

Always validate against your own collector telemetry before sizing
production. The tool says so prominently in its footer for a reason.

### Source maps

The mapping between catalogue equipment slugs and DSA data sources
lives in `tools/data-sizing/mapping.js` (catalogue side) and
`tools/data-sizing/ot-data-sources.js` (OT side). When a new equipment
slug is added to the catalogue, it should also be added there so the
"Estimate Sizing →" hand-off seeds the right defaults.

## Sizing tray (catalogue → DSA)

In the Use Cases tab, every card has a small **multi-select checkbox**
in its top-right corner. Selected UCs are tracked in a footer **sizing
tray** that shows:

- The count of selected UCs.
- A list of *unique data sources* required by those UCs.
- An **Estimate Data Sizing →** button that opens DSA pre-loaded with
  those sources.

This is the second hand-off into DSA — useful for "I know which UCs
I want, what does it cost to ingest them?".

## Where the data comes from

| Surface | Source of truth |
|---|---|
| Equipment slugs and models | `data/equipment.json` + the loader in `splunk_uc.equipment` |
| Per-UC equipment tagging | `equipment[]` and `equipmentModels[]` in `content/cat-NN-*/UC-X.Y.Z.json` |
| Catalogue-side counts and filtering | Build-time enrichment in `tools/build/enrichment.py` (writes `EQUIPMENT` block of `catalog.json`) |
| Per-equipment API | `api/v1/equipment/index.json` and `api/v1/equipment/<slug>.json` |
| DSA source catalogue | `tools/data-sizing/mapping.js` and `ot-data-sources.js` |
| DSA sizing math | `tools/data-sizing/app.js` |

## Privacy

All inventory selections live in your browser's `localStorage`. Nothing
is sent to a server. The catalogue is fully static — there is no
backend to track what you selected. Same for DSA.

## Where to go next

- [Equipment Table](equipment-table.md) — developer-facing reference for
  the equipment registry.
- [Site User Guide](site-user-guide.md) — for the rest of the
  catalogue's UX.
- [Recommender App](recommender-app.md) — the same idea pushed
  *inside* Splunk: the recommender app scans your indexes and CIM
  models, and recommends UCs based on what's actually flowing in.
- [Build Artefacts Reference](build-artefacts-reference.md) — for what
  the build emits (including DSA under `dist/tools/data-sizing/`).
