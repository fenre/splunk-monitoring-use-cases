# Fabric pilot grades

Independent grade of the enrichment pilot. Debatable counts as a miss.
Precision is correct / (correct + debatable + wrong).
The sample is 30 use cases per field, and every value on those use cases is graded.
loose-1 is the first pass. strict-1 is what was written.
When strict-1 filled fewer than 30 pilot use cases for a field, the sample continues through the catalogue in path order.

A value is correct only when a skeptical reader would keep the label.
Stock closers (`SOC SLA breaches`, `audit findings, regulatory gaps`, `shortens cloud incident response`, `defensible audit evidence`, `expands credential and network attack surface`) are wrong.
A sourcetype is correct only when the search the use case runs names it.
Troubleshooting `sourcetype=splunkd` and sibling feeds in a data-source list are wrong.
`Cross-industry` is a bucket, not an industry.
ESCU, syslog, and the word Splunk are debatable vendor products.
Generic tokens such as `pipeline` and `windows` are wrong.

Every field missed its bar, so the six lists were removed from the sidecars.
`proposedValues` notes were kept. Deterministic fabric edges from sidecar facts were not touched.

## Precision

| Field | Bar | Before (loose-1) | After (strict-1) | After sample | Result |
|---|---:|---:|---:|---|---|
| businessOutcomes | 85% | 18.64% (11/59) | 70.59% (24/34) | 30 use cases, 24 correct, 0 debatable, 10 wrong | missed |
| businessAreas | 90% | 7.53% (7/93) | 16.13% (5/31) | 30 use cases, 5 correct, 8 debatable, 18 wrong | missed |
| personas | 85% | 13.56% (8/59) | 70.00% (21/30) | 30 use cases, 21 correct, 7 debatable, 2 wrong | missed |
| industries | 90% | 34.29% (12/35) | 83.33% (25/30) | 30 use cases, 25 correct, 5 debatable, 0 wrong | missed |
| sourcetypes | 90% | 11.11% (20/180) | 74.24% (49/66) | 30 use cases, 49 correct, 0 debatable, 17 wrong | missed |
| vendorProducts | 90% | 18.29% (30/164) | 66.67% (46/69) | 30 use cases, 46 correct, 14 debatable, 9 wrong | missed |

## businessOutcomes (loose-1)

| UC | Value | Evidence | Grade | Reason |
|---|---|---|---|---|
| 1.1.4 Disk I/O Saturation (Linux) | `improve_service_reliability` | latency | debatable | the phrase occurs, but it is too broad to settle the label |
| 1.1.4 Disk I/O Saturation (Linux) | `faster_incident_response` | triage | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `control_privileged_access` | privileged account | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `faster_incident_response` | incident response | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `reduce_downtime` | Availability | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `contain_threats` | containment | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `lower_security_risk` | compromise | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `reduce_downtime` | Availability | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `improve_service_reliability` | latency | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `reduce_downtime` | availability | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.114 Unapproved VM-Read Access to LSASS | `contain_threats` | isolate the host | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.114 Unapproved VM-Read Access to LSASS | `faster_incident_response` | triage | debatable | the phrase occurs, but it is too broad to settle the label |
| 1.2.61 Windows Data Deduplication Job Health | `improve_service_reliability` | latency | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.59 Network Team Failover Detection (Linux) | `reduce_downtime` | Availability | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.59 Network Team Failover Detection (Linux) | `improve_service_reliability` | latency | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `improve_service_reliability` | service health | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `reduce_downtime` | availability | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `contain_threats` | containment | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `faster_incident_response` | triage | debatable | the phrase occurs, but it is too broad to settle the label |
| 2.6.46 Citrix Monitor OData Load Index Trending | `faster_incident_response` | triage | debatable | the phrase occurs, but it is too broad to settle the label |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `improve_service_reliability` | Error Rate | correct | the title names this phrase, and the sentence is not a stock closer |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `reduce_downtime` | Availability | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `faster_incident_response` | triage | debatable | the phrase occurs, but it is too broad to settle the label |
| 2.6.32 Hypervisor Connection Health Monitoring | `reduce_downtime` | Availability | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.2.2 Hyper-V Replication Health | `reduce_downtime` | Availability | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `reduce_downtime` | Availability | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `contain_threats` | containment | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `faster_incident_response` | Triage | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `faster_incident_response` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `reduce_downtime` | availability | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `improve_service_reliability` | Latency | correct | the title names this phrase, and the sentence is not a stock closer |
| 3.1.23 Container Network I/O Anomalies | `faster_incident_response` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 3.1.23 Container Network I/O Anomalies | `lower_security_risk` | compromise | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.1.23 Container Network I/O Anomalies | `improve_service_reliability` | latency | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.1.1 Container Crash Loops | `faster_incident_response` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 3.1.1 Container Crash Loops | `improve_service_reliability` | latency | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.5.7 Envoy Proxy Error Rates | `faster_incident_response` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 3.5.7 Envoy Proxy Error Rates | `reduce_downtime` | Availability | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.5.7 Envoy Proxy Error Rates | `improve_service_reliability` | Error Rate | correct | the title names this phrase, and the sentence is not a stock closer |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `faster_incident_response` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `reduce_downtime` | Availability | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `improve_service_reliability` | latency | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.4.5 Registry Authentication and Authorization Failures | `faster_incident_response` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `faster_incident_response` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `reduce_downtime` | availability | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `improve_service_reliability` | latency | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.4.1 Image Push/Pull Audit | `faster_incident_response` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 3.4.1 Image Push/Pull Audit | `improve_change_safety` | change management | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.4.1 Image Push/Pull Audit | `lower_security_risk` | compromise | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.3.27 Cloud Armor WAF Events | `improve_change_safety` | change window | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.1.320 AWS CloudTrail IAM user listing | `improve_change_safety` | change window | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.3.106 GCP Global forwarding rule create | `lower_security_risk` | attack surface | wrong | the phrase sits in a sentence pasted across many use cases |
| 4.3.106 GCP Global forwarding rule create | `improve_change_safety` | change window | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `improve_change_safety` | change window | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `lower_security_risk` | attack surface | wrong | the phrase sits in a sentence pasted across many use cases |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `improve_change_safety` | change window | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `faster_incident_response` | incident response | wrong | the phrase sits in a sentence pasted across many use cases |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `prove_compliance` | audit evidence | wrong | the phrase sits in a sentence pasted across many use cases |
| 4.3.90 GCP Compute metadata change | `improve_change_safety` | change window | wrong | the evidence is not in the title, description, value, or plain-language explanation |

## businessAreas (loose-1)

| UC | Value | Evidence | Grade | Reason |
|---|---|---|---|---|
| 1.1.4 Disk I/O Saturation (Linux) | `compliance_and_risk` | regulatory | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.4 Disk I/O Saturation (Linux) | `application_performance` | latency | debatable | the phrase occurs, but it is too broad to settle the label |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `identity_and_access` | authentication failure | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `compliance_and_risk` | compliance | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `cost_and_capacity` | capacity | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `security_operations` | SOC  | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `data_protection` | data protection | wrong | data protection is the tail of stale-data protection |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `application_performance` | latency | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.114 Unapproved VM-Read Access to LSASS | `security_operations` | security operations | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.114 Unapproved VM-Read Access to LSASS | `cost_and_capacity` | capacity | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.114 Unapproved VM-Read Access to LSASS | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.61 Windows Data Deduplication Job Health | `compliance_and_risk` | regulatory | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.61 Windows Data Deduplication Job Health | `infrastructure_operations` | disk space | debatable | the phrase occurs, but it is too broad to settle the label |
| 1.2.61 Windows Data Deduplication Job Health | `cost_and_capacity` | capacity | debatable | the phrase occurs, but it is too broad to settle the label |
| 1.2.61 Windows Data Deduplication Job Health | `application_performance` | latency | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.61 Windows Data Deduplication Job Health | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.59 Network Team Failover Detection (Linux) | `network_operations` | network operations | correct | the sentence is about this use case and the phrase is specific |
| 1.1.59 Network Team Failover Detection (Linux) | `compliance_and_risk` | regulatory | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.59 Network Team Failover Detection (Linux) | `application_performance` | latency | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `data_protection` | personal data | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `compliance_and_risk` | compliance | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `cost_and_capacity` | capacity | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `compliance_and_risk` | Compliance | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `cost_and_capacity` | capacity | debatable | the phrase occurs, but it is too broad to settle the label |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `security_operations` | SOC  | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.46 Citrix Monitor OData Load Index Trending | `compliance_and_risk` | regulatory | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.46 Citrix Monitor OData Load Index Trending | `cost_and_capacity` | Capacity | debatable | the phrase occurs, but it is too broad to settle the label |
| 2.6.46 Citrix Monitor OData Load Index Trending | `security_operations` | SOC  | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `application_performance` | Error Rate | correct | the title names this phrase, and the sentence is not a stock closer |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `compliance_and_risk` | regulatory | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `cost_and_capacity` | capacity | debatable | the phrase occurs, but it is too broad to settle the label |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `security_operations` | SOC  | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `compliance_and_risk` | regulatory | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `cost_and_capacity` | capacity | debatable | the phrase occurs, but it is too broad to settle the label |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `security_operations` | SOC  | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `compliance_and_risk` | regulatory | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `cost_and_capacity` | capacity | debatable | the phrase occurs, but it is too broad to settle the label |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `security_operations` | SOC  | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.32 Hypervisor Connection Health Monitoring | `compliance_and_risk` | regulatory | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.32 Hypervisor Connection Health Monitoring | `cost_and_capacity` | capacity | debatable | the phrase occurs, but it is too broad to settle the label |
| 2.6.32 Hypervisor Connection Health Monitoring | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.32 Hypervisor Connection Health Monitoring | `security_operations` | SOC  | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.2.2 Hyper-V Replication Health | `compliance_and_risk` | regulatory | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.2.2 Hyper-V Replication Health | `cost_and_capacity` | capacity | debatable | the phrase occurs, but it is too broad to settle the label |
| 2.2.2 Hyper-V Replication Health | `security_operations` | SOC  | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `cost_and_capacity` | capacity | debatable | the phrase occurs, but it is too broad to settle the label |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `cloud_operations` | Kubernetes | correct | the title names this phrase, and the sentence is not a stock closer |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `cost_and_capacity` | Capacity | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `application_performance` | Latency | correct | the title names this phrase, and the sentence is not a stock closer |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.1.23 Container Network I/O Anomalies | `compliance_and_risk` | compliance | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.1.23 Container Network I/O Anomalies | `cost_and_capacity` | capacity | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.1.23 Container Network I/O Anomalies | `application_performance` | latency | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.1.23 Container Network I/O Anomalies | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.1.23 Container Network I/O Anomalies | `security_operations` | SOC  | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.1.1 Container Crash Loops | `cloud_operations` | Kubernetes | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.1.1 Container Crash Loops | `application_performance` | latency | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.1.1 Container Crash Loops | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.5.7 Envoy Proxy Error Rates | `application_performance` | Error Rate | correct | the title names this phrase, and the sentence is not a stock closer |
| 3.5.7 Envoy Proxy Error Rates | `cloud_operations` | Kubernetes | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.5.7 Envoy Proxy Error Rates | `compliance_and_risk` | regulatory | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.5.7 Envoy Proxy Error Rates | `security_operations` | SOC  | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `cloud_operations` | Kubernetes | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `cost_and_capacity` | Capacity | correct | the title names this phrase, and the sentence is not a stock closer |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `application_performance` | latency | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.4.5 Registry Authentication and Authorization Failures | `identity_and_access` | authentication failure | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.4.5 Registry Authentication and Authorization Failures | `cloud_operations` | Kubernetes | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.4.5 Registry Authentication and Authorization Failures | `compliance_and_risk` | Compliance | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.4.5 Registry Authentication and Authorization Failures | `security_operations` | SOC  | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `cloud_operations` | Kubernetes | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `compliance_and_risk` | compliance | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `cost_and_capacity` | Capacity | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `application_performance` | latency | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `network_operations` | routing | debatable | the phrase occurs, but it is too broad to settle the label |
| 3.4.1 Image Push/Pull Audit | `cloud_operations` | Kubernetes | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.4.1 Image Push/Pull Audit | `compliance_and_risk` | Compliance | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.4.1 Image Push/Pull Audit | `security_operations` | SOC  | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.3.27 Cloud Armor WAF Events | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.1.320 AWS CloudTrail IAM user listing | `cloud_operations` | CloudTrail | correct | the title names this phrase, and the sentence is not a stock closer |
| 4.1.320 AWS CloudTrail IAM user listing | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.3.106 GCP Global forwarding rule create | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `network_operations` | routing | wrong | the evidence is not in the title, description, value, or plain-language explanation |

