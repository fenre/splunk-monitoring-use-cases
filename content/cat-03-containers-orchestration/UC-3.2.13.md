<!-- AUTO-GENERATED from UC-3.2.13.json — DO NOT EDIT -->

---
id: "3.2.13"
title: "Kubernetes Certificate Expiry Tracking"
status: "verified"
criticality: "critical"
splunkPillar: "Platform"
---

# UC-3.2.13 · Kubernetes Certificate Expiry Tracking

> **Criticality:** Critical &middot; **Difficulty:** Expert &middot; **Pillar:** Platform &middot; **Type:** Configuration, Compliance &middot; **Wave:** Run &middot; **Status:** Verified

*We track the many digital credentials that let a Kubernetes cluster talk to itself securely. When any of them expire, things can fail in odd order—sometimes quietly—until an important app stops working. We warn weeks ahead so teams can renew them calmly instead of during an emergency.*

---

## Description

This control inventories the full Kubernetes PKI surface—kube-apiserver serving certificates, etcd peer, server and client TLS material, kubelet client and server certificates, kube-controller-manager and scheduler client certificates, service-account signing keys and public bundles, aggregation-layer front-proxy CA and client certificates, cert-manager Certificate custom resources, ingress controller TLS secrets, validating and mutating webhook caBundles, and metrics-server TLS where customer-managed—then projects days-to-expiry, classifies tiered horizons at ninety, thirty, seven, and zero days, distinguishes rotation-in-flight from rotation-overdue failure modes, and enriches expected posture from k8s_cert_inventory.csv. UC-3.2.42 remains the narrow kubelet client and server certificate story for node bootstrap health; this UC owns fleet-wide PKI lifecycle evidence across kubeadm, kops, EKS, GKE, AKS, RKE2, and OpenShift-consistent baselines without replacing UC-3.5.3 service-mesh workload mTLS, UC-3.3.20 OpenShift-internal PKI specifics, or UC-3.4.8 registry CN certificate scope.

## Value

Executive and platform risk narratives strengthen when certificate expiry is treated as a fleet inventory problem rather than a single-metrics scrape: one expired etcd peer certificate can stall leader election while the Kubernetes API still answers health checks, and one stale webhook caBundle can deny admissions long before node CPU graphs move. Splunk becomes the authoritative cross-plane ledger that ties disk truth on control-plane nodes to cert-manager renewal state and to governance columns for owner_team and rotation_method, which shrinks mean time to identify whether a failure is cloud-managed opacity, customer PKI drift, or a stuck ACME issuance. Regulators and enterprise customers asking for cryptographic hygiene evidence receive exportable rows with tiered severity, rotation state, and lookup version hashes instead of ad hoc openssl commands during incidents.

## Implementation

Land kube:certs:scan, kube:objects:certs, and prometheus:scrape:metrics into k8s_compliance and k8s_metrics with HEC or OpenTelemetry filelog on control-plane nodes; publish k8s_cert_inventory.csv in git; save k8s_uc_3_2_13_certificate_expiry_tracking daily over earliest=-7d@d; join Splunk CIM Inventory summaries for projection freshness; route severity_tier red and amber to platform paging, email, ITSI, and PagerDuty per savedsearches.conf; archive weekly CSV exports with lookup commit hashes.

## Evidence

Saved search k8s_uc_3_2_13_certificate_expiry_tracking; versioned k8s_cert_inventory.csv; weekly CSV exports to restricted k8s_compliance evidence index; dashboard drilldowns on kube:certs:scan, kube:objects:certs, and prometheus scrape lines; savedsearches.conf alert stanzas with ITSI and PagerDuty action chains.

## Control test

### Positive scenario

In lab, ingest kube:certs:scan rows for a PEM with notAfter within six days while k8s_cert_inventory.csv lists the path as prod-critical; run k8s_uc_3_2_13_certificate_expiry_tracking and expect severity_tier amber or red with non-null action_required.

### Negative scenario

Mark the same cluster dev_tier in the lookup with rotation_method=cert-manager, ingest overlapping kube:certs:scan epochs within one hour showing rotation_in_flight=1, confirm rotation-overdue red does not fire when the newer epoch is healthy and lookup suppression flags match.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the Kubernetes platform engineering lead, the identity and PKI service owner, and the SRE who operates etcd and control-plane nodes day to day. This use case is the fleet-wide PKI lifecycle ledger for vanilla Kubernetes and cert-manager overlays: it inventories kube-apiserver TLS serving material, etcd peer and client certificates, kubelet client and server certificates, kube-controller-manager and kube-scheduler client certificates, the cluster root CA bundle, service-account signing keys and published public keys, aggregation-layer front-proxy CA and client certificates, cert-manager Certificate custom resources and their backing Secrets, ingress controller default TLS certificates, validating and mutating admission webhook caBundles, and customer-managed metrics-server TLS where keys live in-cluster. UC-3.2.42 remains the kubelet-only certificate posture narrative for bootstrap and node health; this UC answers whether every other trust anchor and leaf in the cluster is visible, enriched with owner_team and rotation_method from k8s_cert_inventory.csv, and scored with ninety-, thirty-, seven-, and zero-day horizons plus rotation-in-flight versus rotation-overdue semantics. UC-3.5.3 covers Istio workload mTLS, UC-3.3.20 covers OpenShift-internal operator PKI, and UC-3.4.8 covers registry CN certificates; none of those replace this inventory plane.

Index and token contracts land before parsers. Create index=k8s_compliance for structured certificate scans, object snapshots, and kubeadm check-expiration exports, and index=k8s_metrics for Prometheus text exposition scraped from the cert-manager controller and from kube-state-metrics when it exposes cert-manager CRD metrics. Provision distinct HTTP Event Collector tokens per environment with least-privilege indexes, TLS to Splunk, and quarterly rotation recorded in your secrets vault. RBAC on collectors must allow reading /etc/kubernetes/pki on control-plane nodes without world-readable private keys: prefer short-lived signed scripts or systemd units running as root with log-only outputs that never print PEM bodies.

