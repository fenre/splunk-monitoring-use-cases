# External-Link Backlog (Batch 12 deferral)

_Generated 2026-05-09 from `reports/guide-external-links.json`._

Batch 12 (2026-05-09) ran a full external link audit on every guide
under `docs/guides/`. The 11 broken `docs.splunk.com` URLs were
replaced with their closest live parent landing pages. The
`.link-check-ignore` was extended with 25+ entries for bot-blocked
domains and OAuth/API endpoints that 401/403/405 by design.

This file lists the work that was **deferred**, grouped by category,
so a future targeted batch can pick it up without re-running the
full audit.

## A. Splunkbase app IDs returning 404 (29)

These app IDs no longer exist on Splunkbase. Each needs:

1. Look up the app in `data/splunkbase-deprecated.json` (if tracked).
2. Check Splunkbase for a successor app (most TAs were renamed or
   superseded — e.g. legacy single-purpose TAs replaced by a unified
   vendor TA).
3. Either update the URL to the successor's app ID, or replace the
   citation with a sentence explaining the app was withdrawn.

- `https://splunkbase.splunk.com/app/1378`
  - in: third-party-monitoring.md
- `https://splunkbase.splunk.com/app/1622`
  - in: application-availability-caching.md, telco-service-provider-networking.md
- `https://splunkbase.splunk.com/app/1645`
  - in: cisco-ise.md
- `https://splunkbase.splunk.com/app/1759`
  - in: network-flow.md
- `https://splunkbase.splunk.com/app/1851`
  - in: third-party-monitoring.md
- `https://splunkbase.splunk.com/app/1922`
  - in: edge-security-microsegmentation.md
- `https://splunkbase.splunk.com/app/1944`
  - in: third-party-monitoring.md
- `https://splunkbase.splunk.com/app/2785`
  - in: relational-databases.md
- `https://splunkbase.splunk.com/app/2823`
  - in: f5-bigip.md
- `https://splunkbase.splunk.com/app/2845`
  - in: telco-service-provider-networking.md
- `https://splunkbase.splunk.com/app/2849`
  - in: devops-cicd.md
- `https://splunkbase.splunk.com/app/2887`
  - in: web-security.md
- `https://splunkbase.splunk.com/app/2898`
  - in: collaboration-iot-monitoring.md
- `https://splunkbase.splunk.com/app/2950`
  - in: application-monitoring.md
- `https://splunkbase.splunk.com/app/2980`
  - in: application-monitoring.md
- `https://splunkbase.splunk.com/app/3068`
  - in: relational-databases.md
- `https://splunkbase.splunk.com/app/3203`
  - in: nosql-cloud-databases.md
- `https://splunkbase.splunk.com/app/3217`
  - in: gcp.md
- `https://splunkbase.splunk.com/app/3303`
  - in: container-platforms-docker-openshift.md
- `https://splunkbase.splunk.com/app/3441`
  - in: ids-ips.md
- `https://splunkbase.splunk.com/app/3724`
  - in: storage-backup.md
- `https://splunkbase.splunk.com/app/4105`
  - in: compliance-business.md
- `https://splunkbase.splunk.com/app/4500`
  - in: cloud-monitoring.md
- `https://splunkbase.splunk.com/app/4521`
  - in: third-party-monitoring.md
- `https://splunkbase.splunk.com/app/4533`
  - in: third-party-monitoring.md
- `https://splunkbase.splunk.com/app/4945`
  - in: industry-verticals.md, iot-ot.md
- `https://splunkbase.splunk.com/app/4955`
  - in: collaboration-iot-monitoring.md
- `https://splunkbase.splunk.com/app/5099`
  - in: identity-platforms-pam-sso.md
- `https://splunkbase.splunk.com/app/5275`
  - in: identity-platforms-pam-sso.md

## B. Vendor / standards docs returning 404 / 5xx (40)

Each URL needs the canonical current location looked up (vendor
doc moves, NIST publication renames, blog migrations, etc.) and the
source guide updated.

- `https://api-us.cloud.com/casanalyticsapi/v1/risk-indicators` — HEAD 404
  - in: citrix-virtual-apps-desktops.md
- `https://api-us.cloud.com/casanalyticsapi/v1/sessions` — HEAD 404
  - in: citrix-virtual-apps-desktops.md
- `https://api-us.cloud.com/cctrustoauth2/` — HEAD 404
  - in: citrix-virtual-apps-desktops.md
- `https://api.abuseipdb.com/taxii/api1/services/discovery` — HEAD 404
  - in: siem-soar.md
- `https://api.crowdstrike.com` — HEAD 404
  - in: edr.md
- `https://api.datadoghq.com/api/v1/events` — HEAD 404
  - in: third-party-monitoring.md
- `https://api.github.com/enterprises/contoso/copilot/usage` — HEAD 404
  - in: ai-llm-observability.md
