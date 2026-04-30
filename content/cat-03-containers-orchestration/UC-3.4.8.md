<!-- AUTO-GENERATED from UC-3.4.8.json — DO NOT EDIT -->

---
id: "3.4.8"
title: "Registry TLS and Certificate Expiration"
status: "verified"
criticality: "critical"
splunkPillar: "Security"
---

# UC-3.4.8 · Registry TLS and Certificate Expiration

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Availability, Security &middot; **Wave:** Crawl &middot; **Status:** Verified

*Every few hours we check the digital identity cards of our software warehouses to see if any are about to expire, because an expired card means nobody can pick up or deliver packages until a new one is issued.*

---

## Description

Probes container registry HTTPS endpoints to extract TLS certificate metadata (expiration date, key strength, signature algorithm, SAN entries) and classifies certificates by urgency (EXPIRED, CRITICAL, WARNING, NOTICE, OK), then correlates with Kubernetes image pull **x509 errors** to detect when expired or untrusted certificates are actively blocking container deployments across clusters.

## Value

An expired registry TLS certificate is one of the most impactful single-point failures in a container platform — when it expires, every image pull fails simultaneously across all clusters, CI/CD pipelines halt, autoscaler cannot launch new pods, and production rollbacks become impossible because even rollback images cannot be pulled. The blast radius is total and instantaneous. Proactive monitoring with tiered urgency (90/30/7/0 day thresholds) gives the platform team the lead time to renew certificates through their PKI process, which often requires change management approvals and maintenance windows.

## Implementation

Deploy a scripted input on a Splunk forwarder that runs openssl s_client against each registry endpoint daily, parsing certificate metadata into structured events. Build two search variants: certificate expiration inventory with urgency classification and weak crypto detection, and Kubernetes event correlation for active TLS failures during image pulls. Alert at 90/30/7/0 days before expiration.

## Detailed Implementation

### Prerequisites
- One or more **container registries** serving images over HTTPS — **Harbor**, **Docker Hub**, **Amazon ECR**, **Google Artifact Registry**, **Azure Container Registry**, or any **OCI-compliant** registry. Each registry endpoint has a **TLS certificate** that must remain valid for image pull operations to succeed.
- A **Splunk Universal Forwarder** (or heavy forwarder) with **OpenSSL** installed (standard on Linux) to run the certificate probing scripted input. The forwarder must have **network access** to all registry HTTPS endpoints (port 443 or custom port).
- **Splunk HEC** token for **`index=containers`** with **`sourcetype=tls:certificate`** as default; secondary tokens for **`sourcetype=kube:events`** and **`sourcetype=kube:container:logs`**.
- A **registry inventory file** listing all registry endpoints to probe — stored as a CSV or flat file on the forwarder host. Include the hostname, port, and a human-readable description for each endpoint.
- **Kubernetes clusters** configured with **image pull **secret**s** or node-level credentials for authenticated registries. The **TLS certificate** must be trusted by the **container runtime** (**containerd**, **CRI-O**) — either via the system **CA bundle** or via explicit CA configuration in the **containerd** or **CRI-O** configuration file.
- Splunk RBAC: assign a **`cert_monitor`** role with **`srchIndexesAllowed`** including `containers`.
- **License estimate**: certificate probing generates approximately 1 event per endpoint per probe cycle — typically under 1 KB/event. A registry inventory of 20 endpoints probed every 6 hours generates ~80 events/day (~80 KB). TLS-related Kubernetes events are sparse unless certificates are actively failing.

### Step 1 — Configure data collection
(1) **TLS certificate probing scripted input**: create a shell script that iterates over registry endpoints and extracts certificate metadata using **`openssl s_client`**:

```bash
#!/bin/bash
while IFS=, read -r host port desc; do
  cert_info=$(echo | openssl s_client -connect "$host:$port" \
    -servername "$host" 2>/dev/null | openssl x509 -noout \
    -subject -issuer -dates -serial -fingerprint -text 2>/dev/null)
  not_after=$(echo "$cert_info" | grep 'notAfter' | cut -d= -f2)
  subject=$(echo "$cert_info" | grep 'subject' | sed 's/subject=//')
  issuer=$(echo "$cert_info" | grep 'issuer' | sed 's/issuer=//')
  key_size=$(echo "$cert_info" | grep 'Public-Key' | grep -oP '\d+')
  sig_alg=$(echo "$cert_info" | grep 'Signature Algorithm' | head -1 | awk '{print $3}')
  serial=$(echo "$cert_info" | grep 'serial' | cut -d= -f2)
  echo "registry_host=$host, not_after=$not_after, subject=$subject, issuer_cn=$issuer, key_size=$key_size, signature_algorithm=$sig_alg, serial=$serial, description=$desc"
done < /opt/splunk/etc/apps/registry_tls_monitor/lookups/registry_endpoints.csv
```