## personas (loose-1)

| UC | Value | Evidence | Grade | Reason |
|---|---|---|---|---|
| 1.1.4 Disk I/O Saturation (Linux) | `service_owner` | service owner | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.4 Disk I/O Saturation (Linux) | `detection_engineer` | saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `incident_responder` | incident response | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `service_owner` | service owner | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `detection_engineer` | saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `detection_engineer` | saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.114 Unapproved VM-Read Access to LSASS | `detection_engineer` | saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.114 Unapproved VM-Read Access to LSASS | `incident_responder` | forensic | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.61 Windows Data Deduplication Job Health | `service_owner` | service owner | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.2.61 Windows Data Deduplication Job Health | `detection_engineer` | saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.59 Network Team Failover Detection (Linux) | `auditor` | control test | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.59 Network Team Failover Detection (Linux) | `detection_engineer` | saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `service_owner` | service owner | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `detection_engineer` | saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `service_owner` | service owner | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.46 Citrix Monitor OData Load Index Trending | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `service_owner` | service owner | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `service_owner` | service owner | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `service_owner` | service owner | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.32 Hypervisor Connection Health Monitoring | `service_owner` | service owner | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.6.32 Hypervisor Connection Health Monitoring | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.2.2 Hyper-V Replication Health | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `detection_engineer` | saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `incident_responder` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `platform_engineer` | platform engineer | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `service_owner` | service owner | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.1.23 Container Network I/O Anomalies | `incident_responder` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 3.1.23 Container Network I/O Anomalies | `service_owner` | service owner | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.1.23 Container Network I/O Anomalies | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.1.1 Container Crash Loops | `incident_responder` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 3.1.1 Container Crash Loops | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.5.7 Envoy Proxy Error Rates | `incident_responder` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 3.5.7 Envoy Proxy Error Rates | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `incident_responder` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `platform_engineer` | platform engineer | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `network_operator` | network engineer | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `cloud_operator` | cloud engineer | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.4.5 Registry Authentication and Authorization Failures | `detection_engineer` | correlation search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.4.5 Registry Authentication and Authorization Failures | `incident_responder` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `incident_responder` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `service_owner` | service owner | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `capacity_planner` | forecast | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 3.4.1 Image Push/Pull Audit | `incident_responder` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 3.4.1 Image Push/Pull Audit | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.1.320 AWS CloudTrail IAM user listing | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.3.106 GCP Global forwarding rule create | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `incident_responder` | incident response | wrong | the phrase sits in a sentence pasted across many use cases |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `auditor` | audit evidence | wrong | the phrase sits in a sentence pasted across many use cases |
| 4.3.90 GCP Compute metadata change | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |
| 4.13.24 Cloud Network Flow Anomaly HTTPS egress to rare ports | `detection_engineer` | Saved search | wrong | the evidence is not in the title, description, value, or plain-language explanation |

## industries (loose-1)

| UC | Value | Evidence | Grade | Reason |
|---|---|---|---|---|
| 5.4.6 RF Interference Events | `pipeline` | Pipeline | wrong | the evidence is not the industry field |
| 10.12.5 ACH Origination Anomalies | `financial-services` | Financial Services | correct | the industry field matches this registry name |
| 11.3.53 Pexip Conferencing Node Capacity and Load | `pipeline` | Pipeline | wrong | the evidence is not the industry field |
| 12.1.12 Repository Permission Changes | `pipeline` | Pipeline | wrong | the evidence is not the industry field |
| 12.2.9 Jenkins Executor Utilization | `pipeline` | Pipeline | wrong | the evidence is not the industry field |
| 13.7.12 Fluentd Hot-Reload Configuration Change Governance and Drift Detection | `pipeline` | Pipeline | wrong | the evidence is not the industry field |
| 17.1.59 Cisco ISE Logs through Splunk Edge Processor — Pipeline Health and Routing | `pipeline` | Pipeline | wrong | the evidence is not the industry field |
| 18.2.1 VMware NSX Distributed Firewall Rule-Hit Trending, Microsegmentation Effectiveness, and East-West Allow/Drop Visibility | `pipeline` | Pipeline | wrong | the evidence is not the industry field |
| 19.3.5 Windows Admin Center (WAC) Gateway Connection Telemetry and Administrative Action Audit | `pipeline` | Pipeline | wrong | the evidence is not the industry field |
| 19.1.10 Blade Firmware Compliance per FRU (Cisco UCS B-Series and X-Series) | `pipeline` | Pipeline | wrong | the evidence is not the industry field |
| 21.8.2 Core Network Element Health (MME, SGW, PGW) | `telecommunications` | Telecommunications | correct | the industry field matches this registry name |
| 21.3.20 DIPS Arena User Authentication and SSO Monitoring | `healthcare` | Healthcare | correct | the industry field matches this registry name |
| 21.12.23 Municipal smart city sensor outage | `public-sector-and-government` | Public Sector and Government | correct | the industry field matches this registry name |
| 21.5.37 Pipeline SCADA RTU firmware version drift | `oil-gas-and-mining` | Oil, Gas, and Mining | correct | the industry field matches this registry name |
| 21.5.37 Pipeline SCADA RTU firmware version drift | `pipeline` | Pipeline | wrong | the evidence is not the industry field |
| 21.10.29 Annuity surrender spike detection | `insurance-and-claims-processing` | Insurance and Claims Processing | correct | the industry field matches this registry name |
| 21.10.29 Annuity surrender spike detection | `insurance` | insurance | wrong | the evidence is not the industry field |
| 21.3.68 HIPAA workforce termination access revocation | `healthcare-and-life-sciences` | Healthcare and Life Sciences | correct | the industry field matches this registry name |
| 21.3.68 HIPAA workforce termination access revocation | `healthcare` | healthcare | wrong | the evidence is not the industry field |
| 21.5.44 Downhole gauge communication loss | `oil-gas-and-mining` | Oil, Gas, and Mining | correct | the industry field matches this registry name |
| 21.5.44 Downhole gauge communication loss | `pipeline` | pipeline | wrong | the evidence is not the industry field |
| 21.12.10 Higher-ed FERPA student record access audit | `public-sector-and-government` | Public Sector and Government | correct | the industry field matches this registry name |
| 22.55.7 CLC/TS 50701 Target Security Levels (SL-T) Coverage — every zone has an SL-T justified against threat scenarios | `transportation` | Transportation | correct | the industry field matches this registry name |
| 22.55.12 CLC/TS 50701 Rail Cybersecurity Incident Detection — rail-OT specific detection content covering signal, RBC, CBTC, GSM-R, FRMCS, rolling stock | `transportation` | Transportation | correct | the industry field matches this registry name |
| 23.9.3 Waste Diversion and Recycling Rate Tracking | `cross-industry` | Cross-industry | debatable | Cross-industry is a bucket, not an industry |
| 23.8.1 CEO/CFO Business Health Scorecard | `cross-industry` | Cross-industry | debatable | Cross-industry is a bucket, not an industry |
| 23.1.1 Website Conversion Funnel Analysis | `cross-industry` | Cross-industry | debatable | Cross-industry is a bucket, not an industry |
| 23.6.4 Payment Processing Success Rate and Revenue Leakage | `cross-industry` | Cross-industry | debatable | Cross-industry is a bucket, not an industry |
| 23.8.2 Operational Efficiency and Productivity Metrics | `cross-industry` | Cross-industry | debatable | Cross-industry is a bucket, not an industry |
| 24.8.33 Azure Data Factory Pipeline Freshness SLA | `pipeline` | Pipeline | wrong | the evidence is not the industry field |
| 10.7.519 Windows Event Logging Service Has Shutdown | `pipeline` | Pipeline | wrong | the evidence is not the industry field |
| 10.18.9 Broadcom Symantec CloudSOC Shadow IT Signals via DLP Cloud Destinations | `pipeline` | Pipeline | wrong | the evidence is not the industry field |
| 12.4.2 Configuration Drift Detection | `pipeline` | Pipeline | wrong | the evidence is not the industry field |
| 14.6.2 S7comm Program Upload/Download Detection | `manufacturing` | Manufacturing | correct | the industry field matches this registry name |
| 14.6.2 S7comm Program Upload/Download Detection | `pipeline` | Pipeline | wrong | the evidence is not the industry field |