- `https://app.datadoghq.com/monitors/` — HEAD 404
  - in: third-party-monitoring.md
- `https://aws.amazon.com/architecture/well-architected/lenses/` — HEAD 404
  - in: cloud-monitoring.md
- `https://cassandra.apache.org/doc/latest/cassandra/operating/audit_logging.html` — HEAD 404
  - in: nosql-cloud-databases.md
- `https://cloud.google.com/logging/docs/routing/pubsub` — HEAD 404
  - in: gcp.md
- `https://csrc.nist.gov/publications/detail/sp/800-53/rev-5` — HEAD 404
  - in: compliance-business.md, infrastructure-monitoring.md
- `https://csrc.nist.gov/publications/detail/sp/800-82/rev-3/final` — HEAD 404
  - in: collaboration-iot-monitoring.md
- `https://cway.cisco.com/mnemonics/` — HEAD 404
  - in: cisco-networks.md
- `https://developer.broadcom.com/xapis/vsphere-management-sdk/latest/` — HEAD 404
  - in: vmware-vsphere.md
- `https://developer.cisco.com/docs/thousandeyes/get-tests-via-opentelemetry/` — HEAD 404
  - in: cisco-thousandeyes.md
- `https://docs.cilium.io/en/stable/observability/hubble/exporters/` — HEAD 404
  - in: datacenter-fabric-sdn.md
- `https://docs.microsoft.com/en-us/system-center/scom/manage-mp-applications` — HEAD 404
  - in: third-party-monitoring.md
- `https://docs.paloaltonetworks.com/pan-os/latest/pan-os-admin/monitoring/use-syslog-for-monitoring/syslog-field-descriptions.html` — HEAD 404
  - in: firewalls.md
- `https://docs.thousandeyes.com/product-documentation/integrations/integrations-and-api-clients/stream-api` — HEAD 404
  - in: cisco-thousandeyes.md
- `https://docs.thousandeyes.com/product-documentation/internet-and-wan-monitoring/tests/routing-tests/bgp-test` — HEAD 404
  - in: cisco-thousandeyes.md
- `https://insights-api.newrelic.com/v1/accounts/` — HEAD 404
  - in: third-party-monitoring.md
- `https://knowledge.broadcom.com/external/article/345077` — HEAD 404
  - in: vmware-vsphere.md
- `https://opentelemetry.io/docs/specs/semconv/gen-ai/llm-metrics/` — HEAD 404
  - in: ai-llm-observability.md
- `https://opentelemetry.io/docs/specs/semconv/gen-ai/llm-spans/` — HEAD 404
  - in: ai-llm-observability.md
- `https://support.purestorage.com/Solutions/REST_API` — HEAD 404
  - in: storage-backup.md
- `https://techdocs.broadcom.com/us/en/vmware-cis/nsx/vmware-nsx/4-2/api-reference.html` — HEAD 404
  - in: datacenter-fabric-sdn.md
- `https://www.ashrae.org/technical-resources/standards-and-guidelines/standards-addenda/standard-188-2015` — HEAD 404
  - in: collaboration-iot-monitoring.md
- `https://www.axelos.com/best-practice-solutions/itil` — HEAD 404
  - in: application-monitoring.md, compliance-business.md
- `https://www.cisecurity.org/benchmark/google_cloud` — HEAD 404
  - in: cloud-monitoring.md
- `https://www.coso.org/erm` — HEAD 404
  - in: compliance-business.md
- `https://www.first.org/epss/data/` — HEAD 404
  - in: vulnerability-management.md
- `https://www.ifrs.org/issb/` — HEAD 404
  - in: compliance-business.md
- `https://www.splunk.com/en_us/blog/learn/security-research.html` — HEAD 404
  - in: siem-soar.md
- `https://www.splunk.com/en_us/products/apm.html` — HEAD 404
  - in: api-gateways.md
- `https://www.splunk.com/en_us/products/pricing/workload-pricing-faqs.html` — HEAD 404
  - in: finops-cost-capacity.md
- `https://www.splunk.com/en_us/products/splunk-edge-hub.html` — HEAD 404
  - in: iot-ot.md
- `https://www.theiia.org/three-lines-model` — HEAD 404
  - in: compliance-business.md
- `https://www.tsa.gov/news/press/releases/pipeline-security-directives` — HEAD 404
  - in: industry-verticals.md
- `https://www.weave.works/blog/the-red-method-key-metrics-for-microservices-architecture/` — HEAD 404
  - in: splunk-observability-cloud.md

## How to drive this backlog

```bash
# Re-run the audit any time to refresh the source data:
python3 scripts/audit_guide_external_links_oneshot.py

# After fixing a URL, re-run to confirm it's no longer in the report:
python3 scripts/audit_guide_external_links_oneshot.py 2>&1 | grep -F '<url>'
```

When this list is empty, delete the file. Until then, treat it as
the working queue for future docs-freshness batches.