Configure this as a **scripted input** in `inputs.conf`:
— **Interval**: 21600 seconds (6 hours) — certificates change infrequently, but 6-hour probing catches short-lived certificates and provides 4 data points per day.
— **Sourcetype**: `tls:certificate`
— **Index**: `containers`

(2) **Certificate chain validation**: extend the scripted input to validate the **full certificate chain** — not just the leaf certificate. Use `openssl verify -CAfile <ca-bundle>` to detect chain trust issues before they cause pull failures. Record chain depth and any chain validation errors.

(3) **Kubernetes image pull TLS errors**: collect **`sourcetype=kube:events`** from all clusters. Kubernetes generates **Warning** events with specific x509 error messages when image pulls fail due to certificate issues:
— **"x509: certificate has expired"** — the registry certificate has expired
— **"x509: certificate signed by unknown authority"** — the CA is not in the container runtime's trust store
— **"x509: certificate is valid for X, not Y"** — the registry hostname does not match the certificate's SAN entries
— **"tls: handshake failure"** — a general TLS negotiation failure (protocol mismatch, cipher suite incompatibility)

(4) **Harbor container logs**: collect **`sourcetype=kube:container:logs`** from the `harbor-nginx` and `harbor-registry` containers. These logs contain TLS handshake details when clients fail to connect — useful for diagnosing **client-side** certificate issues (mutual TLS, client certificates).

(5) **Multi-cluster correlation**: if images are pulled from multiple clusters, each cluster may have different CA trust configurations. Collect certificate probe results from **each cluster's forwarder** and tag with `cluster_name` to identify which clusters trust which certificates.

### Step 2 — Create the search and alert
The primary SPL processes certificate probe results and classifies urgency:
— **EXPIRED**: `days_left <= 0` — the certificate has already expired. Image pulls are failing NOW.
— **CRITICAL**: `days_left <= 7` — expiration is imminent. The renewal must happen within days.
— **WARNING**: `days_left <= 30` — expiration is approaching. The renewal should be planned.
— **NOTICE**: `days_left <= 90` — early warning. Begin the renewal process.
— **OK**: more than 90 days remaining.

The **`weak_crypto`** flag identifies certificates with **RSA keys smaller than 2048 bits** or **SHA-1/MD5 signatures** — these are security risks independent of expiration.

The second SPL variant correlates **Kubernetes image pull events** with TLS error patterns. It classifies errors by type (CERT_EXPIRED, UNTRUSTED_CA, NAME_MISMATCH, HANDSHAKE_FAILURE) and tracks the blast radius (affected pods and namespaces).

Schedule the certificate probe search every **6 hours**. Set up **tiered alerting**:
— **EXPIRED**: PagerDuty P1 immediate — certificates must be renewed NOW
— **CRITICAL** (≤7 days): PagerDuty P2 — plan emergency renewal
— **WARNING** (≤30 days): Slack `#platform-ops` — begin renewal process
— **NOTICE** (≤90 days): weekly email digest — add to renewal queue
— **weak_crypto=1**: weekly security report — plan certificate rotation

Schedule the Kubernetes event correlation every **15 minutes** and alert when any `tls_failures > 0`.

### Step 3 — Validate
(a) Run the probe script manually: `bash /opt/splunk/etc/apps/registry_tls_monitor/bin/probe_certs.sh` and verify output contains all expected fields.
(b) Verify data in Splunk: `index=containers sourcetype="tls:certificate" earliest=-1d | table registry days_left issuer_cn key_bits sig_algo urgency`. Should list all probed registries.
(c) Compare with manual check: `echo | openssl s_client -connect <registry>:443 -servername <registry> 2>/dev/null | openssl x509 -noout -enddate`. Compare `not_after` with the Splunk event.
(d) Test TLS error detection: if possible, temporarily configure a test namespace to pull from a registry with an untrusted CA. Verify: `index=containers sourcetype="kube:events" reason="FailedPulling" "x509" earliest=-10m`.
(e) Validate urgency classification: for each urgency level, verify at least one registry falls into the expected category (or create a test entry with a known expiry date).