## sourcetypes (loose-1)

| UC | Value | Evidence | Grade | Reason |
|---|---|---|---|---|
| 1.1.4 Disk I/O Saturation (Linux) | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.4 Disk I/O Saturation (Linux) | `device` | device | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.4 Disk I/O Saturation (Linux) | `completion` | completion | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.4 Disk I/O Saturation (Linux) | `dest` | dest | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.4 Disk I/O Saturation (Linux) | `name` | Name | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.4 Disk I/O Saturation (Linux) | `package` | package | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `wineventlog-security` | WinEventLog:Security | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `xmlwineventlog` | XmlWinEventLog | correct | the search the use case runs names this sourcetype |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `issue` | issue | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `scheduler` | scheduler | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `client` | client | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `xmlwineventlog` | XmlWinEventLog | correct | the search the use case runs names this sourcetype |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `issue` | issue | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `wineventlog` | WinEventLog | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `status` | status | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `status` | status | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `severity` | severity | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `interfaces` | interfaces | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `name` | Name | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `protocol` | PROTOCOL | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.114 Unapproved VM-Read Access to LSASS | `xmlwineventlog` | XmlWinEventLog | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.114 Unapproved VM-Read Access to LSASS | `scheduler` | scheduler | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.114 Unapproved VM-Read Access to LSASS | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.114 Unapproved VM-Read Access to LSASS | `client` | client | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.114 Unapproved VM-Read Access to LSASS | `wineventlog` | WinEventLog | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.114 Unapproved VM-Read Access to LSASS | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.61 Windows Data Deduplication Job Health | `issue` | issue | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.61 Windows Data Deduplication Job Health | `client` | client | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.61 Windows Data Deduplication Job Health | `wineventlog` | WinEventLog | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.61 Windows Data Deduplication Job Health | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.61 Windows Data Deduplication Job Health | `status` | status | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.61 Windows Data Deduplication Job Health | `cpu` | cpu | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.59 Network Team Failover Detection (Linux) | `splunkd` | splunkd | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.59 Network Team Failover Detection (Linux) | `syslog` | syslog | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.59 Network Team Failover Detection (Linux) | `scheduler` | scheduler | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.59 Network Team Failover Detection (Linux) | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.59 Network Team Failover Detection (Linux) | `status` | status | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.59 Network Team Failover Detection (Linux) | `props-conf` | props.conf | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `linux-journald` | linux:journald | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `compliance` | compliance | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `status` | status | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `user-id` | USER_ID | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `splunkd` | splunkd | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `compliance` | compliance | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `props-conf` | props.conf | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `severity` | severity | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.46 Citrix Monitor OData Load Index Trending | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.46 Citrix Monitor OData Load Index Trending | `citrix-monitor-odata` | citrix:monitor:odata | correct | the search the use case runs names this sourcetype |
| 2.6.46 Citrix Monitor OData Load Index Trending | `name` | Name | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.46 Citrix Monitor OData Load Index Trending | `named` | named | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.46 Citrix Monitor OData Load Index Trending | `package` | package | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.46 Citrix Monitor OData Load Index Trending | `httpevent` | httpevent | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `splunkd` | splunkd | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `status` | status | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `severity` | severity | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `instance-uuid` | instance_uuid | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `channel` | channel | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `splunkd` | splunkd | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `syslog` | syslog | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `citrix-broker-events` | citrix:broker:events | correct | the search the use case runs names this sourcetype |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `citrix-netscaler-syslog` | citrix:netscaler:syslog | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `citrix-monitor-odata` | citrix:monitor:odata | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `splunkd` | splunkd | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `syslog` | syslog | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `severity` | severity | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `channel` | channel | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `name` | Name | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `named` | named | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.32 Hypervisor Connection Health Monitoring | `splunkd` | splunkd | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.32 Hypervisor Connection Health Monitoring | `citrix-broker-events` | citrix:broker:events | correct | the search the use case runs names this sourcetype |
| 2.6.32 Hypervisor Connection Health Monitoring | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.32 Hypervisor Connection Health Monitoring | `severity` | severity | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.32 Hypervisor Connection Health Monitoring | `vcenter` | vcenter | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.32 Hypervisor Connection Health Monitoring | `channel` | channel | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.2.2 Hyper-V Replication Health | `wineventlog` | WinEventLog | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.2.2 Hyper-V Replication Health | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.2.2 Hyper-V Replication Health | `status` | status | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.2.2 Hyper-V Replication Health | `eventcode` | EventCode | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.2.2 Hyper-V Replication Health | `name` | Name | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.2.2 Hyper-V Replication Health | `named` | named | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `syslog` | syslog | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `issue` | issue | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `scheduler` | scheduler | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `client` | client | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `splunkd` | splunkd | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `prometheus-scrape-metrics` | prometheus:scrape:metrics | correct | the search the use case runs names this sourcetype |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `issue` | issue | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `scheduler` | scheduler | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `client` | client | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.1.23 Container Network I/O Anomalies | `docker-stats` | docker:stats | correct | the search the use case runs names this sourcetype |
| 3.1.23 Container Network I/O Anomalies | `client` | client | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.1.23 Container Network I/O Anomalies | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.1.23 Container Network I/O Anomalies | `compliance` | compliance | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.1.23 Container Network I/O Anomalies | `props-conf` | props.conf | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.1.23 Container Network I/O Anomalies | `severity` | severity | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.1.1 Container Crash Loops | `docker-stats` | docker:stats | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.1.1 Container Crash Loops | `splunkd` | splunkd | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.1.1 Container Crash Loops | `syslog` | syslog | correct | the search the use case runs names this sourcetype |
| 3.1.1 Container Crash Loops | `auditd` | auditd | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.1.1 Container Crash Loops | `linux-audit-2` | linux:audit | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.1.1 Container Crash Loops | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.5.7 Envoy Proxy Error Rates | `kube-events` | kube:events | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.5.7 Envoy Proxy Error Rates | `otel-metrics` | otel:metrics | correct | the search the use case runs names this sourcetype |
| 3.5.7 Envoy Proxy Error Rates | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.5.7 Envoy Proxy Error Rates | `client` | client | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.5.7 Envoy Proxy Error Rates | `envoy-stats` | envoy:stats | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.5.7 Envoy Proxy Error Rates | `status` | status | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `prometheus-metrics` | prometheus:metrics | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `k8s-events` | k8s_events | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `prometheus-metric` | prometheus:metric | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `status` | status | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.4.5 Registry Authentication and Authorization Failures | `kube-events` | kube:events | correct | the search the use case runs names this sourcetype |
| 3.4.5 Registry Authentication and Authorization Failures | `issue` | issue | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.4.5 Registry Authentication and Authorization Failures | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.4.5 Registry Authentication and Authorization Failures | `client` | client | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.4.5 Registry Authentication and Authorization Failures | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.4.5 Registry Authentication and Authorization Failures | `compliance` | compliance | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `kube-events` | kube:events | correct | the search the use case runs names this sourcetype |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `cp-log` | cp_log | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `kube-apiserver-audit` | kube:apiserver:audit | correct | the search the use case runs names this sourcetype |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `ocp-events` | ocp_events | correct | the search the use case runs names this sourcetype |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `ocp-audit` | ocp_audit | correct | the search the use case runs names this sourcetype |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `issue` | issue | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.4.1 Image Push/Pull Audit | `splunkd` | splunkd | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.4.1 Image Push/Pull Audit | `kube-events` | kube:events | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.4.1 Image Push/Pull Audit | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.4.1 Image Push/Pull Audit | `client` | client | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.4.1 Image Push/Pull Audit | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.4.1 Image Push/Pull Audit | `compliance` | compliance | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.3.27 Cloud Armor WAF Events | `google-gcp-pubsub-message` | google:gcp:pubsub:message | correct | the search the use case runs names this sourcetype |
| 4.3.27 Cloud Armor WAF Events | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.3.27 Cloud Armor WAF Events | `client` | client | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.3.27 Cloud Armor WAF Events | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.3.27 Cloud Armor WAF Events | `status` | status | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.3.27 Cloud Armor WAF Events | `props-conf` | props.conf | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.1.320 AWS CloudTrail IAM user listing | `aws-cloudtrail` | aws:cloudtrail | correct | the search the use case runs names this sourcetype |
| 4.1.320 AWS CloudTrail IAM user listing | `splunk-ta-aws` | Splunk_TA_aws | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.1.320 AWS CloudTrail IAM user listing | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.1.320 AWS CloudTrail IAM user listing | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.1.320 AWS CloudTrail IAM user listing | `props-conf` | props.conf | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.1.320 AWS CloudTrail IAM user listing | `severity` | severity | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.3.106 GCP Global forwarding rule create | `google-gcp-audit` | google:gcp:audit | correct | the search the use case runs names this sourcetype |
| 4.3.106 GCP Global forwarding rule create | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.3.106 GCP Global forwarding rule create | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.3.106 GCP Global forwarding rule create | `props-conf` | props.conf | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.3.106 GCP Global forwarding rule create | `severity` | severity | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.3.106 GCP Global forwarding rule create | `gcp-audit` | gcp:audit | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `azure-monitor-activity` | azure:monitor:activity | correct | the search the use case runs names this sourcetype |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `splunk-ta-microsoft-cloudservices` | Splunk_TA_microsoft-cloudservices | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `props-conf` | props.conf | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `severity` | severity | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `azure-monitor-activity` | azure:monitor:activity | correct | the search the use case runs names this sourcetype |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `splunk-ta-microsoft-cloudservices` | Splunk_TA_microsoft-cloudservices | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `user` | User | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `props-conf` | props.conf | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `severity` | severity | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `splunk-ta-aws` | Splunk_TA_aws | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `action` | action | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `status` | status | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `props-conf` | props.conf | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `severity` | severity | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `aws-elb-accesslogs` | aws:elb:accesslogs | correct | the search the use case runs names this sourcetype |

