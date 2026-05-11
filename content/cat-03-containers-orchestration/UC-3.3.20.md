<!-- AUTO-GENERATED from UC-3.3.20.json — DO NOT EDIT -->

---
id: "3.3.20"
title: "Cluster Certificate Expiry"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.3.20 · Cluster Certificate Expiry

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*The platform issues many internal trust credentials so its own parts can talk safely. When an important one expires, administration can fail—sometimes without an obvious alarm. We keep an inventory, warn well ahead, and escalate faster when a renewal still needs a human approval step.*

---

## Description

Detects operator-managed OpenShift control-plane PKI expiry and degradation across openshift-kube-apiserver-operator, openshift-etcd-operator, openshift-ingress-operator, openshift-service-ca-operator, cluster-monitoring-operator, authentication-operator, image-registry-operator, and console-operator surfaces: internal serving and client certificates, signer chains, trust bundles such as openshift-config-managed server and controller-manager client CAs, service-ca signing-cabundle, ingress router-ca and default certs, OAuth serving certs, monitoring client certs, registry and console route TLS defaults, and etcd peer and server material. The analytic multisearches openshift:certificates and openshift:secret digest events, prometheus:metrics apiserver_client_certificate_expiration_seconds series, and openshift:operator ClusterOperator hints, applies coalesce() for notAfter field drift, joins openshift_cert_policy.csv for rotation_policy and signer metadata, uses eventstats and streamstats for cluster and category minima, and emits page, warn, info, or inventory severities with recommended_action verbs that distinguish auto-rotated operator paths, manual kube-apiserver-to-kubelet signer approvals, and external corporate CA responsibilities. UC-3.2.13 covers generic Kubernetes PKI inventory; UC-3.2.42 covers kubelet CSR auto-rotation health; UC-3.3.8 covers customer Route edge TLS.

## Value

Executive and platform risk narratives strengthen when OpenShift internal PKI is treated as an operator contract problem rather than a one-off openssl ticket: one expiring kube-apiserver-to-kubelet signer can strand node credentials while the control plane still answers probes, one stale service CA can invalidate hundreds of service-serving secrets simultaneously, and one OAuth or ingress default expiry can lock administrators out before workload graphs move. Splunk preserves a tamper-resistant ledger tying Secret digest metadata, Prometheus apiserver client horizons, and ClusterOperator degradation text so auditors see continuous coverage of openshift-config-managed trust anchors, router-ca, monitoring scraper identities, and etcd TLS—not ad hoc oc queries during outages. Mean time to remediate improves because responders see rotation_policy and operator_owner columns that route to the right runbook before teams argue about whether the symptom is edge TLS, generic Kubernetes PKI, or kubelet-only renewal.

## Implementation

Land openshift:certificates, openshift:secret, prometheus:metrics, and openshift:operator into index=openshift with cluster labels aligned to management context; publish openshift_cert_policy.csv in git; save openshift_uc_3_3_20_cluster_certificate_expiry on a four-hour cadence over earliest=-7d@d latest=now; route page and warn severities to platform on-call with webhook or email; archive weekly CSV exports with lookup commit hashes for crypto governance reviews.

## Evidence

Saved search openshift_uc_3_3_20_cluster_certificate_expiry; versioned openshift_cert_policy.csv in git; weekly CSV exports to restricted openshift evidence index; dashboard drilldowns on openshift:certificates, openshift:secret, openshift:operator, and prometheus:metrics; alert stanza with platform routing keys.

## Control test

### Positive scenario

In a lab OpenShift cluster, ingest openshift:certificates events for a PEM leaf with notAfter within five days in openshift-config-managed while openshift_cert_policy.csv lists rotation_policy auto; run openshift_uc_3_3_20_cluster_certificate_expiry and expect severity page or warn with non-null recommended_action.

### Negative scenario

In the same cluster after guided operator renewal extends notAfter beyond one hundred twenty days with matching oc get secret verification, confirm severities return to inventory or info and the alert wrapper emits zero rows when filtering to page and warn only.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the OpenShift platform engineering lead, the cluster lifecycle team that carries break-glass kubeconfig access, and the observability engineers who operate Splunk HTTP Event Collector tokens plus OpenTelemetry Collector DaemonSets that federate in-cluster Prometheus. This use case isolates operator-managed control-plane PKI on Red Hat OpenShift Container Platform: the internal trust material issued and rotated by openshift-kube-apiserver-operator, openshift-etcd-operator, openshift-ingress-operator, openshift-service-ca-operator, cluster-monitoring-operator, authentication-operator, image-registry-operator, console-operator, and adjacent Cluster Operators that publish CA bundles such as openshift-config-managed kube-apiserver-server-ca, kube-controller-manager-client-ca, openshift-service-ca signing-cabundle, openshift-ingress-operator router-ca, etcd peer and server secrets, monitoring client certificates for Thanos and Prometheus scrapes, OAuth serving certificates, default ingress certificates, image-registry route TLS, and console route TLS that are part of the platform contract rather than arbitrary customer Routes. UC-3.2.13 remains the vanilla Kubernetes fleet PKI inventory across kubeadm disk paths, cert-manager objects, and generic Secret snapshots; this UC does not duplicate that axis. UC-3.2.42 remains the kubelet CSR renewal pipeline on worker nodes. UC-3.3.8 remains customer-facing Route and edge TLS, cert-manager integrations, and CDN-pinned hostname risk. Splunk becomes the reconciliation ledger that ties scripted Secret digest events, kube_secret_metadata style enrichment, apiserver_client_certificate_expiration_seconds from OpenShift Monitoring, and ClusterOperator degradation hints into one row per cluster, namespace, and secret with rotation_policy classification from openshift_cert_policy.csv.

