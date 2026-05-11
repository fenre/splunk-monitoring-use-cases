# CIM Models Inventory

Central reference for the **Common Information Model** (CIM) data
models the catalogue uses, with use-case counts so you can see where
the catalogue is dense vs sparse.

Audience: Splunk admins planning data onboarding, detection engineers
deciding which CIM model to target, content authors picking the right
model when writing a new UC, integrators consuming the recommender
API.

For the *concept* of CIM and OCSF / data-model acceleration (DMA), read
[CIM, DMA, and OCSF](cim-and-data-models.md). For the per-UC field
contract, see [Use Case Field Reference](use-case-fields.md).

## Coverage at a glance

The catalogue contains 7,300+ use cases across 39 distinct CIM model
references. The numbers in the table below are a representative
snapshot — the live, authoritative numbers are in
[`api/v1/recommender/cim-index.json`](api-docs-guide.md#recommender)
and `dist/metrics.json`.

| CIM model | UC count | Notes |
|---|---:|---|
| **`Endpoint`** (incl. sub-models like `Endpoint.Processes`, `Endpoint.Filesystem`) | ~560 | EDR, agent-based detection, host telemetry. |
| **`Change`** (incl. `Change.All_Changes`) | ~540 | Config drift, audit log entries, change-management. |
| **`Authentication`** | ~423 | AD, SSO, MFA, RDP, SSH, PAM, federation. |
| **`Performance`** (incl. `.CPU`, `.Memory`, `.Storage`) | ~330 | Capacity, saturation, golden signals. |
| **`Alerts`** | ~302 | Already-detected alerts from upstream tools. |
| **`Network_Traffic`** (incl. `.All_Traffic`) | ~190 | Firewalls, NetFlow, Zeek, packet capture. |
| **`Web`** | ~119 | Proxies, CDN, web servers, application logs. |
| **`Vulnerabilities`** | ~98 | Qualys, Tenable, Rapid7, Snyk. |
| **`Inventory`** (incl. `Compute_Inventory`) | ~100 | CMDB, asset databases, hardware lifecycle. |
| **`Intrusion_Detection`** | ~89 | IDS/IPS appliances, Suricata, Snort. |
| **`Application_State`** | ~85 | Service health, status pages, synthetic checks. |
| **`Risk`** | ~81 | Splunk ES Risk-Based Alerting. |
| **`Email`** | ~40 | Mail flow, spam, DLP, Microsoft 365 / Google Workspace. |
| **`Network_Resolution`** (incl. `.DNS`) | ~44 | DNS query / response, recursive resolvers. |
| **`Network_Sessions`** (incl. `.DHCP`) | ~28 | DHCP, IPAM, session tracking. |
| **`Malware`** | ~15 | AV, EDR malware verdicts, sandboxes. |
| **`Certificates`** | ~9 | PKI, CT logs, Venafi, internal CAs. |
| **`DLP`** | ~7 | Data loss prevention. |
| **`Updates`** | ~6 | Patch management, WSUS, Intune. |
| **`Splunk_Audit`** | ~6 | Self-monitoring of Splunk itself. |
| **`Ticket_Management`** | ~2 | ServiceNow, Jira ITSM events. |
| **`Databases`** | ~1 | DB Connect events. |
| **`Capacity`** | ~1 | Capacity-planning model. |
| **`ITSI_KPI_Summary`** | ~1 | ITSI summary index. |

UCs marked **`N/A`** (~3,200) intentionally don't map to a CIM model —
typically because they consume raw events that have no canonical CIM
model (e.g. proprietary OT protocols, third-party SaaS audit logs,
custom telemetry).

## How CIM is encoded on a UC

In the per-UC sidecar:

```json
{
  "id": "9.6.4",
  "title": "Brute force against AD over RDP",
  "cimModels": ["Authentication", "Network_Traffic"]
}
```

Rules:

- The field is an **array of CIM model name strings**.
- Sub-models are written with dot notation: `Endpoint.Processes`.
- A UC can carry multiple CIM models when its SPL spans models — for
  example detecting a brute force attack from authentication events
  *and* the source IP from network events.
- Use **`N/A`** when the data is genuinely outside CIM (raw OT
  telemetry, SaaS audit logs, proprietary formats).
- Always pair `cimModels` with a `cimSpl` (tstats-driven) variant of
  the SPL when the data is CIM-compliant. See [CIM, DMA, and OCSF](cim-and-data-models.md).

The schema reference is in
[`schemas/uc.schema.json`](../schemas/uc.schema.json).

## Filtering the catalogue by CIM

Three ways:

1. **CIM filter dropdown** in the catalogue's advanced filter strip
   — searchable, multi-select.
2. **URL hash** — `index.html#cim=Authentication` or
   `#cim=Authentication,Network_Traffic` for multi-select.
3. **API** — `GET /api/v1/recommender/cim-index.json` returns the
   reverse index (CIM model → UC list) directly.

## Recommender app

The [Splunk UC Recommender](recommender-app.md) consumes
`api/v1/recommender/cim-index.json` as its primary source of truth for
"what CIM models are flowing in your Splunk?" and matches them to UCs
in the catalogue. It will:

1. Scan your local CIM-accelerated data models (via tstats).
2. Build a **detected CIM model list** for your environment.
3. Match it against this index and surface the highest-scoring UCs.

This is often the fastest way to discover *which catalogue UCs your
environment can run today*.

## Data-model acceleration (DMA) hints

For UCs that benefit from a CIM-accelerated query, the per-UC sidecar
carries the `dataModelAcceleration` (`dma`) field with one of:

- `required` — the UC will not run without DMA.
- `recommended` — DMA gives a substantial speedup but the UC works
  without it.
- `optional` — DMA gives a marginal speedup.
- `n/a` — the UC doesn't query CIM-accelerated data.

The catalogue surfaces this in the UC detail panel and is filterable
through the **DMA** advanced filter.

## CIM compliance for ingest

If you're onboarding a new data source that you expect to detect with
catalogue UCs:

1. Identify the **target CIM model** for the data source.
2. Map the source's fields to the CIM model's required fields (use
   `props.conf` `FIELDALIAS-*` and `EVAL-*`).
3. Tag the source with the model's eventtypes (`eventtypes.conf`).
4. Test with `| datamodel <Model> All_<Model> search` and the
   [SA-cim_vladiator](https://splunkbase.splunk.com/app/2968) app.
5. Accelerate the data model so tstats-driven UCs can run.

For implementation detail and `props.conf` recipes, see the
[Splunk-side configuration](implementation-guide.md) doc and the
domain-specific guides under [`docs/guides/`](guides/).

## Anti-patterns to avoid

- **Mis-mapping** — don't tag a UC with a CIM model whose fields it
  doesn't actually use. The catalogue's audit (`python -m splunk_uc
  audit-cim`) catches obvious cases but not all.
- **Over-mapping** — listing every model the SPL *touches* obscures
  the primary signal. List the model that drives the detection.
- **Ignoring sub-models** — if your detection genuinely targets
  `Endpoint.Processes`, tag it that way rather than the broader
  `Endpoint`. Sub-models give the recommender finer reach.

## Future direction: OCSF

Splunk is migrating long-term toward **OCSF** (Open Cybersecurity
Schema Framework) as a parallel normalisation. The catalogue does
**not** carry OCSF tags today; the field contract for OCSF in
[CIM, DMA, and OCSF](cim-and-data-models.md) describes the planned
shape. When OCSF lands as a `cimModels` peer (`ocsfClasses[]`), the
UC sidecars and this inventory will track.

## Where to go next

- [CIM, DMA, and OCSF](cim-and-data-models.md) — the conceptual primer.
- [Site User Guide](site-user-guide.md) — for the CIM filter and the
  CIM column in the detail panel.
- [API Docs page](api-docs-guide.md) — for `recommender/cim-index.json`
  and the rest of the API surface.
- [Recommender App](recommender-app.md) — for the in-Splunk consumer.
- [Use Case Field Reference](use-case-fields.md) — for the per-UC
  authoring contract.
- [Implementation Guide](implementation-guide.md) — for `props.conf`
  / `transforms.conf` patterns to make a source CIM-compliant.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Primary sources

<a id="ref-1"></a>**[1]** Splunk Inc. (2026). *Splunk Common Information Model Add-on Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/CIM

### Supporting sources

<a id="ref-2"></a>**[2]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-3"></a>**[3]** Splunk Inc. (2026). *Splunk Enterprise Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk

<a id="ref-4"></a>**[4]** Splunk Inc. (2026). *Splunk Enterprise Security Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ES

<a id="ref-5"></a>**[5]** Splunk Inc. (2026). *Splunk IT Service Intelligence Administration Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/ITSI

<a id="ref-6"></a>**[6]** Splunk Inc. (2026). *Splunkbase — the Splunk app marketplace*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://splunkbase.splunk.com/

<details>
<summary>Additional online sources cited in the document body (1)</summary>

<a id="ref-7"></a>**[7]** splunkbase.splunk.com. *SA-cim_vladiator*. Retrieved May 11, 2026, from https://splunkbase.splunk.com/app/2968

</details>

### Related repository documents

- [`docs/api-docs-guide.md`](api-docs-guide.md)
- [`docs/cim-and-data-models.md`](cim-and-data-models.md)
- [`docs/implementation-guide.md`](implementation-guide.md)
- [`docs/recommender-app.md`](recommender-app.md)
- [`docs/site-user-guide.md`](site-user-guide.md)
- [`docs/use-case-fields.md`](use-case-fields.md)

### Cited by

- [`docs/build-artefacts-reference.md`](build-artefacts-reference.md)
- [`docs/knowledge-graph-guide.md`](knowledge-graph-guide.md)
- [`docs/mitre-attack-mapping.md`](mitre-attack-mapping.md)
- [`docs/site-user-guide.md`](site-user-guide.md)

<!-- END-AUTOGENERATED-SOURCES -->