## vendorProducts (loose-1)

| UC | Value | Evidence | Grade | Reason |
|---|---|---|---|---|
| 1.1.4 Disk I/O Saturation (Linux) | `commvault` | commvault | wrong | the confirming token is not the monitored product |
| 1.1.4 Disk I/O Saturation (Linux) | `elasticsearch` | elasticsearch | wrong | the confirming token is not the monitored product |
| 1.1.4 Disk I/O Saturation (Linux) | `fleet` | fleet | wrong | the confirming token is not the monitored product |
| 1.1.4 Disk I/O Saturation (Linux) | `github` | github | wrong | the confirming token is not the monitored product |
| 1.1.4 Disk I/O Saturation (Linux) | `hashicorp` | Vault | wrong | the confirming token is not the monitored product |
| 1.1.4 Disk I/O Saturation (Linux) | `hyperv` | hyperv | wrong | the confirming token is not the monitored product |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `azure` | azure | wrong | the confirming token is not the monitored product |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `checkpoint` | checkpoint | wrong | the confirming token is not the monitored product |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `exchange` | exchange | wrong | the confirming token is not the monitored product |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `github` | github | wrong | the confirming token is not the monitored product |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `m365` | m365 | wrong | the confirming token is not the monitored product |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `microsoft` | microsoft | correct | the title or the app field names this product |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `checkpoint` | checkpoint | wrong | the confirming token is not the monitored product |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `defender` | defender | wrong | the confirming token is not the monitored product |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `github` | github | wrong | the confirming token is not the monitored product |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `microsoft` | microsoft | correct | the title or the app field names this product |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `veeam` | veeam | wrong | the confirming token is not the monitored product |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `fleet` | fleet | wrong | the confirming token is not the monitored product |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `github` | github | wrong | the confirming token is not the monitored product |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `hardware_bmc` | hardware_bmc | wrong | the confirming token is not the monitored product |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `linux` | linux | wrong | linux is a generic word, not the product this use case monitors |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `oracle` | oracle | wrong | the confirming token is not the monitored product |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 1.2.114 Unapproved VM-Read Access to LSASS | `checkpoint` | checkpoint | wrong | the confirming token is not the monitored product |
| 1.2.114 Unapproved VM-Read Access to LSASS | `claims` | claims | wrong | the confirming token is not the monitored product |
| 1.2.114 Unapproved VM-Read Access to LSASS | `defender` | defender | wrong | the confirming token is not the monitored product |
| 1.2.114 Unapproved VM-Read Access to LSASS | `hardware_bmc` | hardware_bmc | wrong | the confirming token is not the monitored product |
| 1.2.114 Unapproved VM-Read Access to LSASS | `m365` | Entra | wrong | the confirming token is not the monitored product |
| 1.2.114 Unapproved VM-Read Access to LSASS | `microsoft` | microsoft | debatable | the token appears in the search or data sources, not as the subject of the title |
| 1.2.61 Windows Data Deduplication Job Health | `checkpoint` | checkpoint | wrong | the confirming token is not the monitored product |
| 1.2.61 Windows Data Deduplication Job Health | `fleet` | fleet | wrong | the confirming token is not the monitored product |
| 1.2.61 Windows Data Deduplication Job Health | `github` | github | wrong | the confirming token is not the monitored product |
| 1.2.61 Windows Data Deduplication Job Health | `microsoft` | microsoft | correct | the title or the app field names this product |
| 1.2.61 Windows Data Deduplication Job Health | `snmp` | snmp | wrong | the confirming token is not the monitored product |
| 1.2.61 Windows Data Deduplication Job Health | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 1.1.59 Network Team Failover Detection (Linux) | `github` | github | wrong | the confirming token is not the monitored product |
| 1.1.59 Network Team Failover Detection (Linux) | `linux` | linux | wrong | linux is a generic word, not the product this use case monitors |
| 1.1.59 Network Team Failover Detection (Linux) | `pipeline` | pipeline | wrong | pipeline is a generic word, not the product this use case monitors |
| 1.1.59 Network Team Failover Detection (Linux) | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 1.1.59 Network Team Failover Detection (Linux) | `stream` | stream | wrong | stream is a generic word, not the product this use case monitors |
| 1.1.59 Network Team Failover Detection (Linux) | `syslog` | syslog | debatable | syslog is a transport, a content pack, or the SIEM itself |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `fleet` | fleet | wrong | the confirming token is not the monitored product |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `linux` | linux | wrong | linux is a generic word, not the product this use case monitors |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `citrix` | citrix | correct | the title or the app field names this product |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `linux` | linux | wrong | linux is a generic word, not the product this use case monitors |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `pipeline` | pipeline | wrong | pipeline is a generic word, not the product this use case monitors |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `stream` | stream | wrong | stream is a generic word, not the product this use case monitors |
| 2.6.46 Citrix Monitor OData Load Index Trending | `citrix` | citrix | correct | the title or the app field names this product |
| 2.6.46 Citrix Monitor OData Load Index Trending | `linux` | linux | wrong | linux is a generic word, not the product this use case monitors |
| 2.6.46 Citrix Monitor OData Load Index Trending | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 2.6.46 Citrix Monitor OData Load Index Trending | `stream` | stream | wrong | stream is a generic word, not the product this use case monitors |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `linux` | linux | wrong | linux is a generic word, not the product this use case monitors |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `openstack` | openstack | correct | the title or the app field names this product |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `pipeline` | pipeline | wrong | pipeline is a generic word, not the product this use case monitors |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `stream` | stream | wrong | stream is a generic word, not the product this use case monitors |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `citrix` | citrix | correct | the title or the app field names this product |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `linux` | linux | wrong | linux is a generic word, not the product this use case monitors |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `pipeline` | pipeline | wrong | pipeline is a generic word, not the product this use case monitors |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `syslog` | syslog | debatable | syslog is a transport, a content pack, or the SIEM itself |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `windows` | windows | wrong | windows is a generic word, not the product this use case monitors |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `hardware_bmc` | hardware_bmc | wrong | the confirming token is not the monitored product |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `linux` | linux | wrong | linux is a generic word, not the product this use case monitors |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `pipeline` | pipeline | wrong | pipeline is a generic word, not the product this use case monitors |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `snmp` | snmp | correct | the title or the app field names this product |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `syslog` | syslog | debatable | syslog is a transport, a content pack, or the SIEM itself |
| 2.6.32 Hypervisor Connection Health Monitoring | `citrix` | citrix | correct | the title or the app field names this product |
| 2.6.32 Hypervisor Connection Health Monitoring | `hyperv` | hyperv | correct | the title or the app field names this product |
| 2.6.32 Hypervisor Connection Health Monitoring | `linux` | linux | wrong | linux is a generic word, not the product this use case monitors |
| 2.6.32 Hypervisor Connection Health Monitoring | `microsoft` | microsoft | correct | the title or the app field names this product |
| 2.6.32 Hypervisor Connection Health Monitoring | `nutanix` | nutanix | debatable | the token appears in the search or data sources, not as the subject of the title |
| 2.6.32 Hypervisor Connection Health Monitoring | `pipeline` | pipeline | wrong | pipeline is a generic word, not the product this use case monitors |
| 2.2.2 Hyper-V Replication Health | `hyperv` | hyperv | wrong | the confirming token is not the monitored product |
| 2.2.2 Hyper-V Replication Health | `linux` | linux | wrong | linux is a generic word, not the product this use case monitors |
| 2.2.2 Hyper-V Replication Health | `microsoft` | microsoft | correct | the title or the app field names this product |
| 2.2.2 Hyper-V Replication Health | `pagerduty` | pagerduty | wrong | the confirming token is not the monitored product |
| 2.2.2 Hyper-V Replication Health | `pipeline` | pipeline | wrong | pipeline is a generic word, not the product this use case monitors |
| 2.2.2 Hyper-V Replication Health | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `broadcom_symantec` | Broadcom | wrong | the confirming token is not the monitored product |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `checkpoint` | checkpoint | wrong | the confirming token is not the monitored product |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `hardware_bmc` | hardware_bmc | wrong | the confirming token is not the monitored product |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `pipeline` | pipeline | wrong | pipeline is a generic word, not the product this use case monitors |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `syslog` | syslog | debatable | syslog is a transport, a content pack, or the SIEM itself |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `dell_emc` | Unity | wrong | the confirming token is not the monitored product |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `github` | github | wrong | the confirming token is not the monitored product |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `itsi` | itsi | wrong | the confirming token is not the monitored product |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `kubernetes` | kubernetes | correct | the title or the app field names this product |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `microsoft` | microsoft | wrong | the confirming token is not the monitored product |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `openshift` | openshift | wrong | the confirming token is not the monitored product |
| 3.1.23 Container Network I/O Anomalies | `asterisk` | asterisk | wrong | the confirming token is not the monitored product |
| 3.1.23 Container Network I/O Anomalies | `docker` | docker | correct | the title or the app field names this product |
| 3.1.23 Container Network I/O Anomalies | `envoy` | envoy | wrong | the confirming token is not the monitored product |
| 3.1.23 Container Network I/O Anomalies | `fleet` | fleet | wrong | the confirming token is not the monitored product |
| 3.1.23 Container Network I/O Anomalies | `github` | github | correct | the title or the app field names this product |
| 3.1.23 Container Network I/O Anomalies | `hashicorp` | Vault | wrong | the confirming token is not the monitored product |
| 3.1.1 Container Crash Loops | `docker` | docker | correct | the title or the app field names this product |
| 3.1.1 Container Crash Loops | `fleet` | fleet | wrong | the confirming token is not the monitored product |
| 3.1.1 Container Crash Loops | `hyperv` | Hyper-V | wrong | the confirming token is not the monitored product |
| 3.1.1 Container Crash Loops | `itsi` | itsi | wrong | the confirming token is not the monitored product |
| 3.1.1 Container Crash Loops | `kubernetes` | kubernetes | wrong | the confirming token is not the monitored product |
| 3.1.1 Container Crash Loops | `linux` | linux | wrong | linux is a generic word, not the product this use case monitors |
| 3.5.7 Envoy Proxy Error Rates | `envoy` | envoy | correct | the title or the app field names this product |
| 3.5.7 Envoy Proxy Error Rates | `github` | github | wrong | the confirming token is not the monitored product |
| 3.5.7 Envoy Proxy Error Rates | `kubernetes` | kubernetes | correct | the title or the app field names this product |
| 3.5.7 Envoy Proxy Error Rates | `nginx` | nginx | wrong | the confirming token is not the monitored product |
| 3.5.7 Envoy Proxy Error Rates | `opentelemetry` | opentelemetry | correct | the title or the app field names this product |
| 3.5.7 Envoy Proxy Error Rates | `pagerduty` | pagerduty | wrong | the confirming token is not the monitored product |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `azure` | azure | wrong | the confirming token is not the monitored product |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `fleet` | fleet | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `gcp` | Google Cloud | wrong | the confirming token is not the monitored product |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `github` | github | wrong | the confirming token is not the monitored product |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `itsi` | itsi | correct | the title or the app field names this product |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `kubernetes` | kubernetes | correct | the title or the app field names this product |
| 3.4.5 Registry Authentication and Authorization Failures | `docker` | docker | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.4.5 Registry Authentication and Authorization Failures | `github` | github | wrong | the confirming token is not the monitored product |
| 3.4.5 Registry Authentication and Authorization Failures | `kubernetes` | kubernetes | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.4.5 Registry Authentication and Authorization Failures | `nginx` | nginx | correct | the title or the app field names this product |
| 3.4.5 Registry Authentication and Authorization Failures | `opentelemetry` | OTel Collector | wrong | the confirming token is not the monitored product |
| 3.4.5 Registry Authentication and Authorization Failures | `pagerduty` | pagerduty | wrong | the confirming token is not the monitored product |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `azure` | azure | wrong | the confirming token is not the monitored product |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `checkpoint` | cp_log | wrong | the confirming token is not the monitored product |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `claims` | claims | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `fleet` | fleet | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `gcp` | Google Cloud | wrong | the confirming token is not the monitored product |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `github` | github | wrong | the confirming token is not the monitored product |
| 3.4.1 Image Push/Pull Audit | `argocd` | argocd | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.4.1 Image Push/Pull Audit | `docker` | docker | correct | the title or the app field names this product |
| 3.4.1 Image Push/Pull Audit | `github` | github | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.4.1 Image Push/Pull Audit | `gitlab` | gitlab | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.4.1 Image Push/Pull Audit | `jenkins` | jenkins | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.4.1 Image Push/Pull Audit | `kubernetes` | kubernetes | debatable | the token appears in the search or data sources, not as the subject of the title |
| 4.3.27 Cloud Armor WAF Events | `gcp` | Google Cloud | wrong | the confirming token is not the monitored product |
| 4.3.27 Cloud Armor WAF Events | `m365` | m365 | wrong | the confirming token is not the monitored product |
| 4.3.27 Cloud Armor WAF Events | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 4.3.27 Cloud Armor WAF Events | `windows` | windows | wrong | windows is a generic word, not the product this use case monitors |
| 4.1.320 AWS CloudTrail IAM user listing | `aws` | CloudTrail | correct | the title or the app field names this product |
| 4.1.320 AWS CloudTrail IAM user listing | `dell_emc` | Unity | wrong | the confirming token is not the monitored product |
| 4.1.320 AWS CloudTrail IAM user listing | `pipeline` | pipeline | wrong | pipeline is a generic word, not the product this use case monitors |
| 4.1.320 AWS CloudTrail IAM user listing | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 4.1.320 AWS CloudTrail IAM user listing | `windows` | windows | wrong | windows is a generic word, not the product this use case monitors |
| 4.3.106 GCP Global forwarding rule create | `dell_emc` | Unity | wrong | the confirming token is not the monitored product |
| 4.3.106 GCP Global forwarding rule create | `gcp` | Google Cloud | correct | the title or the app field names this product |
| 4.3.106 GCP Global forwarding rule create | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 4.3.106 GCP Global forwarding rule create | `windows` | windows | wrong | windows is a generic word, not the product this use case monitors |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `azure` | azure | correct | the title or the app field names this product |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `defender` | defender | correct | the title or the app field names this product |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `dell_emc` | Unity | wrong | the confirming token is not the monitored product |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `m365` | m365 | wrong | the confirming token is not the monitored product |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `microsoft` | microsoft | correct | the title or the app field names this product |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `azure` | azure | correct | the title or the app field names this product |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `dell_emc` | Unity | wrong | the confirming token is not the monitored product |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `m365` | m365 | wrong | the confirming token is not the monitored product |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `microsoft` | microsoft | correct | the title or the app field names this product |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `windows` | windows | wrong | windows is a generic word, not the product this use case monitors |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `aws` | CloudWatch | wrong | the confirming token is not the monitored product |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `splunk` | splunk | debatable | splunk is a transport, a content pack, or the SIEM itself |