Index and ACL contracts land before parsers. Designate index=openshift for openshift:certificates structured events emitted by a certificate inventory job, openshift:secret for TLS Secret snapshots produced by oc get secret -A -o json style exporters that never ship private keys, prometheus:metrics for federated OpenShift Monitoring scrapes that include apiserver_client_certificate_expiration_seconds and optional kube_secret_metadata helpers when your collector maps Prometheus labels into indexed fields, and openshift:operator for ClusterOperator status snapshots that include Degraded, Progressing, and Available conditions with messages referencing signer exhaustion, trust bundle propagation, or etcd TLS faults. Issue distinct HEC tokens per environment with least privilege: platform SRE roles may search all four sourcetypes; application teams receive filtered views that exclude openshift-config-managed bodies if counsel requires minimization. Retention should cover at least two full certificate-rotation cycles for your enterprise standard, typically ninety to one hundred eighty days hot, so post-incident reviewers can replay operator rollouts without cold-store latency.

Publish openshift_cert_policy.csv under version control with columns cluster, namespace, secret_name, rotation_policy starting values auto, manual, or external, operator_owner matching the responsible Cluster Operator name, ca_bundle_kind labels such as kube_apiserver_serving, etcd_peer, etcd_server, service_ca_signing, ingress_default, oauth_serving, monitoring_client, registry_route, console_route, kube_apiserver_to_kubelet, signer_chain_status seeds like chain_ok_or_unknown, optional days_until_signer_expiry when you run offline openssl comparisons against parent CA material, and recommended_action_hint verbs for runbook deep links. Include explicit rows for openshift-config-managed secrets that back kube-apiserver-server-ca and kube-controller-manager-client-ca, openshift-service-ca signing-cabundle ConfigMap and service-serving signer secrets, openshift-ingress-operator default-certificate references, openshift-authentication v4-0-0-system-master-auth serving cert, openshift-monitoring prometheus and thanos client secrets, openshift-image-registry route defaults, and openshift-console console TLS routes. Every production row needs an accountable operator_owner because paging without ownership wastes the first thirty minutes of an incident.

RBAC and safety: the inventory job must use a dedicated ServiceAccount with get/list on secrets in enumerated namespaces, not cluster-admin on laptops. Run collectors from a hardened management host or CI worker with short-lived kubeconfigs. Legal review should confirm that Splunk never stores tls.key entries; only metadata, PEM leaf notAfter equivalents, subjects, issuers, and stable fingerprints belong in indexes. For etcd namespaces, restrict which analysts can read events that include peer DNS names.

Field normalization: exporters should emit first PEM leaf notAfter or expiry_epoch, cn, issuer, cluster or openshift_cluster; Prometheus labels must match Secret exports; ClusterOperator snapshots need name plus condition message text for cert and tls substring tests.

Risk briefing: many leaves auto-rotate while kube-apiserver-to-kubelet signers may still need manual approvals; service CA expiry strands many service-serving secrets; stale telemetry during healthy rotation can look catastrophic unless generation and histograms agree; short trust-bundle propagation blips differ from true Not After breaches.

Differentiation recap: operator-managed internal PKI and platform defaults—not generic Kubernetes PKI inventory, kubelet-only CSR health, or customer edge Route customization alone.

### Step 2 — Configure data collection

Stand up four complementary lanes Splunk multisearch can fuse: scripted certificate inventory events, TLS Secret snapshots, federated Prometheus metrics from OpenShift Monitoring, and ClusterOperator status exports.

Certificate inventory lane: schedule a Python or Go utility every six hours from a management host with kubeconfig authentication. The utility should iterate namespaces openshift-kube-apiserver, openshift-kube-controller-manager, openshift-kube-scheduler, openshift-etcd, openshift-config-managed, openshift-service-ca, openshift-ingress-operator, openshift-authentication, openshift-monitoring, openshift-image-registry, openshift-console, and other namespaces your openshift_cert_policy.csv enumerates, calling oc get secret -n <ns> -o json for typed kubernetes.io/tls and opaque bundles that carry tls.crt. Parse each PEM leaf with a safe parser, emit one HEC JSON event per leaf with sourcetype=openshift:certificates, fields cluster, namespace, secret_name, notAfter or expiry_epoch, cn, issuer, cert_category derived from secret name patterns, owning_operator inferred from namespace, and last_rotation_ts when metadata.annotations include known rotation timestamps. Never send tls.key.

Secret snapshot lane: optionally run a wider oc get secret -A -o json exporter on a longer cadence for governance, landing sourcetype=openshift:secret with kube_secret_metadata style fields when your forwarder maps metadata.generation, resourceVersion, uid, and type. Keep TLS bodies out of _raw when counsel requires; you can ship only parsed metadata to Splunk while retaining openssl validation on the collector host.

Metrics lane: enable platform monitoring federation per OpenShift documentation, scrape apiserver_client_certificate_expiration_seconds from the kube-apiserver Prometheus endpoint or aggregated monitoring targets, and forward lines into index=openshift with sourcetype=prometheus:metrics using an OpenTelemetry Collector prometheus receiver. Preserve labels that identify client signer or CN when present. Validate that apiserver_client_certificate_expiration_seconds_bucket histogram series appear when you query the monitoring stack directly so Splunk mirrors the same distribution you will spot-check during validation.

ClusterOperator lane: schedule oc get clusteroperator -o json snapshots every five to fifteen minutes, flatten conditions into events with sourcetype=openshift:operator, and retain message text for Degraded=True rows. Map name to openshift_cluster_version compatible cluster labels.

Example openssl spot-check on the collector host after extracting a tls.crt to a temp file without indexing the file contents:

```bash
openssl x509 -in /tmp/leaf.pem -noout -subject -issuer -enddate
```

Example HEC curl skeleton for openshift:certificates events:

```bash
jq -nc --arg clu "$OCP_CLUSTER" --arg ns "$NS" --arg sec "$SEC" \
  --arg cn "$CN" --arg iss "$ISS" --arg na "$NOT_AFTER" \
  '{event:{cluster:$clu,namespace:$ns,secret_name:$sec,cn:$cn,issuer:$iss,notAfter:$na,sourcetype:"openshift:certificates",index:"openshift"}}' \
| curl -sS -H "Authorization: Splunk $HEC" -H "Content-Type: application/json" \
    "https://splunk-hec.example:8088/services/collector/event" -d @-
```

props.conf guidance: TRUNCATE sufficiently large for JSON, TIMESTAMP_FIELDS respected when HEC time is authoritative, and FIELDALIAS rules that copy metadata.generation into resource_generation when using indexed extractions.

