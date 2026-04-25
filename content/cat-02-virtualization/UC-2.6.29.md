<!-- AUTO-GENERATED from UC-2.6.29.json — DO NOT EDIT -->

---
id: "2.6.29"
title: "Machine Catalog Image Pipeline Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.29 · Machine Catalog Image Pipeline Health

## Description

Machine Catalog health depends on current master images, successful preparation or rollout jobs, and timely rollouts. Stale images (>90 days without refresh), pending rollouts stuck in queue, and provisioning errors reduce pool reliability and can leave machines on vulnerable or non-compliant images. Polling the Monitor `MachineCatalog` OData feed gives a single place to see catalog-level status when broker events do not list every field.

## Value

Machine Catalog health depends on current master images, successful preparation or rollout jobs, and timely rollouts. Stale images (>90 days without refresh), pending rollouts stuck in queue, and provisioning errors reduce pool reliability and can leave machines on vulnerable or non-compliant images. Polling the Monitor `MachineCatalog` OData feed gives a single place to see catalog-level status when broker events do not list every field.

## Implementation

Enable OData collection for Machine Catalog. Align field names to your add-on; use `fieldalias` in `props.conf` if the vendor uses `LastImageTime` instead of `LastMasterImageTime`. Set thresholds: image age 90+ days, any non-empty pending rollout counter for more than 24 hours, and any `Fail` in provisioning. Join to change tickets for image updates. Cross-check MCS/PVS UCs for prep failures on the same image name.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Citrix Monitor Service OData API collector, Template for Citrix XenDesktop 7 (TA-XD7-Broker).
• Ensure the following data sources are available: `index=xd` `sourcetype="citrix:monitor:odata"` for `MachineCatalog`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll the Monitor service with appropriate auth; verify `ODataEntity` or equivalent identifies Machine Catalog records. Add aliases for time and pending-count fields. Optionally enrich with a CSV of image owners and patch cycles.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust field names to match your feed):

```spl
index=xd sourcetype="citrix:monitor:odata" (ODataEntity=MachineCatalog OR entity_type=MachineCatalog OR Name=*)
| eval master_age_days=if(isnotnull(LastImageUpdateTime) OR isnotnull(LastMasterImageTime), round((now()-coalesce(LastImageUpdateTime, LastMasterImageTime, _time)) / 86400, 1), null())
| eval rollout_pending=coalesce(PendingImageRollout, PendingUpdateCount, 0)
| where master_age_days > 90 OR rollout_pending > 0 OR match(coalesce(ProvisioningStatus, State, ErrorState), "(?i)fail|error")
| table _time, Name, ProvisioningType, master_age_days, rollout_pending, ProvisioningStatus, State, ErrorState, MasterImageVhd, host
| sort - master_age_days
```

Step 3 — Validate
Compare results to Citrix Studio for a few catalogs. Confirm the 90-day threshold against your image lifecycle policy. Test alert with a non-production catalog.

Step 4 — Operationalize
Send weekly report to desktop engineering; page on `Fail` states or age breaches over policy. Link dashboard rows to your image build pipeline and vulnerability scanning.

## SPL

```spl
index=xd sourcetype="citrix:monitor:odata" (ODataEntity=MachineCatalog OR entity_type=MachineCatalog OR Name=*)
| eval master_age_days=if(isnotnull(LastImageUpdateTime) OR isnotnull(LastMasterImageTime), round((now()-coalesce(LastImageUpdateTime, LastMasterImageTime, _time)) / 86400, 1), null())
| eval rollout_pending=coalesce(PendingImageRollout, PendingUpdateCount, 0)
| where master_age_days > 90 OR rollout_pending > 0 OR match(coalesce(ProvisioningStatus, State, ErrorState), "(?i)fail|error")
| table _time, Name, ProvisioningType, master_age_days, rollout_pending, ProvisioningStatus, State, ErrorState, MasterImageVhd, host
| sort - master_age_days
```

## Visualization

Table (catalogs at risk), Line chart (pending rollout trend), Single value (catalogs with stale images).

## References

- [Monitor Citrix with OData](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops-221/operations/monitor/odata-connector.html)