## businessOutcomes (strict-1)

| UC | Value | Evidence | Grade | Reason |
|---|---|---|---|---|
| 4.3.106 GCP Global forwarding rule create | `lower_security_risk` | attack surface | wrong | the phrase sits in a sentence pasted across many use cases |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `lower_security_risk` | attack surface | wrong | the phrase sits in a sentence pasted across many use cases |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `faster_incident_response` | incident response | wrong | the phrase sits in a sentence pasted across many use cases |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `prove_compliance` | audit evidence | wrong | the phrase sits in a sentence pasted across many use cases |
| 19.1.10 Blade Firmware Compliance per FRU (Cisco UCS B-Series and X-Series) | `improve_change_safety` | change window | correct | the sentence is about this use case and the phrase is specific |
| 22.26.27 KBF personkontroll privileged access correlation | `control_privileged_access` | privileged access | correct | the title names this phrase, and the sentence is not a stock closer |
| 4.1.37 SNS Delivery Failures and Bounce/Complaint | `faster_incident_response` | incident response | wrong | the phrase sits in a sentence pasted across many use cases |
| 4.1.37 SNS Delivery Failures and Bounce/Complaint | `prove_compliance` | audit evidence | wrong | the phrase sits in a sentence pasted across many use cases |
| 4.1.140 AWS SageMaker Notebook Instance Creation | `lower_security_risk` | attack surface | wrong | the phrase sits in a sentence pasted across many use cases |
| 4.2.310 Azure Storage managementPolicies Create or Update | `lower_security_risk` | attack surface | wrong | the phrase sits in a sentence pasted across many use cases |
| 4.4.82 Cross-Cloud Snapshot Export Burst | `faster_incident_response` | incident response | wrong | the phrase sits in a sentence pasted across many use cases |
| 4.4.82 Cross-Cloud Snapshot Export Burst | `prove_compliance` | audit evidence | wrong | the phrase sits in a sentence pasted across many use cases |
| 12.4.2 Configuration Drift Detection | `improve_change_safety` | Configuration Drift | correct | the title names this phrase, and the sentence is not a stock closer |
| 1.1.111 World-Writable File Detection | `control_privileged_access` | privileged account | correct | the sentence is about this use case and the phrase is specific |
| 1.1.112 Unowned File Detection | `faster_incident_response` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 1.1.116 Installed Package Drift Detection | `lower_security_risk` | attack surface | correct | the sentence is about this use case and the phrase is specific |
| 1.1.43 Fstrim and TRIM Command Monitoring | `improve_change_safety` | configuration drift | correct | the sentence is about this use case and the phrase is specific |
| 1.1.54 Network Namespace Monitoring | `improve_change_safety` | configuration drift | correct | the sentence is about this use case and the phrase is specific |
| 1.1.76 Privilege Escalation Detection | `control_privileged_access` | Privilege Escalation | correct | the title names this phrase, and the sentence is not a stock closer |
| 1.1.76 Privilege Escalation Detection | `improve_change_safety` | change window | correct | the sentence is about this use case and the phrase is specific |
| 1.1.79 Setcap Binary Monitoring | `control_privileged_access` | privilege escalation | correct | the sentence is about this use case and the phrase is specific |
| 1.1.94 Failed Log Forwarding | `prove_compliance` | compliance evidence | correct | the sentence is about this use case and the phrase is specific |
| 1.2.106 Windows Built-in Administrators Membership Changes | `control_privileged_access` | privilege escalation | correct | the sentence is about this use case and the phrase is specific |
| 1.2.15 DNS Server Health | `faster_incident_response` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 1.2.26 Windows Event Logs Cleared | `faster_incident_response` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 1.2.30 Suspicious LSASS Memory-Read Access | `control_privileged_access` | privilege escalation | correct | the sentence is about this use case and the phrase is specific |
| 1.2.33 Windows System Audit Policy Changes (Event 4719) | `prove_compliance` | audit evidence | correct | the sentence is about this use case and the phrase is specific |
| 1.2.37 Four or More RC4 Kerberos Service Accounts Requested in One Hour | `control_privileged_access` | privileged access | correct | the sentence is about this use case and the phrase is specific |
| 1.2.49 Privileged Accounts Used in Windows Explicit-Credential Attempts | `control_privileged_access` | Privileged Account | correct | the title names this phrase, and the sentence is not a stock closer |
| 1.2.55 High-Risk Windows Token Privileges Enabled | `control_privileged_access` | privilege escalation | correct | the sentence is about this use case and the phrase is specific |
| 1.2.64 Windows Event Log Capacity and Retention Risk | `faster_incident_response` | incident response | correct | the sentence is about this use case and the phrase is specific |
| 1.2.76 Active Directory AdminSDHolder Modification | `control_privileged_access` | privileged access | correct | the sentence is about this use case and the phrase is specific |
| 1.2.90 Windows Recovery Inhibition Commands | `lower_security_risk` | malicious activity | correct | the sentence is about this use case and the phrase is specific |
| 1.4.1 Latest IPMI Sensor Reading Is Critical or Non-Recoverable | `reduce_downtime` | service disruption | correct | the sentence is about this use case and the phrase is specific |