### Step 4 — Operationalize dashboards and runbooks
- Row A: **single-value tiles** — soonest expiry (days, red if ≤ 7), total registries monitored, expired count, critical count, weak crypto count.
- Row B: **gauge** per registry showing days until expiry — green (>90), amber (31–90), orange (8–30), red (≤7), black (expired).
- Row C: **certificate inventory table** — registry, days_left, issuer_cn, key_bits, sig_algo, san_count, urgency, weak_crypto. Color-coded rows by urgency.
- Row D: **TLS failure timeline** — stacked bar of hourly TLS failures by error type. Drill down to affected pods and namespaces.
- **Alerting**: EXPIRED → PagerDuty P1; CRITICAL → PagerDuty P2; WARNING → Slack; NOTICE → email; weak_crypto → security report; any Kubernetes TLS failure → Slack `#platform-ops`.
- **Runbook** (owner: platform security/PKI team): (1) identify the certificate owner via the `issuer_cn` field, (2) request renewal through the organization's **PKI portal** or **ACME/Let's Encrypt** automation, (3) deploy the new certificate to the registry (Harbor: update `tls.crt` and `tls.key` in the `harbor-tls` Secret), (4) update **container runtime CA trust** on all nodes if the CA changed, (5) verify by re-running the probe script and confirming `urgency=OK`.

### Step 5 — Visualization, alert design, and troubleshooting
- **Visualization**: use a **certificate timeline** showing each registry as a horizontal bar from now to expiry date — bars shorten as expiry approaches, and expired bars extend past the current date in red. Pair with a **certificate health matrix** showing registry × attribute (expiry, key strength, signature algorithm) with color coding.
- **Alert design**: include `registry`, `days_left`, `urgency`, `issuer_cn`, `not_after`, `key_bits`, `sig_algo`, and `weak_crypto` in the alert payload. For TLS failure alerts include `registry_host`, `tls_failures`, `affected_pods`, `affected_namespaces`, and `tls_error_type`.
- **Probe returns empty results** — the registry may be behind a firewall that blocks the forwarder's connection. Verify network connectivity: `curl -v https://<registry>/v2/ 2>&1 | head -20`.
- **Days left is negative but no Kubernetes errors** — the certificate may have been renewed after the probe ran. Re-run the probe and check the updated `not_after`. Also check if a **CDN** or **load balancer** terminates TLS before the registry, meaning the registry's own certificate is never seen by clients.
- **Certificate chain validation fails but pulls work** — the container runtime may have the CA in its trust store even though the **system CA bundle** does not include it. This is a fragile configuration — future node replacements may not have the custom CA configured.
- **Certificate fingerprint tracking** — store the **SHA-256 fingerprint** of each certificate alongside the expiry date. When the fingerprint changes between probe cycles, it indicates the certificate was **rotated** — log the rotation event and verify the new certificate meets all security requirements.
- **Multiple SANs make it unclear which certificate covers which registry** — use the `san_entries` field to map certificates to all the hostnames they cover. A wildcard certificate (`*.example.com`) covers all subdomains but is a higher-impact certificate to monitor because a single expiration affects all registries under that domain.

## SPL