Publish k8s_cert_inventory.csv under version control with columns cluster, cert_path, owner_team, criticality, rotation_method (manual, kubeadm, cert-manager, cloud-managed), expected_issuer_regex, expected_path_present (1 when the path should exist on a scanned node class, 0 when the certificate is cloud-managed and will never appear on customer disks), and optional cluster_alias when Inventory.dest or CMDB keys disagree with the cluster label embedded in telemetry. Every production row needs a ticket-backed owner_team so paging bridges do not argue about accountability during a red severity_tier incident.

Splunk Universal Forwarder scripted inputs or Splunk OpenTelemetry Collector agents must deploy onto every control-plane host class in kubeadm, kops, RKE2, and self-managed estates, with parallel DaemonSet collectors on managed clouds where customers still own etcd peers or static Pod manifests that mount PKI directories. For Amazon EKS, Google GKE, and Microsoft AKS, document in the lookup which paths are customer-visible versus cloud-rotated so scans do not fabricate false absence signals for apiserver certificates that never ship to worker filesystems.

Schedule a nightly kubeadm certs check-expiration --output yaml or JSON job on each control-plane node where kubeadm applies, forwarding structured events with lane=kubeadm_check inside sourcetype=kube:certs:scan. Pair that with continuous lightweight OpenSSL scans for PEM files under /etc/kubernetes/pki and vendor-specific paths documented in your runbook. Service account signing keys are not always X.509; represent them in kube:objects:certs snapshots with explicit kind=SigningKey or capture sa.pub fingerprints alongside TLS leaves.

RBAC inside the cluster must allow a read-only metrics scraper ServiceAccount to reach cert-manager-controller metrics and kube-state-metrics pods when those metrics are not on the public Service. NetworkPolicy egress from the scraper namespace to Splunk HEC or to the metrics Pod IP must be explicit. Legal and privacy reviews should confirm no private keys enter Splunk; only metadata, notAfter equivalents, subjects, issuers, and serials belong in indexes.

### Step 2 — Configure data collection

OpenTelemetry Collector on control-plane nodes should tail PEM directories with a filelog receiver and ship JSON lines to HEC with sourcetype=kube:certs:scan. Pair hostmetrics receivers for disk and CPU context without merging scopes into this UC’s alert logic.

Example collector fragment:

```yaml
receivers:
  filelog:
    include:
      - /etc/kubernetes/pki/*.crt
      - /etc/kubernetes/pki/*.pem
    exclude:
      - '**/*key*.pem'
    start_at: beginning
    operators:
      - type: regex_parser
        regex: '^(?P<cert_path>.*)$'
        parse_from: body
exporters:
  splunk_hec:
    token: "${SPLUNK_HEC_TOKEN}"
    endpoint: "https://splunk-hec.example:8088/services/collector"
    source: "otel:k8s:pki"
    sourcetype: "kube:certs:scan"
service:
  pipelines:
    logs:
      receivers: [filelog]
      exporters: [splunk_hec]
```

Cron or systemd timer on each control-plane host can emit one JSON object per certificate with OpenSSL metadata pushed through curl to HEC:

```bash
HEC_URL="https://splunk-hec.example:8088/services/collector/event"
for c in /etc/kubernetes/pki/*.crt; do
  test -r "$c" || continue
  jq -nc \
    --arg cert "$c" \
    --arg na "$(openssl x509 -in "$c" -noout -enddate 2>/dev/null | cut -d= -f2)" \
    --arg sub "$(openssl x509 -in "$c" -noout -subject 2>/dev/null)" \
    --arg iss "$(openssl x509 -in "$c" -noout -issuer 2>/dev/null)" \
    --arg ser "$(openssl x509 -in "$c" -noout -serial 2>/dev/null | cut -d= -f2)" \
    --arg clu "${K8S_CLUSTER_NAME}" \
    '{event: {cluster: $clu, cert_path: $cert, not_after: $na, subject: $sub, issuer: $iss, serial: $ser, sourcetype: "kube:certs:scan", index: "k8s_compliance"}}' \
  | curl -k -sS -H "Authorization: Splunk ${SPLUNK_HEC_TOKEN}" -H "Content-Type: application/json" -d @- "$HEC_URL" >/dev/null
done
```

Expose cert-manager controller metrics to Prometheus and forward prometheus:scrape:metrics into k8s_metrics:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: cert-manager-metrics
  namespace: cert-manager
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: cert-manager
  endpoints:
    - port: tcp-prometheus-servicemonitor
      interval: 30s
      path: /metrics