Pre-flight searches operators should run before saving alerts:

```text
index=openshift sourcetype="openshift:certificates" earliest=-24h latest=now | head 20
index=openshift sourcetype="prometheus:metrics" apiserver_client_certificate_expiration_seconds earliest=-24h latest=now | head 20
index=openshift sourcetype="openshift:operator" earliest=-24h latest=now | head 20
```

Zero-result investigations should block production paging until collectors succeed.

Implementation note: openshift_cert_policy.csv is the rotation class matrix—mark manual where docs still require approval, auto for full operator rollout, external for corporate CA or default ingress PEM chains; record signer-of-signers in signer_chain_status and optional days_until_signer_expiry from offline openssl parent checks.

### Step 3 — Create the search and alert

Save the SPL as openshift_uc_3_3_20_cluster_certificate_expiry with a four-hour schedule for inventory dashboards and a one-hour variant for page-tier clusters listed in openshift_cert_policy.csv with criticality markers you maintain in an extended column. Dispatch earliest=-7d@d and latest=now to reduce snapshot bias while still capturing weekly operator cycles. Throttle duplicate cluster, namespace, secret_name rows for forty-five minutes unless severity escalates from info to warn or page.

Pipeline narrative for reviewers: multisearch fans secret and certificate inventory lanes, Prometheus apiserver client expiration metrics, and ClusterOperator degradation hints so a silent metrics outage does not hide a genuinely Degraded etcd or authentication operator. coalesce() ladders absorb notAfter versus expiry_epoch versus prometheus _value style fields versus cert_not_after aliases your parsers emit. inputlookup openshift_cert_policy.csv enriches rotation_policy, operator_owner, ca_bundle_kind, signer_chain_status, days_until_signer_expiry, and recommended_action_hint without hard-coding every secret name inside SPL. eventstats computes days_until_min_expiry per cluster for fleet-wide soonest-expiry captions. streamstats computes cat_fastest_expiry per cluster and ca_bundle_kind to highlight the hottest category bucket even when multiple secrets exist. case() maps severities to page inside seven days, warn inside thirty days, info inside ninety days, and inventory beyond ninety days or when expiry is unknown but telemetry is healthy. ClusterOperator cert_degraded hints synthesize a synthetic near-term horizon only when messages substantiate TLS or signer faults, nudging severity toward page without fabricating a notAfter. recommended_action verbs route to OpenShift certificate runbooks, oc adm certificate approve procedures for kubelet client signer emergencies, ingress and OAuth renewal steps, and monitoring client recycle flows.

Fenced SPL must match the spl JSON field exactly:

```spl
`comment("UC-3.3.20 OpenShift operator-managed control-plane PKI — openshift:secret/openshift:certificates, prometheus apiserver_client_certificate_expiration_seconds, openshift:operator ClusterOperator hints. Join openshift_cert_policy.csv. earliest=-7d@d latest=now; severities page<=7d warn<=30d info<=90d else inventory")`
| multisearch
    [ search index=openshift (sourcetype="openshift:secret" OR sourcetype="openshift:certificates") earliest=-7d@d latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, secret_namespace, metadata_namespace, ""))))
      | eval secret_name=lower(trim(toString(coalesce(secret_name, name, metadata_name, object_name, ""))))
      | eval lane="secret_or_cert_scan"
      | eval cert_degraded=0
      | eval na_str=trim(toString(coalesce(notAfter, not_after, cert_not_after, tls_not_after, "")))
      | eval epoch_raw=tonumber(tostring(coalesce(expiry_epoch, notAfter_epoch, not_after_epoch, cert_expiry_epoch, "")),10)
      | eval prom_like=tonumber(tostring(coalesce(_value, metric_value, prom_value, "")),10)
      | eval not_after_epoch=coalesce(
          if(epoch_raw>1000000000, epoch_raw, null()),
          if(prom_like>1000000000, prom_like, null()),
          if(len(na_str)>0 AND match(na_str,"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"), strptime(na_str, "%Y-%m-%dT%H:%M:%SZ"), null()),
          if(len(na_str)>0 AND match(na_str,"^[A-Za-z]{3}\\s+[0-9]{1,2}\\s"), strptime(na_str, "%b %d %H:%M:%S %Y GMT"), null()),
          if(len(na_str)>0, strptime(na_str, "%Y-%m-%d %H:%M:%S"), null()) )
      | eval cert_subject_cn=trim(toString(coalesce(cn, common_name, subject_cn, tls_cn, cert_cn, "")))
      | eval cert_issuer=trim(toString(coalesce(issuer, tls_issuer, issuer_dn, cert_issuer_x509, "")))
      | eval ca_bundle_kind=lower(trim(toString(coalesce(cert_category, pki_class, bundle_kind, "openshift_operator_tls_secret"))))
      | eval operator_owner=trim(toString(coalesce(owning_operator, operator, ocp_operator, "")))
      | eval last_rot_epoch=tonumber(tostring(coalesce(last_rotation_ts, secret_last_renewal_epoch, "")),10)
      | eval prom_metric_seen="no"
      | fields _time cluster namespace secret_name lane not_after_epoch cert_subject_cn cert_issuer ca_bundle_kind operator_owner last_rot_epoch prom_metric_seen cert_degraded ]
    [ search index=openshift sourcetype="prometheus:metrics" earliest=-7d@d latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | where mn="apiserver_client_certificate_expiration_seconds" OR like(mn,"apiserver_client_certificate_expiration_seconds%")
      | eval lane="prom_apiserver_client_cert"
      | eval cert_degraded=0
      | eval mv=tonumber(tostring(coalesce(value, metric_value, _value, Value, "")), 10)
      | eval not_after_epoch=if(isnotnull(mv) AND mv>1000000000 AND mv<4000000000, mv, null())
      | eval namespace="openshift-kube-apiserver"
      | eval secret_name="prom__apiserver_client_certificate_expiration_seconds"
      | eval cert_subject_cn=trim(toString(coalesce(client_cn, cn, signer_name, "apiserver_authenticated_client")))
      | eval cert_issuer=trim(toString(coalesce(issuer_cn, "kubernetes_ca_signer")))
      | eval ca_bundle_kind="apiserver_client_cert_metric"
      | eval operator_owner="openshift-kube-apiserver-operator"
      | eval last_rot_epoch=null()
      | eval prom_metric_seen="yes"
      | fields _time cluster namespace secret_name lane not_after_epoch cert_subject_cn cert_issuer ca_bundle_kind operator_owner last_rot_epoch prom_metric_seen cert_degraded ]
    [ search index=openshift sourcetype="openshift:operator" earliest=-7d@d latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval co_name=lower(trim(toString(coalesce(name, clusteroperator_name, metadata_name, ""))))
      | eval lane="clusteroperator_status"
      | where like(co_name,"kube-apiserver%") OR co_name=="etcd" OR like(co_name,"ingress%") OR like(co_name,"monitoring") OR co_name=="authentication" OR co_name=="image-registry" OR co_name=="console" OR co_name=="service-ca"
      | eval cond_msg=lower(trim(toString(coalesce(message, reason, status_message, condition_message, ""))))
      | eval cert_degraded=if(match(cond_msg,"cert|tls|x509|expir|signer|ca bundle|trust bundle|rotate|pem"),1,0)
      | where cert_degraded=1
      | eval not_after_epoch=null()
      | eval namespace="openshift-cluster-version"
      | eval secret_name=strcat("clusteroperator__",co_name)
      | eval cert_subject_cn=strcat("clusteroperator:",co_name)
      | eval cert_issuer="cluster_operator_condition"
      | eval ca_bundle_kind="clusteroperator_cert_hint"
      | eval operator_owner=co_name
      | eval last_rot_epoch=null()
      | eval prom_metric_seen="no"
      | fields _time cluster namespace secret_name lane not_after_epoch cert_subject_cn cert_issuer ca_bundle_kind operator_owner last_rot_epoch prom_metric_seen cert_degraded ]
    [ search index=openshift (sourcetype="openshift:operator" OR sourcetype="openshift:event") earliest=-7d@d latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, involvedObject_namespace, ""))))
      | eval secret_name=lower(trim(toString(coalesce(involvedObject_name, secret_name, name, ""))))
      | eval evt_reason=lower(trim(toString(coalesce(reason, event_reason, ""))))
      | eval evt_msg=lower(trim(toString(coalesce(message, event_message, _raw, ""))))
      | where match(evt_reason, "rotated|reissued|signed|expir|csrapproved|signerupdated") OR match(evt_msg, "certificate.*(rotat|reissu|sign|expir)")
      | stats count AS rotation_evt_count, max(_time) AS last_rotation_evt_time, values(evt_reason) AS rotation_evt_reasons BY cluster namespace secret_name
      | eval lane="cert_rotation_signal"
      | eval cert_degraded=0
      | eval na_str=""
      | eval epoch_raw=null()
      | eval prom_like=null()
      | eval not_after_epoch=null()
      | eval cert_subject_cn=""
      | eval cert_issuer=""
      | eval _time=last_rotation_evt_time
      | fields _time cluster namespace secret_name lane cert_degraded not_after_epoch cert_subject_cn cert_issuer rotation_evt_count last_rotation_evt_time rotation_evt_reasons ]
| eval not_after_epoch=if(cert_degraded=1 AND isnull(not_after_epoch), relative_time(now(),"+1d@d"), not_after_epoch)
| eval days_until_expiry=if(isnotnull(not_after_epoch) AND not_after_epoch>0, round((not_after_epoch - now()) / 86400, 2), null())
| eval last_rotation_age_days=if(isnotnull(last_rot_epoch) AND last_rot_epoch>1000000000, round((now()-last_rot_epoch)/86400, 2), null())
| join type=left max=0 cluster, namespace, secret_name [
    | inputlookup openshift_cert_policy.csv
    | eval cluster=lower(trim(toString(cluster)))
    | eval namespace=lower(trim(toString(namespace)))
    | eval secret_name=lower(trim(toString(secret_name)))
    | eval rotation_policy=lower(trim(toString(coalesce(rotation_policy, rotation_class, "auto"))))
    | eval operator_owner_lu=trim(toString(coalesce(operator_owner, owning_operator, "")))
    | eval ca_bundle_kind_lu=lower(trim(toString(coalesce(ca_bundle_kind, pki_bucket, ""))))
    | eval signer_chain_status=trim(toString(coalesce(signer_chain_status, chain_hint, "unknown")))
    | eval days_until_signer_expiry=tonumber(tostring(coalesce(days_until_signer_expiry, signer_days_remaining, "")),10)
    | eval recommended_action_hint=trim(toString(coalesce(recommended_action_hint, "")))
    | fields cluster namespace secret_name rotation_policy operator_owner_lu ca_bundle_kind_lu signer_chain_status days_until_signer_expiry recommended_action_hint ]
| fillnull value="auto" rotation_policy
| fillnull value="" operator_owner_lu ca_bundle_kind_lu signer_chain_status recommended_action_hint
| eval operator_owner=if(len(operator_owner_lu)>0, operator_owner_lu, operator_owner)
| eval ca_bundle_kind=if(len(ca_bundle_kind_lu)>0, ca_bundle_kind_lu, ca_bundle_kind)
| eventstats min(days_until_expiry) AS days_until_min_expiry BY cluster
| streamstats window=20000 current=t global=f min(days_until_expiry) AS cat_fastest_expiry BY cluster ca_bundle_kind
| eval severity=case(
    isnull(days_until_expiry), "inventory",
    days_until_expiry<=7, "page",
    days_until_expiry<=30, "warn",
    days_until_expiry<=90, "info",
    true(), "inventory")
| eval rotation_policy=case(
    match(lower(ca_bundle_kind),"ingress_default|oauth-serving|registry_public|console_public|passthrough_edge"), "external",
    match(lower(ca_bundle_kind),"kube_apiserver_to_kubelet|csr_signer|manual_kubelet_client"), "manual",
    match(lower(rotation_policy),"manual|csr|approve"), "manual",
    match(lower(rotation_policy),"external|edge|custom_ca"), "external",
    true(), "auto")
| eval signer_chain_status=case(
    len(signer_chain_status)>0 AND signer_chain_status!="unknown", signer_chain_status,
    isnotnull(days_until_signer_expiry) AND isnotnull(days_until_expiry) AND days_until_signer_expiry<days_until_expiry, "signer_expires_before_leaf",
    true(), "chain_ok_or_unknown")
| eval recommended_action=case(
    len(recommended_action_hint)>0, recommended_action_hint,
    severity=="page" AND rotation_policy=="manual", "oc_adm_certificate_approve_and_follow_kubelet_signer_runbook",
    severity=="page" AND rotation_policy=="auto", "force_operator_reconcile_and_verify_secret_rotation",
    severity=="page" AND rotation_policy=="external", "renew_default_ingress_or_identity_serving_material",
    severity=="warn", "schedule_rotation_window_before_30d_line",
    severity=="info", "keep_inventory_evidence_before_90d_review",
    true(), "refresh_openshift_cert_policy_lookup_and_inputs")
| eval days_until_signer_expiry=if(isnotnull(days_until_signer_expiry), days_until_signer_expiry, days_until_min_expiry)
| where isnotnull(cluster) AND len(cluster)>1
| table cluster namespace secret_name cert_subject_cn cert_issuer days_until_expiry rotation_policy operator_owner severity last_rotation_age_days signer_chain_status ca_bundle_kind days_until_signer_expiry recommended_action prom_metric_seen
```