```spl
`comment("--- Registry TLS Certificate Expiration — Multi-Endpoint Monitoring ---")`
index=containers sourcetype="tls:certificate"
| eval registry=coalesce(registry_host, endpoint, host)
| eval expiry_epoch=strptime(coalesce(not_after, expiry_time), "%b %d %H:%M:%S %Y %Z")
| eval days_left=round((expiry_epoch - now()) / 86400, 0)
| eval issuer_cn=coalesce(issuer_cn, issuer)
| eval key_bits=coalesce(key_size, key_length)
| eval sig_algo=coalesce(signature_algorithm, sig_alg)
| eval san_count=mvcount(split(coalesce(san_entries, ""), ","))
| eval urgency=case(
    days_left <= 0, "EXPIRED",
    days_left <= 7, "CRITICAL",
    days_left <= 30, "WARNING",
    days_left <= 90, "NOTICE",
    1=1, "OK")
| eval weak_crypto=if(key_bits < 2048 OR match(sig_algo, "(?i)sha1|md5"), 1, 0)
| dedup registry sortby -_time
| sort days_left
| table registry days_left expiry_epoch issuer_cn key_bits sig_algo san_count urgency weak_crypto

`comment("--- Image Pull TLS Failures — Kubernetes Event Correlation ---")`
index=containers sourcetype="kube:events" type="Warning" reason IN ("Failed", "FailedPulling", "ErrImagePull")
| where match(message, "(?i)x509|certificate|tls|handshake")
| eval ns=coalesce(namespace, object_namespace, involvedObject.namespace)
| eval pod=coalesce(involvedObject.name, object_name)
| eval registry_host=coalesce(mvindex(split(mvindex(split(message, "/"), 0), ":"), 0), "unknown")
| eval tls_error_type=case(
    match(message, "(?i)expired"), "CERT_EXPIRED",
    match(message, "(?i)unknown authority"), "UNTRUSTED_CA",
    match(message, "(?i)does not match"), "NAME_MISMATCH",
    match(message, "(?i)handshake"), "HANDSHAKE_FAILURE",
    1=1, "OTHER_TLS")
| bin _time span=1h
| stats count as tls_failures,
    dc(pod) as affected_pods,
    dc(ns) as affected_namespaces,
    values(tls_error_type) as error_types,
    latest(message) as example_msg
    by _time, registry_host
| sort -tls_failures
| table _time registry_host tls_failures affected_pods affected_namespaces error_types example_msg

`comment("--- Certificate Chain Trust Validation — CA and Intermediate Status ---")`
index=containers sourcetype="tls:certificate"
| eval registry=coalesce(registry_host, endpoint, host)
| eval chain_valid=coalesce(chain_validation, "unknown")
| eval chain_depth=coalesce(chain_depth, 0)
| eval issuer_org=coalesce(issuer_o, issuer_org, "unknown")
| eval key_bits=coalesce(key_size, key_length)
| eval sig_algo=coalesce(signature_algorithm, sig_alg)
| eval expiry_epoch=strptime(coalesce(not_after, expiry_time), "%b %d %H:%M:%S %Y %Z")
| eval days_left=round((expiry_epoch - now()) / 86400, 0)
| eval weak_crypto=if(key_bits < 2048 OR match(sig_algo, "(?i)sha1|md5"), 1, 0)
| eval cert_health=case(
    chain_valid="invalid", "CHAIN_BROKEN",
    days_left <= 0, "EXPIRED",
    days_left <= 7, "CRITICAL",
    weak_crypto=1, "WEAK_CRYPTO",
    1=1, "HEALTHY")
| dedup registry sortby -_time
| table registry days_left chain_valid chain_depth issuer_org key_bits sig_algo weak_crypto cert_health
| sort days_left
```

## Visualization

Gauge showing soonest expiry (days), certificate inventory table color-coded by urgency, timeline of TLS pull failures, single-value tiles (expired count, critical count, weak crypto count).

## Known False Positives

**load_balancer_tls_termination** — If a load balancer or CDN terminates TLS in front of the registry, the probe sees the load balancer's certificate, not the registry's. The load balancer certificate may have a different expiry than the backend registry certificate. Probe both endpoints if the architecture includes TLS termination layers.

**acme_auto_renewal** — Registries using Let's Encrypt or ACME-based certificate automation renew certificates automatically 30 days before expiry. The WARNING alert triggers but the certificate is renewed without manual intervention. Suppress WARNING alerts for ACME-managed registries and only alert on CRITICAL (indicating the automation failed).

**internal_ca_short_lived** — Organizations using internal PKI often issue short-lived certificates (30–90 days) with automated renewal. These certificates frequently trigger WARNING and NOTICE alerts even though the renewal process is automated. Configure per-registry urgency thresholds in the lookup to match the expected certificate lifecycle.

**certificate_pinning_rotation** — Some container runtimes or Kubernetes distributions pin certificates and require explicit trust store updates when certificates are rotated. A new certificate that passes the probe may still cause pull failures on nodes with outdated trust stores. Cross-reference certificate serial numbers between the probe and kubelet logs.

**wildcard_certificate_scope** — A wildcard certificate covering `*.registry.example.com` is probed once but covers multiple registry subdomains. If the wildcard certificate expires, all subdomains fail simultaneously. Track wildcard certificates separately and alert at a higher urgency level due to the larger blast radius.

**self_signed_development** — Development and testing environments often use self-signed certificates that are always flagged as untrusted by the chain validation. Exclude known development registries from the untrusted CA alert or tag them in the registry inventory lookup.

## References

- [OpenSSL — s_client Documentation](https://www.openssl.org/docs/man3.0/man1/openssl-s_client.html)
- [Harbor — HTTPS Configuration](https://goharbor.io/docs/latest/install-config/configure-https/)
- [Kubernetes — Pull an Image from a Private Registry](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/)
- [Splunk — Scripted Inputs](https://docs.splunk.com/Documentation/Splunk/latest/Data/Monitorchangestofilesanddirectories)
- [Splunk eval Command Reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Eval)