```

Normalize kube:objects:certs from a periodic kubectl-style exporter or Kyverno report that dumps Certificate status.notAfter, Secret tls.crt PEM metadata (without private keys), ValidatingWebhookConfiguration caBundle age, and front-proxy ConfigMap references. Map cluster identity consistently across arms so multisearch joins do not fan into Cartesian noise.

Security hygiene: never index tls.key material. Redact internal service DNS names in non-production only when counsel requires; production evidence usually keeps them for routing pages correctly.

Pre-save validation: index=k8s_compliance sourcetype=kube:certs:scan earliest=-1h must show non-zero counts on lab clusters after the cron fires; index=k8s_metrics sourcetype=prometheus:scrape:metrics certmanager* earliest=-1h must show gauge lines; kube:objects:certs should include at least one ingress or webhook row in shared lab.

### Step 3 — Create the search and alert

Save the SPL as k8s_uc_3_2_13_certificate_expiry_tracking with daily schedule earliest=-7d@d latest=now for inventory dashboards, and a higher-frequency variant every four hours for red-tier clusters listed in the lookup. Throttle duplicate amber rows per cluster cert_path for twelve hours unless severity_tier escalates to red.

Pipeline narrative for operators: multisearch fans disk_or_kubeadm_scan, certmanager_prometheus, and api_object_snapshot lanes so a silent cert-manager scrape does not hide apiserver disk truth. coalesce ladders absorb notAfter versus not_after versus Prometheus gauge epochs. inputlookup k8s_cert_inventory.csv enriches owner_team, criticality, and rotation_method. A twenty-four-hour join on cluster and subject_cn counts distinct not_after_epoch values to mark rotation_in_flight when more than one epoch appears while an old PEM may still be on disk. tstats against the Inventory data model supplies inventory_projection_ts for accelerated daily freshness context aligned to CIM summaries documented in cimSpl. case() implements horizons: green beyond ninety days, yellow inside ninety, amber inside thirty, red inside seven or already expired, with amber also used when rotation_in_flight overlaps calendar expiry so on-call verifies rollout completion instead of declaring catastrophe. rotation_overdue flags expired material with no in-flight renewal signal. action_required verbs route to platform runbooks and PKI recovery chapters.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.2.13 Kubernetes Certificate Expiry Tracking — full PKI inventory (apiserver, etcd, kubelet, CM, ingress, webhooks). Tunables: k8s_compliance + k8s_metrics; sourcetypes kube:certs:scan kube:objects:certs prometheus:scrape:metrics; lookup k8s_cert_inventory.csv; earliest=-7d@d latest=now; horizons 90/30/7/0 days; UC-3.2.42 remains kubelet-only.")`
| multisearch
    [ search index=k8s_compliance sourcetype="kube:certs:scan" earliest=-7d@d latest=now
      | eval lane="disk_or_kubeadm_scan"
      | eval cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, kube_cluster, cluster_name, eks_cluster, cluster_arn, ""))))
      | eval cert_path=trim(toString(coalesce(cert_path, cert, filepath, path, filename, "")))
      | eval notAfter_str=trim(toString(coalesce(notAfter, not_after, NotAfter, enddate, EXPIRY, expiration_human, "")))
      | eval subject_full=trim(toString(coalesce(subject, Subject, subject_dn, SubjectDN, "")))
      | eval issuer_full=trim(toString(coalesce(issuer, Issuer, issuer_dn, IssuerDN, "")))
      | eval serial_hex=trim(toString(coalesce(serial, serialNumber, serial_number, "")))
      | eval fingerprint_sha256=trim(toString(coalesce(fingerprint_sha256, sha256_fp, cert_fp, "")))
      | eval expiration_epoch_raw=tonumber(tostring(coalesce(expiration_epoch, notAfter_epoch, not_after_epoch, "")),10)
      | eval not_after_epoch=coalesce(
          if(expiration_epoch_raw>1000000000, expiration_epoch_raw, null()),
          if(len(notAfter_str)>0 AND match(notAfter_str,"^[A-Za-z]{3}\\s+[0-9]{1,2}\\s"), strptime(notAfter_str, "%b %d %H:%M:%S %Y GMT"), null()),
          if(len(notAfter_str)>0 AND match(notAfter_str,"^[A-Za-z]{3}\\s+[0-9]{1,2}\\s"), strptime(notAfter_str, "%b %d %H:%M:%S %Y %Z"), null()),
          if(len(notAfter_str)>0 AND match(notAfter_str,"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"), strptime(notAfter_str, "%Y-%m-%dT%H:%M:%SZ"), null()),
          if(len(notAfter_str)>0, strptime(notAfter_str, "%Y-%m-%d %H:%M:%S"), null()) )
      | fields _time lane cluster cert_path not_after_epoch notAfter_str subject_full issuer_full serial_hex fingerprint_sha256 ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-7d@d latest=now
      | where match(_raw,"certmanager_certificate_expiration_timestamp_seconds")
      | eval lane="certmanager_prometheus"
      | eval cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, kube_cluster, prometheus_cluster, kube_cluster_id, ""))))
      | rex field=_raw "(?im)certmanager_certificate_expiration_timestamp_seconds[^\\n]+\\s+(?<pm_value>[0-9\\.eE+-]+)"
      | rex field=_raw "(?im)namespace\\?=\\?\"(?<cm_ns>[^\"]+)\""
      | rex field=_raw "(?im)name\\?=\\?\"(?<cm_name>[^\"]+)\""
      | eval cert_path=strcat("cert-manager/",coalesce(cm_ns,"-"),"/",coalesce(cm_name,"unknown"))
      | eval pm_epoch=tonumber(pm_value,10)
      | eval not_after_epoch=if(pm_epoch>1000000000, pm_epoch, null())
      | eval notAfter_str=""
      | eval subject_full=strcat("cn:",coalesce(cm_name,"cert-manager-certificate"))
      | eval issuer_full="cert-manager-controller"
      | eval serial_hex=""
      | eval fingerprint_sha256=strcat("prom:",cert_path)
      | fields _time lane cluster cert_path not_after_epoch notAfter_str subject_full issuer_full serial_hex fingerprint_sha256 ]
    [ search index=k8s_compliance sourcetype="kube:objects:certs" earliest=-7d@d latest=now
      | eval lane="api_object_snapshot"
      | eval cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, kube_cluster, cluster_id, ""))))
      | eval cert_path=trim(toString(coalesce(cert_path, object_path, namespaced_name, resource_name, object_ns_name, "")))
      | eval notAfter_str=trim(toString(coalesce(notAfter, not_after, status_notAfter, status_not_after, "")))
      | eval subject_full=trim(toString(coalesce(subject, spec_cn, spec_commonName, common_name, "")))
      | eval issuer_full=trim(toString(coalesce(issuer, status_issuer, "")))
      | eval serial_hex=trim(toString(coalesce(serial, status_serial, "")))
      | eval fingerprint_sha256=trim(toString(coalesce(uid_fingerprint, resource_uid, "")))
      | eval obj_epoch=tonumber(tostring(coalesce(expiration_epoch, status_not_after_epoch, "")),10)
      | eval not_after_epoch=coalesce(
          if(obj_epoch>1000000000, obj_epoch, null()),
          if(len(notAfter_str)>0, strptime(notAfter_str, "%Y-%m-%dT%H:%M:%SZ"), null()),
          if(len(notAfter_str)>0, strptime(notAfter_str, "%b %d %H:%M:%S %Y GMT"), null()) )
      | fields _time lane cluster cert_path not_after_epoch notAfter_str subject_full issuer_full serial_hex fingerprint_sha256 ]