savedsearches.conf sketch for platform paging:

```ini
[openshift_uc_3_3_20_cluster_certificate_expiry_alert]
cron_schedule = 0 */4 * * *
dispatch.earliest_time = -7d@d
dispatch.latest_time = now
enableSched = 1
action.email = 1
action.email.to = openshift-pki@example.com
action.email.subject = OCP PKI $result.severity$ $result.cluster$ $result.namespace$/$result.secret_name$
counttype = number of events
relation = greater than
quantity = 0
search = | savedsearch openshift_uc_3_3_20_cluster_certificate_expiry | where severity IN ("page","warn")
```

Performance: materialize hourly openshift:certificates summaries if Job Inspector queue time exceeds SLAs.

### Step 4 — Validate

Ground truth for Secret material always starts on-cluster with targeted JSON exports. Run oc get secret -n openshift-config-managed -o json | jq '.items[] | select(.type=="kubernetes.io/tls" or (.data|has("tls.crt")))' to compare notAfter equivalents from openssl against Splunk rows for kube-apiserver-server-ca and kube-controller-manager-client-ca families without pasting private keys into tickets. Repeat for openshift-service-ca, openshift-ingress-operator default certificate secrets, openshift-authentication serving secrets, openshift-monitoring client secrets for Prometheus and Thanos scrapes, openshift-image-registry route TLS secrets, and openshift-console console TLS secrets. When Splunk shows a shorter horizon than openssl on the same generation, first verify indexer time skew, then verify you are comparing the same PEM leaf index after rotations append multiple certs.

ClusterOperator truth: run oc get clusteroperator and oc describe clusteroperator authentication console etcd ingress kube-apiserver monitoring image-registry service-ca, focusing on Degraded messages that mention certificate, TLS, signer, trust bundle, or etcd peer failures. Splunk openshift:operator rows should appear within one collection interval of CLI transitions; if not, fix kubeconfig expiration on the management host before blaming parsers.

Prometheus distribution sanity: in the OpenShift monitoring UI or with oc get --raw against the monitoring route, run instant queries for apiserver_client_certificate_expiration_seconds_bucket and confirm histogram buckets move logically with your cluster age and rotation policies. Splunk should retain representative metric lines with sourcetype=prometheus:metrics so auditors see the same distribution class the platform exposes upstream.

Signer chain verification: extract a tls.crt from a namespace under change control, run openssl x509 -text -noout -dates -issuer -subject against the temp file, and compare issuer chains to parent CA material from openshift-config-managed or service-ca bundles documented for your minor version. When issuer notAfter is sooner than leaf notAfter, openshift_cert_policy.csv should mark signer_chain_status as signer_expires_before_leaf so the search surfaces cascading risk.

Synthetic near-expiry: in lab only, introduce a short-lived TLS secret or use a known low-lifetime signer in a dev cluster, ingest openshift:certificates events, and confirm severity becomes page or warn within the expected horizon bands. Clear the lab artifact after validation.

Negative test: when a cluster is healthy and all notAfter values exceed one hundred twenty days, confirm severities fall back to inventory or info tiers and that the alert wrapper returns zero rows for page and warn filters.

Lookup completeness: run a small join that lists Secret rows without openshift_cert_policy.csv coverage and fix CSV gaps before production enforcement.

Publish a dashboard with one row per cluster, namespace, and secret_name using the closing table columns, color severities with UI thresholds where page is red, warn is amber, info is blue, and inventory is gray, and add drilldowns to raw openshift:certificates JSON, openshift:secret metadata, openshift:operator messages, and prometheus metric lines. Archive weekly CSV exports of the alert table to a restricted evidence index with the git commit hash of openshift_cert_policy.csv for cryptographic governance packs.

Wire alert actions to platform on-call, optional Splunk ITSI episodes keyed on cluster entities, and ticketing systems with recommended_action, rotation_policy, and direct links to internal runbooks covering kube-apiserver-to-kubelet signer approvals, etcd peer rotations, service CA propagation, ingress default certificate replacement, OAuth serving cert replacement, monitoring client recycling, registry route TLS, and console route TLS. Document ownership: openshift platform SRE for kube-apiserver and etcd operators, ingress team for default edge certificates, identity team for OAuth, observability team for monitoring clients, and developer services for registry and console routes when those remain platform managed.

Train responders: Splunk shows timing and scope; remediation follows vendor rotation and must-gather guidance—never paste private keys into chat.

### Step 5 — Operationalize & Troubleshoot