## businessAreas (strict-1)

| UC | Value | Evidence | Grade | Reason |
|---|---|---|---|---|
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `data_protection` | data protection | wrong | data protection is the tail of stale-data protection |
| 1.2.61 Windows Data Deduplication Job Health | `infrastructure_operations` | disk space | debatable | the phrase occurs, but it is too broad to settle the label |
| 1.1.59 Network Team Failover Detection (Linux) | `network_operations` | network operations | correct | the sentence is about this use case and the phrase is specific |
| 9.8.5 BeyondTrust Password Safe Credential Rotation Compliance | `compliance_and_risk` | audit finding | wrong | the phrase sits in a sentence pasted across many use cases |
| 9.1.17 Entra Conditional Access Policy Changes | `compliance_and_risk` | audit finding | wrong | the phrase sits in a sentence pasted across many use cases |
| 9.3.10 SSO Session Hijacking Indicators | `compliance_and_risk` | audit finding | wrong | the phrase sits in a sentence pasted across many use cases |
| 9.1.2 Account Lockout Monitoring | `compliance_and_risk` | audit finding | wrong | the phrase sits in a sentence pasted across many use cases |
| 9.3.13 App Registration Secret Expiry | `compliance_and_risk` | audit finding | wrong | the phrase sits in a sentence pasted across many use cases |
| 9.4.23 BeyondTrust Password Safe Denied or Failed Access Attempts | `compliance_and_risk` | audit finding | wrong | the phrase sits in a sentence pasted across many use cases |
| 9.8.1 BeyondTrust Privileged Session Recording and Playback Audit | `compliance_and_risk` | audit finding | wrong | the phrase sits in a sentence pasted across many use cases |
| 9.3.3 Token Anomaly Detection | `compliance_and_risk` | audit finding | wrong | the phrase sits in a sentence pasted across many use cases |
| 10.12.5 ACH Origination Anomalies | `service_management` | SLA breach | wrong | the phrase sits in a sentence pasted across many use cases |
| 10.2.60 Mmc LOLBAS Execution Process Spawn | `service_management` | SLA breach | wrong | the phrase sits in a sentence pasted across many use cases |
| 10.7.147 Azure AD Multiple Service Principals Created by SP | `service_management` | SLA breach | wrong | the phrase sits in a sentence pasted across many use cases |
| 10.7.513 Windows Domain Admin Impersonation Indicator | `service_management` | SLA breach | wrong | the phrase sits in a sentence pasted across many use cases |
| 10.2.167 SMB Traffic Spike - MLTK | `service_management` | SLA breach | wrong | the phrase sits in a sentence pasted across many use cases |
| 10.3.270 PowerShell - Connect To Internet With Hidden Window | `service_management` | SLA breach | wrong | the phrase sits in a sentence pasted across many use cases |
| 10.4.118 Detect Outlook exe writing a zip file | `service_management` | SLA breach | wrong | the phrase sits in a sentence pasted across many use cases |
| 10.3.505 Windows Ldifde Directory Object Behavior | `service_management` | SLA breach | wrong | the phrase sits in a sentence pasted across many use cases |
| 14.9.6 Snort IDS Threat Detection on OT Networks | `security_operations` | Threat Detection | correct | the title names this phrase, and the sentence is not a stock closer |
| 21.3.20 DIPS Arena User Authentication and SSO Monitoring | `identity_and_access` | single sign-on | correct | the sentence is about this use case and the phrase is specific |
| 22.6.33 Information Deletion — S3 Object Delete Storm Outside Retention Workflow | `compliance_and_risk` | audit finding | debatable | compliance use case, but the sentence is the pasted audit-findings closer |
| 22.26.27 KBF personkontroll privileged access correlation | `identity_and_access` | privileged access | correct | the title names this phrase, and the sentence is not a stock closer |
| 22.26.27 KBF personkontroll privileged access correlation | `compliance_and_risk` | audit finding | correct | the sentence is about this use case and the phrase is specific |
| 22.12.12 Production change volume during financial close windows | `compliance_and_risk` | audit finding | debatable | compliance use case, but the sentence is the pasted audit-findings closer |
| 22.55.7 CLC/TS 50701 Target Security Levels (SL-T) Coverage — every zone has an SL-T justified against threat scenarios | `compliance_and_risk` | audit finding | debatable | compliance use case, but the sentence is the pasted audit-findings closer |
| 22.8.33 SOC 2 CC7.1 — System-operations monitoring: uptime attestation and alert-noise governance | `compliance_and_risk` | audit finding | debatable | compliance use case, but the sentence is the pasted audit-findings closer |
| 22.13.9 Security Awareness Training Completion for BES Personnel | `compliance_and_risk` | audit finding | debatable | compliance use case, but the sentence is the pasted audit-findings closer |
| 22.55.12 CLC/TS 50701 Rail Cybersecurity Incident Detection — rail-OT specific detection content covering signal, RBC, CBTC, GSM-R, FRMCS, rolling stock | `compliance_and_risk` | audit finding | debatable | compliance use case, but the sentence is the pasted audit-findings closer |
| 22.10.55 Cloud Service Provider — ePHI Hosting Admin Actions in AWS or Azure Audit | `compliance_and_risk` | audit finding | debatable | compliance use case, but the sentence is the pasted audit-findings closer |
| 9.3.5 IdP Availability Monitoring | `compliance_and_risk` | audit finding | wrong | the phrase sits in a sentence pasted across many use cases |

## personas (strict-1)

| UC | Value | Evidence | Grade | Reason |
|---|---|---|---|---|
| 13.3.1 Legacy Nagios, Icinga, Zabbix, and Nimsoft Alert Ingestion Health, Cross-Tool Deduplication, and Source-of-Truth Reconciliation | `ot_operator` | control room | debatable | control room is a place or a metaphor, not an OT operator |
| 1.1.10 Instrumented Cron Job Non-Zero Exit Detection | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 1.1.101 Context Switch Anomalies Detection | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 1.1.114 Linux Per-Process File Descriptor Limit Utilization | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 1.1.123 Linux Cgroup Resource Pressure (PSI) | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 1.1.128 Filesystem Inode Exhaustion | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 1.1.26 CPU Frequency Scaling Events | `platform_engineer` | platform engineer | correct | the sentence is about this use case and the phrase is specific |
| 1.1.33 Inode Exhaustion Detection | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 1.1.44 Memory Leak Detection Per Process | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 1.1.49 Memory Cgroup Limit Enforcement | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 1.1.53 Socket Buffer Overflow Detection | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 1.1.64 Network Latency Monitoring (Ping RTT) | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 1.1.88 Container Escape Attempt Detection | `incident_responder` | incident responder | correct | the sentence is about this use case and the phrase is specific |
| 1.1.99 Kernel Lock Contention Detection | `platform_engineer` | platform engineer | correct | the sentence is about this use case and the phrase is specific |
| 1.2.11 Windows Bug Check Reboot Detection | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 1.2.134 Configuration Manager Client Pending Restart Status | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 1.2.17 Windows Certificate Expiration | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 1.2.77 Service Principal Name Added to AD User | `service_owner` | service owner | wrong | the match is the prefix of service ownership, not the persona |
| 2.2.5 Hyper-V Windows Guest Integration Service Protocol Mismatch | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 2.2.6 Hyper-V Host Sustained Physical CPU Overload | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 3.3.12 OpenShift Network Operator and OVN-Kubernetes Cluster Network Health | `network_operator` | Network Operator | wrong | OpenShift Network Operator is a component, not a person |
| 8.7.7 IIS Client Error Status Trending for Service Review | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 10.6.197 Citrix Admin Console Privilege Escalation Detection | `ot_operator` | control room | debatable | control room is a place or a metaphor, not an OT operator |
| 10.6.6 Vulnerability SLA Compliance | `service_owner` | service owner | correct | the sentence is about this use case and the phrase is specific |
| 13.6.5 Grafana User Login Audit, Session Anomalies, and Account Takeover Indicators (failed-login spikes, brute force, impossible travel, OAuth token abuse, anonymous org exposure, admin promotion, API key drift, session forgery; OSS Enterprise Cloud SSO SAML OAuth) | `ot_operator` | control room | debatable | control room is a place or a metaphor, not an OT operator |
| 17.1.35 Cisco ISE pxGrid Cloud Connectivity and TLS Health | `network_operator` | Network operator | debatable | stock sentence: Network operators treat UC-… as the canonical signal |
| 17.1.43 Cisco ISE TACACS+ Device Administration — Privileged Command Auditing | `network_operator` | network engineer | correct | the sentence is about this use case and the phrase is specific |
| 17.1.46 Cisco Identity Intelligence (CII) Risk-Score Drift and Adaptive-Auth Triggering | `network_operator` | Network operator | debatable | stock sentence: Network operators treat UC-… as the canonical signal |
| 17.1.63 ISE Stealth-Mode Posture and Compliance Pre-Auth Validation | `network_operator` | Network operator | debatable | stock sentence: Network operators treat UC-… as the canonical signal |
| 17.3.36 Netskope Private Access (NPA) Health | `network_operator` | Network operator | debatable | stock sentence: Network operators treat UC-… as the canonical signal |

## industries (strict-1)