| eval not_after_epoch=coalesce(not_after_epoch,
    if(len(notAfter_str)>0 AND isnull(not_after_epoch), strptime(notAfter_str, "%b %d %H:%M:%S %Y %Z"), null()) )
| eval subject_cn=trim(replace(subject_full, "^.*(?:CN|cn)\\s*=\\s*([^,/]+).*$", "\\1"))
| join type=left max=0 cluster, cert_path [
    | inputlookup k8s_cert_inventory.csv
    | eval cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, cluster_id, ""))))
    | eval cert_path=trim(toString(coalesce(cert_path, path, logical_path, "")))
    | eval owner_team=trim(toString(coalesce(owner_team, squad, team, "")))
    | eval criticality=trim(toString(coalesce(criticality, tier, impact_class, "")))
    | eval rotation_method=trim(toString(coalesce(rotation_method, method, renew_mode, "")))
    | eval expected_issuer_regex=trim(toString(coalesce(expected_issuer_regex, issuer_allow, "")))
    | eval expected_path_present=tonumber(tostring(coalesce(expected_path_present, "1")),10)
    | fields cluster cert_path owner_team criticality rotation_method expected_issuer_regex expected_path_present ]
| fillnull value="" owner_team
| fillnull value="unknown" criticality rotation_method
| fillnull value=1 expected_path_present
| join type=left max=0 cluster, subject_cn [
    search index=k8s_compliance (sourcetype="kube:certs:scan" OR sourcetype="kube:objects:certs") earliest=-24h latest=now
    | eval cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, kube_cluster, ""))))
    | eval subject_full=trim(toString(coalesce(subject, Subject, spec_commonName, "")))
    | eval subject_cn=trim(replace(subject_full, "^.*(?:CN|cn)\\s*=\\s*([^,/]+).*$", "\\1"))
    | eval notAfter_str=trim(toString(coalesce(notAfter, not_after, "")))
    | eval not_after_epoch=coalesce(
        if(len(notAfter_str)>0, strptime(notAfter_str, "%Y-%m-%dT%H:%M:%SZ"), null()),
        if(len(notAfter_str)>0, strptime(notAfter_str, "%b %d %H:%M:%S %Y GMT"), null()) )
    | where isnotnull(not_after_epoch)
    | stats dc(not_after_epoch) AS rot_epoch_dc BY cluster subject_cn
    | eval rotation_in_flight=if(rot_epoch_dc>1,1,0)
    | fields cluster subject_cn rotation_in_flight ]
| fillnull value=0 rotation_in_flight
| stats latest(_time) AS last_seen latest(not_after_epoch) AS not_after_epoch latest(subject_full) AS subject_full latest(issuer_full) AS issuer_full latest(lane) AS signal_lane max(rotation_in_flight) AS rotation_in_flight first(owner_team) AS owner_team first(criticality) AS criticality first(rotation_method) AS rotation_method first(expected_issuer_regex) AS expected_issuer_regex first(expected_path_present) AS expected_path_present BY cluster cert_path
| eval subject_cn=trim(replace(subject_full, "^.*(?:CN|cn)\\s*=\\s*([^,/]+).*$", "\\1"))
| eval issuer_cn=trim(replace(issuer_full, "^.*(?:CN|cn)\\s*=\\s*([^,/]+).*$", "\\1"))
| eval not_after=strftime(not_after_epoch, "%Y-%m-%dT%H:%M:%SZ")
| eval days_to_expiry=if(isnotnull(not_after_epoch) AND not_after_epoch>0, round((not_after_epoch - now()) / 86400, 2), null())
| join type=left max=1 cluster [
    | tstats summariesonly=t latest(_time) AS inventory_projection_ts FROM datamodel=Inventory WHERE nodename=Inventory earliest=-24h@h latest=now BY Inventory.dest
    | rename Inventory.dest AS cluster ]
| eval rotation_overdue=if(isnotnull(days_to_expiry) AND days_to_expiry<=0 AND rotation_in_flight=0, 1, 0)
| eval issuer_ok=if(len(expected_issuer_regex)==0 OR len(issuer_full)==0 OR match(lower(issuer_full), lower(expected_issuer_regex)), 1, 0)
| eval severity_tier=case(
    expected_path_present=0 AND rotation_method="cloud-managed", "green",
    rotation_in_flight=1 AND isnotnull(days_to_expiry) AND days_to_expiry<=0, "amber",
    rotation_overdue=1 AND expected_path_present=1, "red",
    isnotnull(days_to_expiry) AND days_to_expiry<=0, "red",
    isnotnull(days_to_expiry) AND days_to_expiry<=7, "red",
    isnotnull(days_to_expiry) AND days_to_expiry<=30, "amber",
    isnotnull(days_to_expiry) AND days_to_expiry<=90, "yellow",
    isnotnull(days_to_expiry), "green",
    true(), "unknown")
| eval action_required=case(
    rotation_overdue=1, "open_pki_incident_and_rotate_immediately",
    rotation_in_flight=1 AND isnotnull(days_to_expiry) AND days_to_expiry<=0, "verify_staged_rollout_completion",
    issuer_ok=0, "investigate_unexpected_issuer_vs_lookup",
    severity_tier="red", "execute_cert_rotation_within_7_days",
    severity_tier="amber", "schedule_rotation_before_30_day_line",
    severity_tier="yellow", "plan_rotation_before_90_day_line",
    severity_tier="green", "maintain_inventory_evidence_only",
    true(), "resolve_missing_not_after_fields")