Case A — auto-rotated service-ca signed serving cert inside five days: expect healthy operator churn, confirm service-ca ClusterOperator Available=True, verify DistIssuer still publishes valid CABundle ConfigMaps, and treat Splunk page severity as informational if openshift_cert_policy.csv marks rotation_policy auto and Prometheus shows stable apiserver_client_certificate_expiration_seconds buckets without Degraded conditions.

Case B — kube-apiserver-to-kubelet-client signer nearing expiry with manual rotation required: follow documentation for CSR approval flows, run oc get csr and oc adm certificate approve as authorized, validate kube-controller-manager logs for signer errors, and escalate if nodes lose kubelet client credentials while API still answers health checks.

Case C — etcd peer certificate expiring inside seven days: confirm etcd ClusterOperator and member health, snapshot etcd before guided rotation, compare peer and server secrets for skew, and coordinate with Red Hat support when quorum risk appears.

Case D — etcd server certificate shows expired in Splunk while etcd ClusterOperator reports healthy and etcdctl member list succeeds: suspect stale Splunk snapshot or indexer delay, re-run oc get secret -n openshift-etcd -o json | jq immediately, verify resourceVersion increments, and clear summary indexes if you materialize hourly aggregates.

Case E — service-ca signing CA expiring inside thirty days: expect wide blast radius across service-serving secrets, validate signing-cabundle ConfigMap distribution to trusting pods, plan signer rotation under maintenance windows, and watch for brief TLS errors during bundle propagation that should not page if leaves remain valid.

Case F — ingress operator default certificate expiring with CDN-pinned hostnames: treat as external rotation_policy, validate router-ca and default certificate secrets, coordinate cutovers with corporate PKI and edge teams, and remember UC-3.3.8 covers customer Routes while this case covers operator-managed defaults.

Case G — OAuth server certificate expiry risking SSO-wide outage: check authentication ClusterOperator, openshift-authentication secrets, console login failures correlated with SAML or OIDC IdP errors, and renew serving material per identity runbooks before broad user impact.

Case H — image-registry route certificate expiry risking cluster pulls: validate image-registry ClusterOperator, route hostnames builders use, and registry TLS secrets; rotations here can break CI/CD pipelines even when workloads still run.

Case I — console route certificate expiry risking admin lockout: validate console ClusterOperator and console TLS secrets, test oc login and web console from administrative jump hosts, renew before break-glass procedures become the only path.

Case J — monitoring or Prometheus client certificate expiry halting metric collection: validate monitoring ClusterOperator, thanos and prometheus client secrets, and federation tokens to Splunk; metric silence can hide the next PKI failure, so treat as high priority even when user workloads look fine.

Case K — signer-of-signers expiring before child leaves: openssl comparison shows parent CA notAfter sooner than leaf notAfter, openshift_cert_policy.csv marks signer_chain_status signer_expires_before_leaf, prioritize parent rotation or CA issuance before leaf renewals consume an untrusted issuer.

Case L — clean cluster control test with all certificates beyond ninety days and operators Available: expect inventory severities, empty alert wrapper for page and warn filters, and quarterly replay of this case to prove telemetry freshness.

## SPL

