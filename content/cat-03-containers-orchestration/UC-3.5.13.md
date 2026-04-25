<!-- AUTO-GENERATED from UC-3.5.13.json — DO NOT EDIT -->

---
id: "3.5.13"
title: "eBPF Network Observability (Cilium Hubble)"
criticality: "high"
splunkPillar: "Security"
---

# UC-3.5.13 · eBPF Network Observability (Cilium Hubble)

## Description

Traditional network monitoring in Kubernetes relies on service mesh sidecars or packet capture — both adding overhead and complexity. Cilium Hubble provides kernel-level L3/L4/L7 network visibility via eBPF without sidecar injection, capturing every network flow between pods, services, and external endpoints with near-zero performance impact. Ingesting Hubble flow logs into Splunk reveals unexpected service communication (security), DNS failures (availability), and packet drops (performance) that are invisible to application-level monitoring.

## Value

Traditional network monitoring in Kubernetes relies on service mesh sidecars or packet capture — both adding overhead and complexity. Cilium Hubble provides kernel-level L3/L4/L7 network visibility via eBPF without sidecar injection, capturing every network flow between pods, services, and external endpoints with near-zero performance impact. Ingesting Hubble flow logs into Splunk reveals unexpected service communication (security), DNS failures (availability), and packet drops (performance) that are invisible to application-level monitoring.

## Implementation

Deploy Cilium as the Kubernetes CNI with Hubble enabled. Hubble captures eBPF-level network flows including source/destination pod, namespace, identity, IP, port, protocol, L7 protocol details (HTTP method/path, DNS query/response, Kafka topic), verdict (forwarded/dropped), and drop reason. Export Hubble flows to Splunk via the OTel Collector's Hubble receiver or by relaying Hubble's gRPC stream to a log pipeline. Key detections: dropped flows indicate network policy violations or misconfigurations; unexpected destination identities signal lateral movement or misconfigured services; DNS failures (NXDOMAIN, timeout) from Hubble's DNS-aware L7 parsing reveal resolution issues before they cascade. Correlate dropped flows with Cilium network policies to identify which policy blocked the traffic. Track flow volume per namespace to detect traffic anomalies.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Distribution of OpenTelemetry Collector (Hubble receiver), Cilium Hubble.
• Ensure the following data sources are available: `sourcetype=cilium:hubble:flows`, Hubble flow logs via OTLP or gRPC relay.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy Cilium as the Kubernetes CNI with Hubble enabled. Hubble captures eBPF-level network flows including source/destination pod, namespace, identity, IP, port, protocol, L7 protocol details (HTTP method/path, DNS query/response, Kafka topic), verdict (forwarded/dropped), and drop reason. Export Hubble flows to Splunk via the OTel Collector's Hubble receiver or by relaying Hubble's gRPC stream to a log pipeline. Key detections: dropped flows indicate network policy violations or misconfigurati…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=containers sourcetype="cilium:hubble:flows"
| eval flow_direction=case(
    traffic_direction=="INGRESS", "Inbound",
    traffic_direction=="EGRESS", "Outbound",
    1==1, "Unknown")
| eval flow_status=case(
    verdict=="FORWARDED", "Allowed",
    verdict=="DROPPED", "Dropped",
    verdict=="AUDIT", "Audited",
    1==1, verdict)
| bin _time span=5m
| stats count as flows, sum(eval(if(verdict=="DROPPED",1,0))) as dropped, dc(destination_identity) as unique_destinations by _time, source_namespace, source_pod, destination_namespace, flow_direction
| eval drop_pct=round(dropped*100/flows, 2)
| where dropped > 0 OR unique_destinations > 50
| table _time, source_namespace, source_pod, destination_namespace, flow_direction, flows, dropped, drop_pct, unique_destinations
| sort -dropped
```

Understanding this SPL

**eBPF Network Observability (Cilium Hubble)** — Traditional network monitoring in Kubernetes relies on service mesh sidecars or packet capture — both adding overhead and complexity. Cilium Hubble provides kernel-level L3/L4/L7 network visibility via eBPF without sidecar injection, capturing every network flow between pods, services, and external endpoints with near-zero performance impact. Ingesting Hubble flow logs into Splunk reveals unexpected service communication (security), DNS failures (availability), and packet…

Documented **Data sources**: `sourcetype=cilium:hubble:flows`, Hubble flow logs via OTLP or gRPC relay. **App/TA** (typical add-on context): Splunk Distribution of OpenTelemetry Collector (Hubble receiver), Cilium Hubble. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: containers; **sourcetype**: cilium:hubble:flows. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=containers, sourcetype="cilium:hubble:flows". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **flow_direction** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **flow_status** — often to normalize units, derive a ratio, or prepare for thresholds.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, source_namespace, source_pod, destination_namespace, flow_direction** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **drop_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where dropped > 0 OR unique_destinations > 50` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **eBPF Network Observability (Cilium Hubble)**): table _time, source_namespace, source_pod, destination_namespace, flow_direction, flows, dropped, drop_pct, unique_destinations
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. For Kubernetes and OpenShift data, sample rows should line up with what you see from the cluster command-line tool, the Kubernetes Dashboard (or OpenShift console), and your Splunk Add-on for Kubernetes (`Splunk_TA_kubernetes`) or OpenTelemetry collector view of the same objects. Compare with known good and bad scenarios where you have them. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Sankey diagram (namespace-to-namespace traffic flow), Table (dropped flows with source/destination), Line chart (flow volume and drop rate over 24 hours), Bar chart (top drop reasons), Network graph (pod communication map).

## SPL

```spl
index=containers sourcetype="cilium:hubble:flows"
| eval flow_direction=case(
    traffic_direction=="INGRESS", "Inbound",
    traffic_direction=="EGRESS", "Outbound",
    1==1, "Unknown")
| eval flow_status=case(
    verdict=="FORWARDED", "Allowed",
    verdict=="DROPPED", "Dropped",
    verdict=="AUDIT", "Audited",
    1==1, verdict)
| bin _time span=5m
| stats count as flows, sum(eval(if(verdict=="DROPPED",1,0))) as dropped, dc(destination_identity) as unique_destinations by _time, source_namespace, source_pod, destination_namespace, flow_direction
| eval drop_pct=round(dropped*100/flows, 2)
| where dropped > 0 OR unique_destinations > 50
| table _time, source_namespace, source_pod, destination_namespace, flow_direction, flows, dropped, drop_pct, unique_destinations
| sort -dropped
```

## Visualization

Sankey diagram (namespace-to-namespace traffic flow), Table (dropped flows with source/destination), Line chart (flow volume and drop rate over 24 hours), Bar chart (top drop reasons), Network graph (pod communication map).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