| UC | Value | Evidence | Grade | Reason |
|---|---|---|---|---|
| 10.12.5 ACH Origination Anomalies | `financial-services` | Financial Services | correct | the industry field matches this registry name |
| 21.8.2 Core Network Element Health (MME, SGW, PGW) | `telecommunications` | Telecommunications | correct | the industry field matches this registry name |
| 21.3.20 DIPS Arena User Authentication and SSO Monitoring | `healthcare` | Healthcare | correct | the industry field matches this registry name |
| 21.12.23 Municipal smart city sensor outage | `public-sector-and-government` | Public Sector and Government | correct | the industry field matches this registry name |
| 21.5.37 Pipeline SCADA RTU firmware version drift | `oil-gas-and-mining` | Oil, Gas, and Mining | correct | the industry field matches this registry name |
| 21.10.29 Annuity surrender spike detection | `insurance-and-claims-processing` | Insurance and Claims Processing | correct | the industry field matches this registry name |
| 21.3.68 HIPAA workforce termination access revocation | `healthcare-and-life-sciences` | Healthcare and Life Sciences | correct | the industry field matches this registry name |
| 21.5.44 Downhole gauge communication loss | `oil-gas-and-mining` | Oil, Gas, and Mining | correct | the industry field matches this registry name |
| 21.12.10 Higher-ed FERPA student record access audit | `public-sector-and-government` | Public Sector and Government | correct | the industry field matches this registry name |
| 22.55.7 CLC/TS 50701 Target Security Levels (SL-T) Coverage — every zone has an SL-T justified against threat scenarios | `transportation` | Transportation | correct | the industry field matches this registry name |
| 22.55.12 CLC/TS 50701 Rail Cybersecurity Incident Detection — rail-OT specific detection content covering signal, RBC, CBTC, GSM-R, FRMCS, rolling stock | `transportation` | Transportation | correct | the industry field matches this registry name |
| 23.9.3 Waste Diversion and Recycling Rate Tracking | `cross-industry` | Cross-industry | debatable | Cross-industry is a bucket, not an industry |
| 23.8.1 CEO/CFO Business Health Scorecard | `cross-industry` | Cross-industry | debatable | Cross-industry is a bucket, not an industry |
| 23.1.1 Website Conversion Funnel Analysis | `cross-industry` | Cross-industry | debatable | Cross-industry is a bucket, not an industry |
| 23.6.4 Payment Processing Success Rate and Revenue Leakage | `cross-industry` | Cross-industry | debatable | Cross-industry is a bucket, not an industry |
| 23.8.2 Operational Efficiency and Productivity Metrics | `cross-industry` | Cross-industry | debatable | Cross-industry is a bucket, not an industry |
| 14.6.2 S7comm Program Upload/Download Detection | `manufacturing` | Manufacturing | correct | the industry field matches this registry name |
| 21.9.21 AMI water meter leak detection | `water-and-wastewater-utilities` | Water and Wastewater Utilities | correct | the industry field matches this registry name |
| 21.4.23 Maritime AIS vessel route deviation | `transportation-and-logistics` | Transportation and Logistics | correct | the industry field matches this registry name |
| 21.10.6 Insurance Fraud Ring Detection | `insurance-and-financial-services` | Insurance and Financial Services | correct | the industry field matches this registry name |
| 21.13.19 Athletic event crowd density safety | `education-and-academic-medical` | Education and Academic Medical | correct | the industry field matches this registry name |
| 21.9.22 Chemical dosing pump failure | `water-and-wastewater-utilities` | Water and Wastewater Utilities | correct | the industry field matches this registry name |
| 5.10.1 Diameter Signaling Health Monitoring | `telecommunications` | Telecommunications | correct | the industry field matches this registry name |
| 5.10.10 BGP Community and AS-Path Anomaly from Upstream Providers | `telecommunications` | Telecommunications | correct | the industry field matches this registry name |
| 5.10.11 Provider SLA Measurement (Latency, Jitter, Loss to PE) | `telecommunications` | Telecommunications | correct | the industry field matches this registry name |
| 5.10.12 Carrier Maintenance Window Correlation | `telecommunications` | Telecommunications | correct | the industry field matches this registry name |
| 5.10.13 PSTN Gateway Health (Analog/PRI/SIP Gateway Status) | `telecommunications` | Telecommunications | correct | the industry field matches this registry name |
| 5.10.14 Internet Exchange Point (IXP) Peering Health | `telecommunications` | Telecommunications | correct | the industry field matches this registry name |
| 5.10.15 Carrier BGP Session Failover and Prefix Acceptance Tracking | `telecommunications` | Telecommunications | correct | the industry field matches this registry name |
| 5.10.2 Diameter Subscriber Data Accounting | `telecommunications` | Telecommunications | correct | the industry field matches this registry name |

## sourcetypes (strict-1)

| UC | Value | Evidence | Grade | Reason |
|---|---|---|---|---|
| 1.1.4 Disk I/O Saturation (Linux) | `iostat` | sourcetype=iostat | correct | the search the use case runs names this sourcetype |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `xmlwineventlog` | sourcetype=XmlWinEventLog | correct | the search the use case runs names this sourcetype |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `xmlwineventlog` | sourcetype=XmlWinEventLog | correct | the search the use case runs names this sourcetype |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `hardware-ipmi-sensor-2` | sourcetype=hardware:ipmi_sensor | correct | the search the use case runs names this sourcetype |
| 1.2.114 Unapproved VM-Read Access to LSASS | `wineventlog` | sourcetype=WinEventLog | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.114 Unapproved VM-Read Access to LSASS | `xmlwineventlog` | sourcetype=XmlWinEventLog | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 1.2.61 Windows Data Deduplication Job Health | `ms-windows-dedup-status` | sourcetype=ms:windows:dedup:status | correct | the search the use case runs names this sourcetype |
| 1.1.59 Network Team Failover Detection (Linux) | `linux-teamd-state` | sourcetype=linux:teamd_state | correct | the search the use case runs names this sourcetype |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `linux-journald-systemd-coredump` | sourcetype=linux:journald:systemd-coredump | correct | the search the use case runs names this sourcetype |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `citrix-sharefile-admin` | sourcetype="citrix:sharefile:admin | correct | the search the use case runs names this sourcetype |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `citrix-sharefile-audit` | sourcetype='citrix:sharefile:audit | correct | the search the use case runs names this sourcetype |
| 2.6.46 Citrix Monitor OData Load Index Trending | `citrix-monitor-odata` | sourcetype='citrix:monitor:odata | correct | the search the use case runs names this sourcetype |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `openstack-cinder` | sourcetype='openstack:cinder | correct | the search the use case runs names this sourcetype |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `citrix-broker-events` | sourcetype='citrix:broker:events | correct | the search the use case runs names this sourcetype |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `citrix-monitor-odata` | sourcetype="citrix:monitor:odata | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `citrix-netscaler-syslog` | sourcetype="citrix:netscaler:syslog | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `vxrail-chassis` | sourcetype='vxrail:chassis | correct | the search the use case runs names this sourcetype |
| 2.6.32 Hypervisor Connection Health Monitoring | `citrix-broker-events` | sourcetype='citrix:broker:events | correct | the search the use case runs names this sourcetype |
| 2.6.32 Hypervisor Connection Health Monitoring | `hyperv-host-health` | sourcetype="hyperv_host_health | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.6.32 Hypervisor Connection Health Monitoring | `vmware-inv-host` | sourcetype="vmware:inv:host | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.2.2 Hyper-V Replication Health | `wineventlog-microsoft-windows-hyper-v-vmms-admin` | sourcetype='WinEventLog:Microsoft-Windows-Hyper-V-VMMS-Admin | correct | the search the use case runs names this sourcetype |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `vminv-hostsystem` | VMInv:HostSystem | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `vmware-inframon-events` | sourcetype=vmware_inframon:events | correct | the search the use case runs names this sourcetype |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `prometheus-scrape-metrics` | sourcetype='prometheus:scrape:metrics | correct | the search the use case runs names this sourcetype |
| 3.1.23 Container Network I/O Anomalies | `docker-stats` | sourcetype='docker:stats | correct | the search the use case runs names this sourcetype |
| 3.1.23 Container Network I/O Anomalies | `linux-proc-net-dev` | sourcetype=linux:proc:net:dev | correct | the search the use case runs names this sourcetype |
| 3.1.1 Container Crash Loops | `docker-container-logs` | sourcetype=docker:container:logs | correct | the search the use case runs names this sourcetype |
| 3.1.1 Container Crash Loops | `docker-events` | sourcetype='docker:events | correct | the search the use case runs names this sourcetype |
| 3.1.1 Container Crash Loops | `docker-stats` | sourcetype=docker:stats | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.1.1 Container Crash Loops | `linux-audit-2` | sourcetype=linux:audit | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.1.1 Container Crash Loops | `linux-cgroup` | sourcetype=linux:cgroup | correct | the search the use case runs names this sourcetype |
| 3.1.1 Container Crash Loops | `syslog` | sourcetype=syslog | correct | the search the use case runs names this sourcetype |
| 3.5.7 Envoy Proxy Error Rates | `envoy-stats` | sourcetype=envoy:stats | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.5.7 Envoy Proxy Error Rates | `istio-accesslog` | sourcetype=istio:accesslog | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.5.7 Envoy Proxy Error Rates | `kube-events` | sourcetype=kube:events | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.5.7 Envoy Proxy Error Rates | `otel-metrics` | sourcetype='otel:metrics | correct | the search the use case runs names this sourcetype |
| 3.5.7 Envoy Proxy Error Rates | `prometheus-istio` | sourcetype=prometheus:istio | correct | the search the use case runs names this sourcetype |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `openshift-controlplanemachineset` | sourcetype=openshift:controlplanemachineset | correct | the search the use case runs names this sourcetype |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `openshift-cpms` | sourcetype="openshift:cpms | correct | the search the use case runs names this sourcetype |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `openshift-event` | sourcetype=openshift:event | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `openshift-machine` | sourcetype=openshift:machine | correct | the search the use case runs names this sourcetype |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `openshift-machinehealthcheck` | sourcetype='openshift:machinehealthcheck | correct | the search the use case runs names this sourcetype |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `openshift-machineset` | sourcetype=openshift:machineset | correct | the search the use case runs names this sourcetype |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `prometheus-metrics` | sourcetype=prometheus:metrics | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.4.5 Registry Authentication and Authorization Failures | `harbor-access` | sourcetype='harbor:access | correct | the search the use case runs names this sourcetype |
| 3.4.5 Registry Authentication and Authorization Failures | `harbor-audit` | sourcetype=harbor:audit | correct | the search the use case runs names this sourcetype |
| 3.4.5 Registry Authentication and Authorization Failures | `harbor-webhook` | sourcetype=harbor:webhook | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.4.5 Registry Authentication and Authorization Failures | `kube-events` | sourcetype=kube:events | correct | the search the use case runs names this sourcetype |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `k8s-audit` | sourcetype=k8s_audit | correct | the search the use case runs names this sourcetype |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `kube-apiserver-audit` | sourcetype='kube:apiserver:audit | correct | the search the use case runs names this sourcetype |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `kube-events` | sourcetype=kube:events | correct | the search the use case runs names this sourcetype |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `ocp-acrq-snapshot` | sourcetype=ocp_acrq_snapshot | correct | the search the use case runs names this sourcetype |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `ocp-audit` | sourcetype=ocp_audit | correct | the search the use case runs names this sourcetype |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `ocp-clusterresourcequota-snapshot` | sourcetype=ocp_clusterresourcequota_snapshot | correct | the search the use case runs names this sourcetype |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `ocp-events` | sourcetype=ocp_events | correct | the search the use case runs names this sourcetype |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `ocp-projectconfig-snapshot` | sourcetype=ocp_projectconfig_snapshot | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 3.4.1 Image Push/Pull Audit | `harbor-access` | sourcetype=harbor:access | correct | the search the use case runs names this sourcetype |
| 3.4.1 Image Push/Pull Audit | `harbor-audit` | sourcetype=harbor:audit | correct | the search the use case runs names this sourcetype |
| 3.4.1 Image Push/Pull Audit | `harbor-webhook` | sourcetype='harbor:webhook | correct | the search the use case runs names this sourcetype |
| 3.4.1 Image Push/Pull Audit | `kube-events` | sourcetype=kube:events | wrong | not a sourcetype in the search; it is troubleshooting text or a sibling feed |
| 4.3.27 Cloud Armor WAF Events | `google-gcp-pubsub-message` | sourcetype=`google:gcp:pubsub:message | correct | the search the use case runs names this sourcetype |
| 4.1.320 AWS CloudTrail IAM user listing | `aws-cloudtrail` | sourcetype=`aws:cloudtrail | correct | the search the use case runs names this sourcetype |
| 4.3.106 GCP Global forwarding rule create | `google-gcp-audit` | sourcetype=`google:gcp:audit | correct | the search the use case runs names this sourcetype |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `azure-monitor-activity` | sourcetype=`azure:monitor:activity | correct | the search the use case runs names this sourcetype |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `azure-monitor-activity` | sourcetype=`azure:monitor:activity | correct | the search the use case runs names this sourcetype |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `aws-elb-accesslogs` | sourcetype=`aws:elb:accesslogs | correct | the search the use case runs names this sourcetype |