```spl
`comment("UC-3.3.20 OpenShift operator-managed control-plane PKI — openshift:secret/openshift:certificates, prometheus apiserver_client_certificate_expiration_seconds, openshift:operator ClusterOperator hints. Join openshift_cert_policy.csv. earliest=-7d@d latest=now; severities page<=7d warn<=30d info<=90d else inventory")`
| multisearch
    [ search index=openshift (sourcetype="openshift:secret" OR sourcetype="openshift:certificates") earliest=-7d@d latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, secret_namespace, metadata_namespace, ""))))
      | eval secret_name=lower(trim(toString(coalesce(secret_name, name, metadata_name, object_name, ""))))
      | eval lane="secret_or_cert_scan"
      | eval cert_degraded=0
      | eval na_str=trim(toString(coalesce(notAfter, not_after, cert_not_after, tls_not_after, "")))
      | eval epoch_raw=tonumber(tostring(coalesce(expiry_epoch, notAfter_epoch, not_after_epoch, cert_expiry_epoch, "")),10)
      | eval prom_like=tonumber(tostring(coalesce(_value, metric_value, prom_value, "")),10)
      | eval not_after_epoch=coalesce(
          if(epoch_raw>1000000000, epoch_raw, null()),
          if(prom_like>1000000000, prom_like, null()),
          if(len(na_str)>0 AND match(na_str,"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"), strptime(na_str, "%Y-%m-%dT%H:%M:%SZ"), null()),
          if(len(na_str)>0 AND match(na_str,"^[A-Za-z]{3}\\s+[0-9]{1,2}\\s"), strptime(na_str, "%b %d %H:%M:%S %Y GMT"), null()),
          if(len(na_str)>0, strptime(na_str, "%Y-%m-%d %H:%M:%S"), null()) )
      | eval cert_subject_cn=trim(toString(coalesce(cn, common_name, subject_cn, tls_cn, cert_cn, "")))
      | eval cert_issuer=trim(toString(coalesce(issuer, tls_issuer, issuer_dn, cert_issuer_x509, "")))
      | eval ca_bundle_kind=lower(trim(toString(coalesce(cert_category, pki_class, bundle_kind, "openshift_operator_tls_secret"))))
      | eval operator_owner=trim(toString(coalesce(owning_operator, operator, ocp_operator, "")))
      | eval last_rot_epoch=tonumber(tostring(coalesce(last_rotation_ts, secret_last_renewal_epoch, "")),10)
      | eval prom_metric_seen="no"
      | fields _time cluster namespace secret_name lane not_after_epoch cert_subject_cn cert_issuer ca_bundle_kind operator_owner last_rot_epoch prom_metric_seen cert_degraded ]
    [ search index=openshift sourcetype="prometheus:metrics" earliest=-7d@d latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, k8s_cluster_name, ""))))
      | eval mn=lower(trim(toString(coalesce(__name__, metric_name, name, ""))))
      | where mn="apiserver_client_certificate_expiration_seconds" OR like(mn,"apiserver_client_certificate_expiration_seconds%")
      | eval lane="prom_apiserver_client_cert"
      | eval cert_degraded=0
      | eval mv=tonumber(tostring(coalesce(value, metric_value, _value, Value, "")), 10)
      | eval not_after_epoch=if(isnotnull(mv) AND mv>1000000000 AND mv<4000000000, mv, null())
      | eval namespace="openshift-kube-apiserver"
      | eval secret_name="prom__apiserver_client_certificate_expiration_seconds"
      | eval cert_subject_cn=trim(toString(coalesce(client_cn, cn, signer_name, "apiserver_authenticated_client")))
      | eval cert_issuer=trim(toString(coalesce(issuer_cn, "kubernetes_ca_signer")))
      | eval ca_bundle_kind="apiserver_client_cert_metric"
      | eval operator_owner="openshift-kube-apiserver-operator"
      | eval last_rot_epoch=null()
      | eval prom_metric_seen="yes"
      | fields _time cluster namespace secret_name lane not_after_epoch cert_subject_cn cert_issuer ca_bundle_kind operator_owner last_rot_epoch prom_metric_seen cert_degraded ]
    [ search index=openshift sourcetype="openshift:operator" earliest=-7d@d latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval co_name=lower(trim(toString(coalesce(name, clusteroperator_name, metadata_name, ""))))
      | eval lane="clusteroperator_status"
      | where like(co_name,"kube-apiserver%") OR co_name=="etcd" OR like(co_name,"ingress%") OR like(co_name,"monitoring") OR co_name=="authentication" OR co_name=="image-registry" OR co_name=="console" OR co_name=="service-ca"
      | eval cond_msg=lower(trim(toString(coalesce(message, reason, status_message, condition_message, ""))))
      | eval cert_degraded=if(match(cond_msg,"cert|tls|x509|expir|signer|ca bundle|trust bundle|rotate|pem"),1,0)
      | where cert_degraded=1
      | eval not_after_epoch=null()
      | eval namespace="openshift-cluster-version"
      | eval secret_name="clusteroperator__".co_name
      | eval cert_subject_cn="clusteroperator:".co_name
      | eval cert_issuer="cluster_operator_condition"
      | eval ca_bundle_kind="clusteroperator_cert_hint"
      | eval operator_owner=co_name
      | eval last_rot_epoch=null()
      | eval prom_metric_seen="no"
      | fields _time cluster namespace secret_name lane not_after_epoch cert_subject_cn cert_issuer ca_bundle_kind operator_owner last_rot_epoch prom_metric_seen cert_degraded ]
    [ search index=openshift (sourcetype="openshift:operator" OR sourcetype="openshift:event") earliest=-7d@d latest=now
      | eval cluster=lower(trim(toString(coalesce(cluster, openshift_cluster, cluster_name, cluster_id, ""))))
      | eval namespace=lower(trim(toString(coalesce(namespace, k8s_namespace, involvedObject_namespace, ""))))
      | eval secret_name=lower(trim(toString(coalesce(involvedObject_name, secret_name, name, ""))))
      | eval evt_reason=lower(trim(toString(coalesce(reason, event_reason, ""))))
      | eval evt_msg=lower(trim(toString(coalesce(message, event_message, _raw, ""))))
      | where match(evt_reason, "rotated|reissued|signed|expir|csrapproved|signerupdated") OR match(evt_msg, "certificate.*(rotat|reissu|sign|expir)")
      | stats count AS rotation_evt_count, max(_time) AS last_rotation_evt_time, values(evt_reason) AS rotation_evt_reasons BY cluster namespace secret_name
      | eval lane="cert_rotation_signal"
      | eval cert_degraded=0
      | eval na_str=""
      | eval epoch_raw=null()
      | eval prom_like=null()
      | eval not_after_epoch=null()
      | eval cert_subject_cn=""
      | eval cert_issuer=""
      | eval _time=last_rotation_evt_time
      | fields _time cluster namespace secret_name lane cert_degraded not_after_epoch cert_subject_cn cert_issuer rotation_evt_count last_rotation_evt_time rotation_evt_reasons ]
| eval not_after_epoch=if(cert_degraded=1 AND isnull(not_after_epoch), relative_time(now(),"+1d@d"), not_after_epoch)
| eval days_until_expiry=if(isnotnull(not_after_epoch) AND not_after_epoch>0, round((not_after_epoch - now()) / 86400, 2), null())
| eval last_rotation_age_days=if(isnotnull(last_rot_epoch) AND last_rot_epoch>1000000000, round((now()-last_rot_epoch)/86400, 2), null())
| join type=left max=0 cluster, namespace, secret_name [
    | inputlookup openshift_cert_policy.csv
    | eval cluster=lower(trim(toString(cluster)))
    | eval namespace=lower(trim(toString(namespace)))
    | eval secret_name=lower(trim(toString(secret_name)))
    | eval rotation_policy=lower(trim(toString(coalesce(rotation_policy, rotation_class, "auto"))))
    | eval operator_owner_lu=trim(toString(coalesce(operator_owner, owning_operator, "")))
    | eval ca_bundle_kind_lu=lower(trim(toString(coalesce(ca_bundle_kind, pki_bucket, ""))))
    | eval signer_chain_status=trim(toString(coalesce(signer_chain_status, chain_hint, "unknown")))
    | eval days_until_signer_expiry=tonumber(tostring(coalesce(days_until_signer_expiry, signer_days_remaining, "")),10)
    | eval recommended_action_hint=trim(toString(coalesce(recommended_action_hint, "")))
    | fields cluster namespace secret_name rotation_policy operator_owner_lu ca_bundle_kind_lu signer_chain_status days_until_signer_expiry recommended_action_hint ]
| fillnull value="auto" rotation_policy
| fillnull value="" operator_owner_lu ca_bundle_kind_lu signer_chain_status recommended_action_hint
| eval operator_owner=if(len(operator_owner_lu)>0, operator_owner_lu, operator_owner)
| eval ca_bundle_kind=if(len(ca_bundle_kind_lu)>0, ca_bundle_kind_lu, ca_bundle_kind)
| eventstats min(days_until_expiry) AS days_until_min_expiry BY cluster
| streamstats window=20000 current=t global=f min(days_until_expiry) AS cat_fastest_expiry BY cluster ca_bundle_kind
| eval severity=case(
    isnull(days_until_expiry), "inventory",
    days_until_expiry<=7, "page",
    days_until_expiry<=30, "warn",
    days_until_expiry<=90, "info",
    true(), "inventory")
| eval rotation_policy=case(
    match(lower(ca_bundle_kind),"ingress_default|oauth-serving|registry_public|console_public|passthrough_edge"), "external",
    match(lower(ca_bundle_kind),"kube_apiserver_to_kubelet|csr_signer|manual_kubelet_client"), "manual",
    match(lower(rotation_policy),"manual|csr|approve"), "manual",
    match(lower(rotation_policy),"external|edge|custom_ca"), "external",
    true(), "auto")
| eval signer_chain_status=case(
    len(signer_chain_status)>0 AND signer_chain_status!="unknown", signer_chain_status,
    isnotnull(days_until_signer_expiry) AND isnotnull(days_until_expiry) AND days_until_signer_expiry<days_until_expiry, "signer_expires_before_leaf",
    true(), "chain_ok_or_unknown")
| eval recommended_action=case(
    len(recommended_action_hint)>0, recommended_action_hint,
    severity=="page" AND rotation_policy=="manual", "oc_adm_certificate_approve_and_follow_kubelet_signer_runbook",
    severity=="page" AND rotation_policy=="auto", "force_operator_reconcile_and_verify_secret_rotation",
    severity=="page" AND rotation_policy=="external", "renew_default_ingress_or_identity_serving_material",
    severity=="warn", "schedule_rotation_window_before_30d_line",
    severity=="info", "keep_inventory_evidence_before_90d_review",
    true(), "refresh_openshift_cert_policy_lookup_and_inputs")
| eval days_until_signer_expiry=if(isnotnull(days_until_signer_expiry), days_until_signer_expiry, days_until_min_expiry)
| where isnotnull(cluster) AND len(cluster)>1
| table cluster namespace secret_name cert_subject_cn cert_issuer days_until_expiry rotation_policy operator_owner severity last_rotation_age_days signer_chain_status ca_bundle_kind days_until_signer_expiry recommended_action prom_metric_seen
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS app_state latest(Application_State.info) AS app_info FROM datamodel=Application_State WHERE nodename=Application_State earliest=-24h@h latest=now BY Application_State.dest
| rename Application_State.dest AS cim_dest
| join type=left max=0 cim_dest
    [| tstats summariesonly=t latest(Inventory.vendor_product) AS inv_prod latest(Inventory.version) AS inv_ver FROM datamodel=Inventory WHERE nodename=Inventory earliest=-24h@h latest=now BY Inventory.dest
     | rename Inventory.dest AS cim_dest ]
| where like(lower(app_info), "%openshift%") OR like(lower(inv_prod), "%openshift%")
| table cim_dest app_state app_info inv_prod inv_ver
```