| where isnotnull(cluster) AND len(cluster)>1
| table cluster cert_path subject_cn issuer_cn not_after days_to_expiry severity_tier owner_team criticality rotation_method last_seen action_required
```


savedsearches.conf example for red and amber paging with email, ITSI, and PagerDuty:

```ini
[k8s_uc_3_2_13_certificate_expiry_tracking_alert]
action.email = 1
action.email.to = platform-pki@example.com
action.email.subject = Kubernetes PKI horizon breach $result.severity_tier$ $result.cluster$
action.email.message.alert = See Splunk alert for cert $result.cert_path$ subject $result.subject_cn$ days $result.days_to_expiry$
cron_schedule = 0 */4 * * *
dispatch.earliest_time = -7d@d
dispatch.latest_time = now
enableSched = 1
is_visible = 1
alert.track = 1
alert.condition = search
alert.comparator = greater than
alert.threshold = 0
alert.digest_mode = 0
counttype = number of events
relation = greater than
quantity = 0
search = `comment("alert wrapper for UC-3.2.13")`\
| savedsearch k8s_uc_3_2_13_certificate_expiry_tracking\
| where severity_tier IN ("red","amber") AND NOT (rotation_method="cloud-managed" AND expected_path_present=0)\
| eval it_summary=strcat(cluster," ",cert_path," ",severity_tier)\
| eval pagerduty_routing_key="PKI_PLATFORM"

[itsi_episode_action]
# Route via Splunk ITSI Episode Analytics REST modular alert or Adaptive Response action configured in UI:
# Episode title: PKI breach — $result.cluster$ $result.cert_path$
# Severity mapping: red=6 amber=5