## vendorProducts (strict-1)

| UC | Value | Evidence | Grade | Reason |
|---|---|---|---|---|
| 1.1.4 Disk I/O Saturation (Linux) | `linux` | Linux | wrong | Linux is a generic word, not the product this use case monitors |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `m365` | entra | correct | the title or the app field names this product |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `splunk_es` | Splunk Enterprise Security | correct | the title or the app field names this product |
| 1.2.98 NPS / RADIUS Authentication Monitoring | `windows` | Windows | wrong | Windows is a generic word, not the product this use case monitors |
| 1.2.46 DFS Replication Stale-Data, Sharing-Violation, and Partner Errors | `windows` | Windows | wrong | Windows is a generic word, not the product this use case monitors |
| 1.4.9 Out-of-Band Sensor Threshold Breach (IPMI) | `hardware_bmc` | BMC | correct | the title or the app field names this product |
| 1.2.114 Unapproved VM-Read Access to LSASS | `windows` | Windows | wrong | Windows is a generic word, not the product this use case monitors |
| 1.2.61 Windows Data Deduplication Job Health | `windows` | Windows | wrong | Windows is a generic word, not the product this use case monitors |
| 1.1.59 Network Team Failover Detection (Linux) | `linux` | Linux | wrong | Linux is a generic word, not the product this use case monitors |
| 1.1.23 Linux Core Dumps Processed by systemd-coredump | `linux` | Linux | wrong | Linux is a generic word, not the product this use case monitors |
| 2.6.74 Citrix ShareFile User Activity Audit Trail | `citrix` | Citrix | correct | the title or the app field names this product |
| 2.6.46 Citrix Monitor OData Load Index Trending | `citrix` | Citrix | correct | the title or the app field names this product |
| 2.9.3 OpenStack Cinder Volume Attach and Detach Error Rate | `openstack` | OpenStack | correct | the title or the app field names this product |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `citrix` | Citrix | correct | the title or the app field names this product |
| 2.6.31 Citrix Zone Topology and Zone Preference Failover | `syslog` | syslog | debatable | syslog is a transport, a content pack, or the SIEM itself |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `hardware_bmc` | iDRAC | correct | the title or the app field names this product |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `snmp` | SNMP | correct | the title or the app field names this product |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `syslog` | syslog | debatable | syslog is a transport, a content pack, or the SIEM itself |
| 2.10.8 VxRail Power Supply Redundancy Loss Events | `vxrail` | VxRail | correct | the title or the app field names this product |
| 2.6.32 Hypervisor Connection Health Monitoring | `citrix` | Citrix | correct | the title or the app field names this product |
| 2.6.32 Hypervisor Connection Health Monitoring | `hyperv` | Hyperv | correct | the title or the app field names this product |
| 2.6.32 Hypervisor Connection Health Monitoring | `nutanix` | Nutanix | debatable | the token appears in the search or data sources, not as the subject of the title |
| 2.6.32 Hypervisor Connection Health Monitoring | `vmware` | VMware | correct | the title or the app field names this product |
| 2.2.2 Hyper-V Replication Health | `hyperv` | Hyper-V | correct | the title or the app field names this product |
| 2.2.2 Hyper-V Replication Health | `windows` | windows | wrong | windows is a generic word, not the product this use case monitors |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `hardware_bmc` | BMC | correct | the title or the app field names this product |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `syslog` | syslog | debatable | syslog is a transport, a content pack, or the SIEM itself |
| 2.1.21 Unexpected vCenter Loss of ESXi Host Connection | `vmware` | VMware | correct | the title or the app field names this product |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `kubernetes` | Kubernetes | correct | the title or the app field names this product |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `opentelemetry` | OpenTelemetry | correct | the title or the app field names this product |
| 3.2.21 Kubernetes Slow Admission and Validation Webhooks Exhausting API Server Request Budget (Latency Backpressure Axis) | `prometheus` | prometheus | correct | the title or the app field names this product |
| 3.1.23 Container Network I/O Anomalies | `docker` | docker | correct | the title or the app field names this product |
| 3.1.23 Container Network I/O Anomalies | `github` | GitHub | correct | the title or the app field names this product |
| 3.1.23 Container Network I/O Anomalies | `prometheus` | Prometheus | correct | the title or the app field names this product |
| 3.1.1 Container Crash Loops | `docker` | Docker | correct | the title or the app field names this product |
| 3.1.1 Container Crash Loops | `linux` | Linux | wrong | Linux is a generic word, not the product this use case monitors |
| 3.1.1 Container Crash Loops | `opentelemetry` | OpenTelemetry | correct | the title or the app field names this product |
| 3.1.1 Container Crash Loops | `syslog` | syslog | debatable | syslog is a transport, a content pack, or the SIEM itself |
| 3.5.7 Envoy Proxy Error Rates | `envoy` | Envoy | correct | the title or the app field names this product |
| 3.5.7 Envoy Proxy Error Rates | `kubernetes` | Kubernetes | correct | the title or the app field names this product |
| 3.5.7 Envoy Proxy Error Rates | `opentelemetry` | OpenTelemetry | correct | the title or the app field names this product |
| 3.5.7 Envoy Proxy Error Rates | `prometheus` | Prometheus | correct | the title or the app field names this product |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `itsi` | Splunk ITSI | correct | the title or the app field names this product |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `kubernetes` | Kubernetes | correct | the title or the app field names this product |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `openshift` | OpenShift | correct | the title or the app field names this product |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `opentelemetry` | OpenTelemetry | correct | the title or the app field names this product |
| 3.3.24 OpenShift MachineHealthCheck Remediation Lifecycle: Unhealthy-Condition Detection, Remediation Storms, MachineSet Replica Drift, and Cluster API Capacity Watermark Risks | `prometheus` | prometheus | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.4.5 Registry Authentication and Authorization Failures | `docker` | docker | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.4.5 Registry Authentication and Authorization Failures | `kubernetes` | Kubernetes | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.4.5 Registry Authentication and Authorization Failures | `nginx` | nginx | correct | the title or the app field names this product |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `kubernetes` | Kubernetes | correct | the title or the app field names this product |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `openshift` | OpenShift | correct | the title or the app field names this product |
| 3.3.25 OpenShift ClusterResourceQuota and AppliedClusterResourceQuota Multi-Project Enforcement Drift, Hierarchical Burn-Rate, and Quota-Selector Coverage Gaps | `opentelemetry` | OpenTelemetry | correct | the title or the app field names this product |
| 3.4.1 Image Push/Pull Audit | `argocd` | argocd | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.4.1 Image Push/Pull Audit | `docker` | Docker | correct | the title or the app field names this product |
| 3.4.1 Image Push/Pull Audit | `github` | github | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.4.1 Image Push/Pull Audit | `gitlab` | gitlab | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.4.1 Image Push/Pull Audit | `jenkins` | jenkins | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.4.1 Image Push/Pull Audit | `kubernetes` | Kubernetes | debatable | the token appears in the search or data sources, not as the subject of the title |
| 3.4.1 Image Push/Pull Audit | `nginx` | nginx | correct | the title or the app field names this product |
| 4.3.27 Cloud Armor WAF Events | `gcp` | gcp | debatable | the token appears in the search or data sources, not as the subject of the title |
| 4.1.320 AWS CloudTrail IAM user listing | `aws` | AWS | correct | the title or the app field names this product |
| 4.3.106 GCP Global forwarding rule create | `gcp` | GCP | correct | the title or the app field names this product |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `azure` | Azure | correct | the title or the app field names this product |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `defender` | Defender | correct | the title or the app field names this product |
| 4.2.88 Azure Defender for Cloud Alert Ingestion | `m365` | microsoft-cloudservices | correct | the title or the app field names this product |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `azure` | Azure | correct | the title or the app field names this product |
| 4.2.234 Azure Network ddosProtectionPlans Create or Update | `m365` | microsoft-cloudservices | correct | the title or the app field names this product |
| 4.1.21 ALB/NLB Access Logs and 5xx Errors | `aws` | aws | correct | the title or the app field names this product |

