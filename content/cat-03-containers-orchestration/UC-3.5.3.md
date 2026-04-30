<!-- AUTO-GENERATED from UC-3.5.3.json — DO NOT EDIT -->

---
id: "3.5.3"
title: "mTLS Certificate Expiry"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-3.5.3 · mTLS Certificate Expiry

## Description

Tracks **Istio** mesh **mTLS certificate** expiry timestamps for root CA, intermediate CA, istiod workload certificates, and ingress/egress gateway TLS certificates, computing days-to-expiry and alert tiers — then correlates certificate-related TLS handshake failures from Envoy access logs to detect in-progress expiry events before the entire service mesh loses mutual authentication.

## Value

An expired mTLS root CA certificate takes down mutual authentication across every service in the mesh simultaneously — there is no gradual degradation, just a cliff-edge failure that breaks all inter-service communication at once. Monitoring certificate lifetimes gives security and platform teams weeks of warning to rotate certificates, while handshake-failure correlation catches rotation gaps that automated renewal missed.

## Implementation

Scrape Istio control plane certificate expiry metrics (citadel_server_root_cert_expiry_timestamp, citadel_server_cert_chain_expiry_timestamp, istiod_cert_expiry_seconds) from istiod via the OTel Collector. Collect Kubernetes Secret metadata for gateway TLS certificates. Build three search variants: certificate expiry status with alert tiers, gateway TLS cert expiry, and mTLS handshake failure correlation from access logs. Alert at 30/7/1-day thresholds with escalating severity.

## Detailed Implementation

Prerequisites
• **Istio** 1.18+ with **mTLS** in **STRICT** mode across all namespaces (verify with `kubectl get peerauthentication --all-namespaces`); Istio manages its own **root CA** and issues short-lived **workload certificates** via its built-in **certificate authority** (formerly Citadel, now integrated into **istiod**).
• **istiod** control plane metrics endpoint enabled on port **15014** — this exposes the certificate expiry timestamps that the SPL monitors. Verify: `kubectl port-forward -n istio-system svc/istiod 15014:15014` then `curl localhost:15014/metrics | grep cert_expiry`.
• **Splunk OpenTelemetry Collector** with the **Prometheus receiver** scraping **istiod** metrics on port **15014**; add a static or service-discovery scrape target for the `istiod` service in the `istio-system` namespace.
• **Splunk HEC** token for **`index=containers`** with default **`sourcetype=otel:metrics`**; secondary streams for **`sourcetype=istio:pilot`** (istiod logs), **`sourcetype=kube:events`**, and **`sourcetype=istio:accesslog`**.
• **Kubernetes Secret metadata collection**: configure the OTel Collector's **`k8sobjects`** receiver or a **scripted input** to collect **Secret metadata** (name, namespace, annotations, creation timestamp) for Secrets matching `type=kubernetes.io/tls` — never collect the actual certificate data or private keys. Index as **`sourcetype=kube:secrets`**.
• Splunk RBAC: assign **`srchIndexesAllowed`** including `containers` via a custom role (**`mesh_security_analyst`**).
• **Certificate rotation context**: Istio's default workload certificate TTL is **24 hours** (configurable via `meshConfig.certificates[].dnsNames` or `CITADEL_SELF_SIGNED_CA_CERT_TTL`). The root CA certificate default TTL is **10 years** for self-signed CAs. External CAs (**cert-manager**, Vault) have their own rotation schedules.