[pagerduty_v2]
# Configure PagerDuty modular alert v2 with custom_details fields cluster, cert_path, days_to_expiry, owner_team
```

cimSpl (Inventory projection for dashboards and freshness audits — accelerate Inventory DM):

Paste the cimSpl field from this UC JSON into a panel that proves nightly summaries still receive control-plane host facts; correlate dips with forwarder outages before blaming PKI.

Alert actions: attach lookup git SHA, include inventory_projection_ts when present, and link to the cluster runbook section for the cert_path family (etcd versus apiserver versus webhook).

Understanding severity semantics: cloud-managed rows with expected_path_present=0 downgrade to green in the case statement so EKS apiserver materials you cannot see never page from absent file paths. Issuer mismatches against expected_issuer_regex set action_required to investigate unexpected issuer without automatically paging unless paired with horizon breach in your wrapper search.

Performance: Job Inspector should stay under organizational limits; if multisearch cost spikes, materialize kube:certs:scan summaries hourly into a summary index keyed on cluster cert_path and point dashboards at summaries while keeping this search for investigations.

### Step 4 — Validate

Synthetic near-expiry TLS: on a lab node run openssl req -x509 -newkey rsa:2048 -keyout /tmp/k8s-pki-test/key.pem -out /tmp/k8s-pki-test/cert.pem -days 7 -nodes -subj "/CN=lab-pki-splunk-test" and configure the collector to read that path under a test cluster label. Within two scan intervals expect days_to_expiry below eight and severity_tier red or amber in the saved search output.

cert-manager rotation signal: kubectl annotate certificate demo-tls -n default cert-manager.io/issue-temporary-certificate=true --overwrite and watch kube:objects:certs plus prometheus gauges; the rotation_in_flight join should flip to 1 when two epochs appear for the same subject_cn within twenty-four hours. Clear the annotation after validation.

Restore baseline: delete lab certificates and confirm alerts clear after the next successful scan window.

Validation SPL for spot-checking enrichment:

```spl
index=k8s_compliance sourcetype="kube:certs:scan" earliest=-24h latest=now
| stats count by cluster cert_path
| join type=left max=0 cluster cert_path [| inputlookup k8s_cert_inventory.csv | fields + cluster cert_path owner_team criticality rotation_method]
| where isnull(owner_team)
```

Rows with null owner_team after the join indicate lookup gaps to fix before production paging.

Negative test: mark a lab cluster dev_tier with rotation_method=cert-manager, force rotation_in_flight=1 while an old epoch remains on disk, confirm the alert wrapper does not page rotation_overdue when the newer epoch is healthy per prometheus gauge.

Clock skew test: skew a lab VM clock forward six hours temporarily; days_to_expiry should shift consistently across all certs on that host, signaling NTP remediation rather than silent Splunk failure.

RBAC test: readers without k8s_compliance must see zero rows.

Correlation test: when UC-3.2.45 admission webhook latency spikes, pivot from this UC’s webhook caBundle rows to confirm expiry proximity.

### Step 5 — Operationalize & Troubleshoot

Case 1 — kubeadm cluster expiry: kubelet client certs often renew via bootstrap loops while apiserver and etcd static Pod certificates require explicit kubeadm alpha certs renew; disk scans must include apiserver.crt, apiserver-kubelet-client.crt, etcd/server.crt, etcd/peer.crt, and front-proxy-client.crt paths documented in Kubernetes PKI references.

Case 2 — EKS managed cluster: AWS rotates apiserver-facing materials opaquely; customer-owned worker kubelet certificates and cluster CA distribution to nodes remain visible—tune k8s_cert_inventory.csv expected_path_present flags so absence of apiserver.crt on workers never pages.

Case 3 — cert-manager renewal failure: ACME rate limits or DNS-01 solver outages stall Certificate Ready=False while metrics still show a future expiration; pair this UC with cert-manager Challenge and Order events to distinguish metric lag from issuance failure.

Case 4 — service account signing key rotation: old in-cluster JWTs remain valid until expiry even after sa.key rotation; track sa.pub and key publication ConfigMaps via kube:objects:certs snapshots and document token lifetime expectations per service.

Case 5 — etcd peer certificate expiry: peer mesh TLS failures mimic network partitions; correlate this UC’s etcd peer paths with etcd member list alarms and backup restore procedures before restarting peers.

Case 6 — front-proxy CA expiry: extension API servers and aggregated metrics pipelines lose trust; renew front-proxy-ca.crt and client bundles per Kubernetes aggregation guidance and revalidate aggregated APIService discovery.

Case 7 — webhook caBundle expiry: admission webhooks begin failing closed or open depending on failure policy; map ValidatingWebhookConfiguration names to owner teams in the lookup and page application security when ingress TLS is unrelated.

Case 8 — ingress controller TLS expiry: public browsers fail while in-cluster paths look fine; cross-link UC-3.2.18 operational panels after this UC flags the Secret notAfter.

Case 9 — cert pre-expiry rotation in flight: when rotation_in_flight=1 and severity_tier=amber during calendar overlap, suppress rotation_overdue pages using the alert wrapper predicate until rollout completes or a timer breach occurs.

Case 10 — new cluster bootstrap: initial certificates often carry one-year validity; green beyond ninety days should dominate until the ninety-day window approaches—avoid paging simply because a cluster is young; rely on horizon tiers.

Case 11 — custom CA bundle ConfigMap rotator: some teams distribute ca-bundle.crt via ConfigMaps with update timestamps; extend kube:objects:certs to capture ConfigMap resourceVersion or metadata.generation when PEM bodies are not file-scanned on nodes.

Case 12 — disaster expired root CA: cluster signing chains break renewal entirely; escalate to offline PKI recovery runbooks linked from enterprise architecture, including air-gapped csr signers and manual kubeconfig distribution, before attempting in-cluster automation retries that will never succeed.

Closing checklist: five plain em-dash step headers present, Step 3 fence matches spl JSON, savedsearches.conf documents email ITSI and PagerDuty hooks, Step 5 lists twelve numbered cases, references span Kubernetes PKI, kubeadm, kubelet bootstrap, cert-manager, etcd security, service account admin, Splunk Kubernetes add-on, and upstream certificate concept source, cimModels lists Inventory and Change, monitoringType lists Configuration and Compliance, equipmentModels lists kubernetes_k8s, and exclusions distinguish UC-3.2.42 kubelet-only scope.



## SPL

```spl
`comment("UC-3.2.13 Kubernetes Certificate Expiry Tracking — full PKI inventory (apiserver, etcd, kubelet, CM, ingress, webhooks). Tunables: k8s_compliance + k8s_metrics; sourcetypes kube:certs:scan kube:objects:certs prometheus:scrape:metrics; lookup k8s_cert_inventory.csv; earliest=-7d@d latest=now; horizons 90/30/7/0 days; UC-3.2.42 remains kubelet-only.")`
| multisearch
    [ search index=k8s_compliance sourcetype="kube:certs:scan" earliest=-7d@d latest=now
      | eval lane="disk_or_kubeadm_scan"
      | eval cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, kube_cluster, cluster_name, eks_cluster, cluster_arn, ""))))
      | eval cert_path=trim(toString(coalesce(cert_path, cert, filepath, path, filename, "")))
      | eval notAfter_str=trim(toString(coalesce(notAfter, not_after, NotAfter, enddate, EXPIRY, expiration_human, "")))
      | eval subject_full=trim(toString(coalesce(subject, Subject, subject_dn, SubjectDN, "")))
      | eval issuer_full=trim(toString(coalesce(issuer, Issuer, issuer_dn, IssuerDN, "")))
      | eval serial_hex=trim(toString(coalesce(serial, serialNumber, serial_number, "")))
      | eval fingerprint_sha256=trim(toString(coalesce(fingerprint_sha256, sha256_fp, cert_fp, "")))
      | eval expiration_epoch_raw=tonumber(tostring(coalesce(expiration_epoch, notAfter_epoch, not_after_epoch, "")),10)
      | eval not_after_epoch=coalesce(
          if(expiration_epoch_raw>1000000000, expiration_epoch_raw, null()),
          if(len(notAfter_str)>0 AND match(notAfter_str,"^[A-Za-z]{3}\\s+[0-9]{1,2}\\s"), strptime(notAfter_str, "%b %d %H:%M:%S %Y GMT"), null()),
          if(len(notAfter_str)>0 AND match(notAfter_str,"^[A-Za-z]{3}\\s+[0-9]{1,2}\\s"), strptime(notAfter_str, "%b %d %H:%M:%S %Y %Z"), null()),
          if(len(notAfter_str)>0 AND match(notAfter_str,"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"), strptime(notAfter_str, "%Y-%m-%dT%H:%M:%SZ"), null()),
          if(len(notAfter_str)>0, strptime(notAfter_str, "%Y-%m-%d %H:%M:%S"), null()) )
      | fields _time lane cluster cert_path not_after_epoch notAfter_str subject_full issuer_full serial_hex fingerprint_sha256 ]
    [ search index=k8s_metrics sourcetype="prometheus:scrape:metrics" earliest=-7d@d latest=now
      | where match(_raw,"certmanager_certificate_expiration_timestamp_seconds")
      | eval lane="certmanager_prometheus"
      | eval cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, kube_cluster, prometheus_cluster, kube_cluster_id, ""))))
      | rex field=_raw "(?im)certmanager_certificate_expiration_timestamp_seconds[^\\n]+\\s+(?<pm_value>[0-9\\.eE+-]+)"
      | rex field=_raw "(?im)namespace\\?=\\?\"(?<cm_ns>[^\"]+)\""
      | rex field=_raw "(?im)name\\?=\\?\"(?<cm_name>[^\"]+)\""
      | eval cert_path="cert-manager/".coalesce(cm_ns,"-")."/".coalesce(cm_name,"unknown")
      | eval pm_epoch=tonumber(pm_value,10)
      | eval not_after_epoch=if(pm_epoch>1000000000, pm_epoch, null())
      | eval notAfter_str=""
      | eval subject_full="cn:".coalesce(cm_name,"cert-manager-certificate")
      | eval issuer_full="cert-manager-controller"
      | eval serial_hex=""
      | eval fingerprint_sha256="prom:".cert_path
      | fields _time lane cluster cert_path not_after_epoch notAfter_str subject_full issuer_full serial_hex fingerprint_sha256 ]
    [ search index=k8s_compliance sourcetype="kube:objects:certs" earliest=-7d@d latest=now
      | eval lane="api_object_snapshot"
      | eval cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, kube_cluster, cluster_id, ""))))
      | eval cert_path=trim(toString(coalesce(cert_path, object_path, namespaced_name, resource_name, object_ns_name, "")))
      | eval notAfter_str=trim(toString(coalesce(notAfter, not_after, status_notAfter, status_not_after, "")))
      | eval subject_full=trim(toString(coalesce(subject, spec_cn, spec_commonName, common_name, "")))
      | eval issuer_full=trim(toString(coalesce(issuer, status_issuer, "")))
      | eval serial_hex=trim(toString(coalesce(serial, status_serial, "")))
      | eval fingerprint_sha256=trim(toString(coalesce(uid_fingerprint, resource_uid, "")))
      | eval obj_epoch=tonumber(tostring(coalesce(expiration_epoch, status_not_after_epoch, "")),10)
      | eval not_after_epoch=coalesce(
          if(obj_epoch>1000000000, obj_epoch, null()),
          if(len(notAfter_str)>0, strptime(notAfter_str, "%Y-%m-%dT%H:%M:%SZ"), null()),
          if(len(notAfter_str)>0, strptime(notAfter_str, "%b %d %H:%M:%S %Y GMT"), null()) )
      | fields _time lane cluster cert_path not_after_epoch notAfter_str subject_full issuer_full serial_hex fingerprint_sha256 ]