## Visualization

Severity-colored table by cluster, namespace, and secret_name with drilldowns to openshift:certificates JSON, openshift:secret metadata, openshift:operator messages, and prometheus metric lines; single-value tiles for cluster days_until_min_expiry; timeline of cat_fastest_expiry by ca_bundle_kind; histogram panel mirroring apiserver_client_certificate_expiration_seconds_bucket upstream queries.

## Known False Positives

Chained certificate renewals routinely leave multiple PEM leaves in a single tls.crt while operators finish rollout; Splunk may still read an older notAfter until parsers select the final leaf—correlate resourceVersion increments and openshift:operator Progressing messages before paging. Trust bundle propagation lag after service-ca or apiserver signer rotation can produce short TLS error bursts that resemble imminent expiry even when new CABundle ConfigMaps already exist on disk; require sustained Degraded conditions or consistent short notAfter across collectors before executive escalation. Operator reconciliation timestamps and metadata.generation can advance without changing notAfter when secrets are relabeled; avoid interpreting generation bumps alone as rotation completion. etcd quorum maintenance can pause secret writes briefly, producing null exporter rows that look like missing certificates; verify openshift:certificates lane freshness against oc get secret before assuming data loss. Prometheus federation scrape gaps or Thanos receive outages can drop apiserver_client_certificate_expiration_seconds samples while clusters remain healthy; combine with openshift:certificates horizons before muting metrics entirely. Lab clusters with intentionally short lifetimes for drill secrets will page unless openshift_cert_policy.csv marks them non-production; tune rotation_policy and suppress windows rather than disabling the control. Duplicate HEC submissions from redundant inventory jobs can double-count secrets; dedupe on cluster, namespace, secret_name, and fingerprint fields in summary indexes when cost matters. ClusterOperator messages that mention cert in unrelated contexts, such as registry mirror TLS to external sites, can false-positive cert_degraded; read message text and compare to etcd, authentication, or ingress operator ownership before kubelet signer escalation. Splunk lookup staleness after a successful rotation can show expired rows while OpenShift already serves new PEM material; re-ingest openshift_cert_policy.csv signer columns after offline openssl parent comparisons. This control focuses on internal operator PKI, not customer edge CDN pinning alone—that narrative lives in UC-3.3.8.

## References

- [OpenShift Documentation — Understanding API server certificates](https://docs.openshift.com/container-platform/latest/security/certificates/api-server.html)
- [OpenShift Documentation — Service CA certificates](https://docs.openshift.com/container-platform/latest/security/certificate_types_descriptions/service-ca-certificates.html)
- [OpenShift Documentation — etcd certificates](https://docs.openshift.com/container-platform/latest/security/certificate_types_descriptions/etcd-certificates.html)
- [Splunkbase — Splunk Add-on for Kubernetes](https://splunkbase.splunk.com/app/3743)
- [Splunk Lantern — Kubernetes data descriptors](https://lantern.splunk.com/Data_Descriptors/Kubernetes)
- [Kubernetes Documentation — Metrics for Kubernetes system components](https://kubernetes.io/docs/reference/instrumentation/metrics/)
- [Red Hat Knowledgebase — OpenShift cluster certificate recovery guidance](https://access.redhat.com/solutions/)
