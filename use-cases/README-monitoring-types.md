# Assigning correct Monitoring type to use cases

Each use case has a **Monitoring type** subcategory (e.g. Availability, Performance, Security) used for filtering in the dashboard. Types are stored in the markdown and in `data.js`.

## How assignment works

1. **EXPLICIT_CORRECT** — In `monitoring_type_overrides.py`, the `EXPLICIT_CORRECT` dict holds the **per-UC reviewed** correct type for use cases where rule-based inference would be wrong. This list was built by going through each use case and double-checking title + value.
2. **OVERRIDES** — Legacy/additional overrides (uc_id → type) in the same file.
3. **NETWORK_TYPE_BY_UC** — Full explicit mapping for Network use cases 5.1.1–5.8.8.
4. **Inference** — For any UC not in the above, `build_monitoring_type_mapping.py` uses **value** first (compliance, security, availability, fault, capacity, configuration, anomaly), then **title** keywords. Value wins when it strongly suggests Compliance, Fault, Security, Configuration, or Availability.

## Correcting a use case

1. Open **`use-cases/monitoring_type_overrides.py`**.
2. Add or edit an entry in **`EXPLICIT_CORRECT`** (preferred) or **`OVERRIDES`**, e.g. `"1.1.42": "Fault"`.
3. Rebuild the mapping and apply to markdown:
   ```bash
   cd use-cases
   python3 build_monitoring_type_mapping.py
   python3 apply_monitoring_types_to_md.py
   ```
4. Regenerate the dashboard data:
   ```bash
   cd ..
   python3 build.py
   ```

## Files

| File | Purpose |
|------|--------|
| `uc_list.json` | Extracted (uc_id, title, value) from all cat-*.md. Regenerate with `extract_uc_list.py`. |
| `monitoring_type_overrides.py` | OVERRIDES and NETWORK_TYPE_BY_UC. Edit to fix wrong types. |
| `build_monitoring_type_mapping.py` | Builds `monitoring_type_mapping.json` from uc_list + overrides + inference. |
| `monitoring_type_mapping.json` | Final uc_id → type. Consumed by apply script. |
| `apply_monitoring_types_to_md.py` | Replaces `- **Monitoring type:**` in each UC block in cat-*.md. |

## Monitoring type values

- **Availability** — up/down, health, failover, uptime  
- **Performance** — utilization, latency, throughput, errors, response time  
- **Security** — ACL, auth failures, threats, IDS/IPS, policy violations  
- **Configuration** — config/policy change, drift, audit  
- **Capacity** — exhaustion, trending, capacity planning, queue depth  
- **Fault** — environmental, power, hardware failure, crash, OOM  
- **Anomaly** — flapping, instability, anomalous patterns  
- **Compliance** — audit trail, backup compliance, posture  

You can use a single type or two comma-separated (e.g. `"Performance, Capacity"`).