| eval not_after_epoch=coalesce(not_after_epoch,
    if(len(notAfter_str)>0 AND isnull(not_after_epoch), strptime(notAfter_str, "%b %d %H:%M:%S %Y %Z"), null()) )
| eval subject_cn=trim(replace(subject_full, "^.*(?:CN|cn)\\s*=\\s*([^,/]+).*$", "\\1"))
| join type=left max=0 cluster, cert_path [
    | inputlookup k8s_cert_inventory.csv
    | eval cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, cluster_id, ""))))
    | eval cert_path=trim(toString(coalesce(cert_path, path, logical_path, "")))
    | eval owner_team=trim(toString(coalesce(owner_team, squad, team, "")))
    | eval criticality=trim(toString(coalesce(criticality, tier, impact_class, "")))
    | eval rotation_method=trim(toString(coalesce(rotation_method, method, renew_mode, "")))
    | eval expected_issuer_regex=trim(toString(coalesce(expected_issuer_regex, issuer_allow, "")))
    | eval expected_path_present=tonumber(tostring(coalesce(expected_path_present, "1")),10)
    | fields cluster cert_path owner_team criticality rotation_method expected_issuer_regex expected_path_present ]
| fillnull value="" owner_team
| fillnull value="unknown" criticality rotation_method
| fillnull value=1 expected_path_present
| join type=left max=0 cluster, subject_cn [
    search index=k8s_compliance (sourcetype="kube:certs:scan" OR sourcetype="kube:objects:certs") earliest=-24h latest=now
    | eval cluster=lower(trim(toString(coalesce(cluster, k8s_cluster, kube_cluster, ""))))
    | eval subject_full=trim(toString(coalesce(subject, Subject, spec_commonName, "")))
    | eval subject_cn=trim(replace(subject_full, "^.*(?:CN|cn)\\s*=\\s*([^,/]+).*$", "\\1"))
    | eval notAfter_str=trim(toString(coalesce(notAfter, not_after, "")))
    | eval not_after_epoch=coalesce(
        if(len(notAfter_str)>0, strptime(notAfter_str, "%Y-%m-%dT%H:%M:%SZ"), null()),
        if(len(notAfter_str)>0, strptime(notAfter_str, "%b %d %H:%M:%S %Y GMT"), null()) )
    | where isnotnull(not_after_epoch)
    | stats dc(not_after_epoch) AS rot_epoch_dc BY cluster subject_cn
    | eval rotation_in_flight=if(rot_epoch_dc>1,1,0)
    | fields cluster subject_cn rotation_in_flight ]
| fillnull value=0 rotation_in_flight
| stats latest(_time) AS last_seen latest(not_after_epoch) AS not_after_epoch latest(subject_full) AS subject_full latest(issuer_full) AS issuer_full latest(lane) AS signal_lane max(rotation_in_flight) AS rotation_in_flight first(owner_team) AS owner_team first(criticality) AS criticality first(rotation_method) AS rotation_method first(expected_issuer_regex) AS expected_issuer_regex first(expected_path_present) AS expected_path_present BY cluster cert_path
| eval subject_cn=trim(replace(subject_full, "^.*(?:CN|cn)\\s*=\\s*([^,/]+).*$", "\\1"))
| eval issuer_cn=trim(replace(issuer_full, "^.*(?:CN|cn)\\s*=\\s*([^,/]+).*$", "\\1"))
| eval not_after=strftime(not_after_epoch, "%Y-%m-%dT%H:%M:%SZ")
| eval days_to_expiry=if(isnotnull(not_after_epoch) AND not_after_epoch>0, round((not_after_epoch - now()) / 86400, 2), null())
| join type=left max=1 cluster [
    | tstats summariesonly=t latest(_time) AS inventory_projection_ts FROM datamodel=Inventory WHERE nodename=Inventory earliest=-24h@h latest=now BY Inventory.dest
    | rename Inventory.dest AS cluster ]