Step 1 — Configure data collection
(1) **istiod metrics scraping**: add the **istiod** service as a Prometheus scrape target. Key metrics:
— **`citadel_server_root_cert_expiry_timestamp`** (gauge: Unix epoch when the **root CA** cert expires)
— **`citadel_server_cert_chain_expiry_timestamp`** (gauge: Unix epoch when the **intermediate CA** cert chain expires)
— **`istiod_cert_expiry_seconds`** (gauge: seconds remaining until istiod's own workload certificate expires — resets on each rotation)
These three metrics provide complete visibility into the **certificate hierarchy**.

(2) **istiod log collection**: collect istiod logs as **`sourcetype=istio:pilot`** via the OTel **`filelog`** receiver or **Splunk Connect for Kubernetes**. Key log patterns to monitor:
— `certificate rotation` — successful rotation event
— `failed to sign cert` — CA signing failure
— `SDS push error` — Secret Discovery Service failure delivering certs to sidecars
— `certificate expired` — post-expiry error

(3) **Gateway TLS Secrets**: Istio **ingress** and **egress gateways** use **Kubernetes** TLS Secrets for external-facing certificates (different from the mesh-internal mTLS certs). These are not covered by Istio's automatic rotation and must be tracked separately. Collect Secret metadata including the `not_after` annotation if present, or extract the expiry from the certificate's **`tls.crt`** field using a **scripted input** that runs `openssl x509 -enddate -noout -in <cert>`.

(4) **Envoy access log enrichment**: the **`response_flags`** field in **Envoy** access logs indicates TLS failures — **UF** (upstream connection failure) paired with TLS error context, **UC** (upstream connection termination during handshake). These correlate expired certificates with actual traffic impact.

(5) **External CA integration**: if using **cert-manager** or **HashiCorp Vault** as the Istio CA, collect the CA's own certificate expiry metrics and logs. For cert-manager: scrape `certmanager_certificate_expiration_timestamp_seconds`; for Vault: monitor the PKI secret engine's CA certificate expiry.

Step 2 — Create the search and alert
The primary SPL converts Unix epoch **expiry timestamps** into human-readable dates and computes `days_remaining` and `hours_remaining`. The **`alert_level`** classification escalates through **HEALTHY** → **APPROACHING** (30d) → **WARNING** (7d) → **CRITICAL** (1d) → **EXPIRED**.

The root CA certificate has the longest lifetime and the most catastrophic impact if it expires — a single expired root invalidates every workload certificate in the mesh. The intermediate CA and istiod workload certificates have shorter lifetimes but are rotated automatically.

The gateway TLS variant monitors Kubernetes Secrets rather than Istio metrics because gateway certificates are managed externally (manually or via cert-manager) and don't appear in the istiod metrics.

The **handshake-failure variant** detects active certificate problems by searching for TLS-related error patterns in access logs and istiod logs. A spike in handshake failures correlated with a certificate approaching expiry confirms that rotation has failed.

Schedule the expiry search every **6 hours** with long-range thresholds (30/7/1 day). Schedule the **handshake-failure** search every **5 minutes** over **`-5m`** and alert on any failure count > 10.

Step 3 — Validate
(a) Verify **certificate metrics**: `index=containers sourcetype=otel:metrics metric_name=citadel_server_root_cert_expiry_timestamp | head 1 | eval expiry=strftime(tonumber(value), "%Y-%m-%d") | table expiry`. Should show the root CA expiry date matching `istioctl proxy-config secret -n istio-system <istiod-pod> | grep ROOTCA`.
(b) Test **workload cert rotation**: `kubectl rollout restart deployment -n istio-system istiod` triggers a fresh cert issuance cycle. The `istiod_cert_expiry_seconds` metric should reset to the full TTL value (default 86400s for 24h certs).
(c) Verify **gateway Secret monitoring**: `index=containers sourcetype="kube:secrets" secret_name=*tls* | stats count by ns, secret_name`. Should list all TLS Secrets in gateway namespaces.
(d) Test **handshake failure detection**: temporarily set a PeerAuthentication to STRICT in a namespace where a pod lacks sidecar injection — traffic to that pod will produce TLS handshake failures that the third SPL variant should capture.
(e) Cross-check with `istioctl`: `istioctl proxy-config secret <pod>` shows the certificate chain, ROOTCA expiry, and whether the SDS stream is healthy.

Step 4 — Operationalize dashboards and runbooks
• Row A: **countdown tiles** — root CA days-to-expiry (large single-value), intermediate CA days-to-expiry, istiod cert hours-to-expiry (expected to cycle every 24h). Color-code: green > 30d, yellow 7–30d, red < 7d.
• Row B: **timeline** of upcoming certificate expirations — a Gantt-style bar for each certificate showing its validity window.
• Row C: **handshake-failure bar chart** — failures per 15-minute window by source service, correlated with certificate rotation events.
• Row D: **gateway certificate table** — ns, secret_name, expiry, days_left, alert_level. Red highlighting for any non-HEALTHY entry.
• **Alerting**: root CA ≤ 30 days → email to **security team** and **platform engineering** leads; root CA ≤ 7 days → **PagerDuty** P1; istiod cert not rotating (hours_remaining > 36h for a 24h TTL) → P2 to mesh on-call; handshake failures > 10 in 5m → P2 with affected services.
• **Runbook** (owner: platform security on-call): (1) check cert type from alert, (2) for root CA: follow Istio root CA rotation procedure (`istioctl x create-remote-secret`), plan rolling restart of all workloads, (3) for gateway certs: renew via cert-manager or manual CSR, (4) for workload certs: verify istiod is healthy and SDS is pushing.

Step 5 — Visualization, alert design, and troubleshooting
• **Visualization**: use a **certificate lifecycle timeline** showing each cert's issued/expiry dates as colored bars (green/yellow/red by remaining time); pair with a **handshake-failure heatmap** showing source × destination × time to correlate failures with specific cert rotation windows; add a **rotation history table** from istiod logs showing successful and failed rotations.
• **Alert design**: include `cert_type`, `expiry`, `days_left`, `hours_left`, and `alert_level`; for handshake alerts include `source_svc`, `dest_svc`, `failure_count`, and `error_detail`; add deep-links to the certificate dashboard and the Istio security documentation.
• **Root CA expiry shows year 2033** — this is the default 10-year self-signed CA. While not urgent, plan rotation before it becomes a forgotten time bomb. Add a calendar reminder 6 months before expiry.
• **istiod cert metric not updating** — istiod may have lost connection to its CA or the SDS push is failing. Check istiod logs: `kubectl logs -n istio-system -l app=istiod | grep -i cert`.
• **Gateway cert shows EXPIRED but traffic works** — the ingress gateway may be serving cached certificates. Restart the gateway pod to force a fresh cert load and verify whether traffic breaks.
• **Handshake failures without cert expiry** — may indicate misconfigured **PeerAuthentication** (STRICT mode on a namespace with non-injected pods), not cert expiry. Check the `error_detail` field for specific TLS error codes.
• **cert-manager certificates not appearing** — the kube:secrets collection may not include the cert-manager-managed Secrets. Add cert-manager namespace to the k8sobjects receiver scope.

## SPL

```spl
`comment("--- Istio mTLS Certificate Expiry — Root CA and Workload Cert Status ---")`
index=containers (sourcetype="otel:metrics" OR sourcetype="prometheus:istio")
| where match(metric_name, "citadel_server_root_cert_expiry_timestamp|citadel_server_cert_chain_expiry_timestamp|istiod_cert_expiry_seconds")
| eval metric=coalesce(metric_name, name)
| eval cert_type=case(
    match(metric, "root_cert_expiry"), "root_ca",
    match(metric, "cert_chain_expiry"), "intermediate_ca",
    match(metric, "istiod_cert_expiry"), "istiod_workload",
    1=1, "unknown")
| eval expiry_epoch=tonumber(value)
| eval expiry_time=strftime(expiry_epoch, "%Y-%m-%d %H:%M:%S")
| eval seconds_remaining=expiry_epoch - now()
| eval days_remaining=round(seconds_remaining / 86400, 1)
| eval hours_remaining=round(seconds_remaining / 3600, 1)
| eval alert_level=case(
    days_remaining <= 0, "EXPIRED",
    days_remaining <= 1, "CRITICAL",
    days_remaining <= 7, "WARNING",
    days_remaining <= 30, "APPROACHING",
    1=1, "HEALTHY")
| stats latest(expiry_time) as expiry,
    latest(days_remaining) as days_left,
    latest(hours_remaining) as hours_left,
    latest(alert_level) as alert_level,
    latest(_time) as last_seen
    by cert_type
| sort alert_level
| table cert_type expiry days_left hours_left alert_level last_seen

`comment("--- Gateway TLS Certificate Expiry — Ingress/Egress Gateway Certs ---")`
index=containers sourcetype="kube:secrets"
| where match(secret_name, "(?i)(tls|cert|gateway|ingress)")
| eval ns=coalesce(namespace, object_namespace)
| eval cert_not_after=strftime(tonumber(coalesce(not_after, cert_expiry)), "%Y-%m-%d")
| eval days_remaining=round((tonumber(coalesce(not_after, cert_expiry)) - now()) / 86400, 1)
| eval alert_level=case(
    days_remaining <= 0, "EXPIRED",
    days_remaining <= 7, "CRITICAL",
    days_remaining <= 30, "WARNING",
    days_remaining <= 90, "APPROACHING",
    1=1, "HEALTHY")
| stats latest(cert_not_after) as expiry,
    latest(days_remaining) as days_left,
    latest(alert_level) as alert_level
    by ns, secret_name
| where alert_level != "HEALTHY"
| sort alert_level days_left
| table ns secret_name expiry days_left alert_level

`comment("--- mTLS Handshake Failure Correlation ---")`
index=containers (sourcetype="istio:accesslog" OR sourcetype="istio:pilot")
| eval is_tls_failure=case(
    match(response_flags, "(UF|UC)") AND match(_raw, "(?i)tls|ssl|handshake|certificate"), 1,
    match(_raw, "(?i)certificate.*expired|cert.*verify.*fail|tls.*error|x509"), 1,
    1=1, 0)
| where is_tls_failure=1
| eval dest_svc=coalesce(upstream_cluster, authority, destination_service, "unknown")
| eval source_svc=coalesce(downstream_remote_address, source_workload, "unknown")
| eval error_detail=coalesce(response_flags, reason, "unknown")
| stats count as failure_count,
    dc(dest_svc) as affected_destinations,
    values(dest_svc) as destinations,
    latest(_time) as last_failure
    by source_svc, error_detail
| sort -failure_count
| table source_svc error_detail failure_count affected_destinations destinations last_failure
```

## Visualization

Certificate expiry countdown tiles (color-coded by alert level), timeline of upcoming expirations, handshake failure bar chart by service pair, sortable certificate table with drilldown.

## Known False Positives

**workload_cert_rotation_window** — Istio's default workload certificate TTL is 24 hours, meaning the `istiod_cert_expiry_seconds` metric naturally drops to near-zero every day before automatic rotation replenishes it. The CRITICAL alert fires on the expected rotation cycle rather than an actual problem. Set the workload cert alert threshold to 2× the TTL (e.g., alert only if hours_remaining > 36h for a 24h TTL, indicating rotation has stalled).

**root_ca_self_signed_decade** — Istio's default self-signed root CA has a 10-year validity, so the root CA alert_level stays at HEALTHY for years. This is correct behavior, not a false positive — but teams should still plan rotation well before the 10-year mark because root CA rotation requires a coordinated rollout across all clusters.

**gateway_cert_renewal_overlap** — When cert-manager renews a gateway TLS Secret, there is a brief overlap period where both the old and new certificates exist. The monitoring may briefly show two entries for the same gateway, one approaching expiry and one freshly issued. Deduplicate by taking the latest cert for each secret_name.

**sds_push_transient_failure** — istiod occasionally logs transient SDS push errors during high churn (many pods starting simultaneously) that resolve within seconds. These are not certificate problems but control-plane load spikes. Alert only on sustained SDS failures (> 5 errors in 5 minutes).

**permissive_mode_handshake** — Namespaces with PeerAuthentication set to PERMISSIVE mode accept both plaintext and mTLS traffic. TLS handshake failures from non-mesh clients are expected and do not indicate certificate problems. Filter handshake alerts to STRICT-mode namespaces only.

**external_ca_metric_absence** — When using an external CA (cert-manager, Vault PKI), the `citadel_server_root_cert_expiry_timestamp` metric may not be populated because istiod is not acting as the CA. Use the external CA's own metrics instead and suppress alerts for missing Istio CA metrics in external-CA deployments.

## References

- [Istio Security — Mutual TLS Architecture](https://istio.io/latest/docs/concepts/security/)
- [Istio — Certificate Management](https://istio.io/latest/docs/tasks/security/cert-management/)
- [Istio Control Plane Metrics — istiod](https://istio.io/latest/docs/reference/commands/pilot-discovery/#metrics)
- [Envoy Access Log Response Flags](https://www.envoyproxy.io/docs/envoy/latest/configuration/observability/access_log/usage)
- [Kubernetes TLS Secret Management](https://kubernetes.io/docs/concepts/configuration/secret/#tls-secrets)