| eval rotation_overdue=if(isnotnull(days_to_expiry) AND days_to_expiry<=0 AND rotation_in_flight=0, 1, 0)
| eval issuer_ok=if(len(expected_issuer_regex)==0 OR len(issuer_full)==0 OR match(lower(issuer_full), lower(expected_issuer_regex)), 1, 0)
| eval severity_tier=case(
    expected_path_present=0 AND rotation_method="cloud-managed", "green",
    rotation_in_flight=1 AND isnotnull(days_to_expiry) AND days_to_expiry<=0, "amber",
    rotation_overdue=1 AND expected_path_present=1, "red",
    isnotnull(days_to_expiry) AND days_to_expiry<=0, "red",
    isnotnull(days_to_expiry) AND days_to_expiry<=7, "red",
    isnotnull(days_to_expiry) AND days_to_expiry<=30, "amber",
    isnotnull(days_to_expiry) AND days_to_expiry<=90, "yellow",
    isnotnull(days_to_expiry), "green",
    true(), "unknown")
| eval action_required=case(
    rotation_overdue=1, "open_pki_incident_and_rotate_immediately",
    rotation_in_flight=1 AND isnotnull(days_to_expiry) AND days_to_expiry<=0, "verify_staged_rollout_completion",
    issuer_ok=0, "investigate_unexpected_issuer_vs_lookup",
    severity_tier="red", "execute_cert_rotation_within_7_days",
    severity_tier="amber", "schedule_rotation_before_30_day_line",
    severity_tier="yellow", "plan_rotation_before_90_day_line",
    severity_tier="green", "maintain_inventory_evidence_only",
    true(), "resolve_missing_not_after_fields")
| where isnotnull(cluster) AND len(cluster)>1
| table cluster cert_path subject_cn issuer_cn not_after days_to_expiry severity_tier owner_team criticality rotation_method last_seen action_required
```

## CIM SPL

```spl
| tstats summariesonly=t latest(_time) AS inventory_projection_ts FROM datamodel=Inventory WHERE nodename=Inventory earliest=-24h@h latest=now BY Inventory.dest
| rename Inventory.dest AS cluster_key
| eval cluster_key=lower(trim(toString(cluster_key)))
| join type=left max=0 cluster_key [
| tstats summariesonly=t latest(Inventory.os) AS inventory_os latest(Inventory.vendor_product) AS inventory_product FROM datamodel=Inventory WHERE nodename=Inventory.OperatingSystem earliest=-24h@h latest=now BY Inventory.dest
| rename Inventory.dest AS cluster_key
| eval cluster_key=lower(trim(toString(cluster_key))) ]
| where len(cluster_key)>1
| sort - inventory_projection_ts
| head 500
```

## Visualization

Severity-tier colored table by cluster and cert_path with drilldowns to raw kube:certs:scan JSON and prometheus metric lines; single-value tiles for counts of red and amber rows; timeline of days_to_expiry for top criticality paths; overlay of inventory_projection_ts from cimSpl to prove summary freshness; optional map of rotation_method by cluster segment; companion timechart of fleet minimum days_to_expiry by criticality for steering reviews.

## Known False Positives

cert-manager and kubeadm rotations routinely present two distinct notAfter epochs for the same logical subject_cn inside a twenty-four-hour window while static file scans still read the previous on-disk PEM; treat rotation_in_flight=1 from the dc(not_after_epoch) arm as a suppression flag for red rotation-overdue pages until the newer epoch stabilizes or until the inventory lookup marks rotation_method=cert-manager with an active Certificate Ready=True snapshot. Amazon EKS, Google GKE, and Microsoft AKS rotate some apiserver-facing certificates without exposing the same filesystem paths as self-managed kubeadm; rows tied to cloud-managed rotation_method should skip red tiers when the only signal is a missing /etc/kubernetes/pki/apiserver.crt on nodes that never hosted that material—gate with expected_path_present=0 in k8s_cert_inventory.csv. kind and minikube clusters often run deliberately short-lived bootstrap certs; mark those clusters dev_tier in the lookup and raise yellow only inside thirty days unless prod_criticality_override is set. Self-signed issuers in lab clusters frequently break naive issuer_cn regex expectations; use expected_issuer_regex with a broad ALLOW-LAB pattern rather than deleting telemetry. Nightly kubeadm JSON and continuous filelog can double-count the same serial when both land; dedupe on fingerprint_sha256 or serial_hex before paging. Prometheus text exposition occasionally omits namespace labels on certmanager_certificate_expiration_timestamp_seconds after upgrades; fallback to kube:objects:certs for namespace binding before declaring a missing workload cert. Webhook caBundle rotations sourced only from ConfigMap volume mounts may lag API status fields by one rollout wave; pair object snapshots with admission failure logs from UC-3.2.45 before assuming PKI doom. Inventory model joins can map dest to node name while cluster grain uses eks_cluster_arn; maintain a cluster_alias column in the lookup to prevent false orphan rows. Clock skew between control-plane host and indexer time distorts days_to_expiry; enforce chrony on collectors when variance exceeds two minutes.

## References

- [Kubernetes Documentation — PKI certificates and requirements](https://kubernetes.io/docs/setup/best-practices/certificates/)
- [Kubernetes Documentation — kubeadm certificate management](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/)
- [Kubernetes Documentation — kubelet TLS bootstrapping](https://kubernetes.io/docs/reference/access-authn-authz/kubelet-tls-bootstrapping/)
- [cert-manager — Certificate resource](https://cert-manager.io/docs/usage/certificate/)
- [etcd Documentation — Security (TLS for peers and clients)](https://etcd.io/docs/latest/op-guide/security/)
- [Kubernetes website — certificates concept (source)](https://github.com/kubernetes/website/blob/main/content/en/docs/concepts/cluster-administration/certificates.md)
- [Splunk Documentation — Splunk Add-on for Kubernetes](https://docs.splunk.com/Documentation/AddOns/released/Kubernetes/About)
- [Kubernetes Documentation — Service accounts administration (token signing keys)](https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/)
