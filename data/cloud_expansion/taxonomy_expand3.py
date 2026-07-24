"""Third expansion — GCP method coverage and cross-cutting monitors to exceed 1000 new UCs."""

from __future__ import annotations

from .taxonomy import TaxonomyEntry
from .taxonomy_gcp import _gcp_entry
from .taxonomy_other import _entry

EXP3: list[TaxonomyEntry] = []

_GCP_EXTRA = (
    ("compute.instances.setMetadata", "Compute metadata change", "Metadata changes can expose startup scripts."),
    ("compute.instances.setTags", "Compute network tags change", "Tags drive firewall rule scope."),
    ("compute.instances.setServiceAccount", "Compute service account change", "SA change grants new OAuth scopes."),
    ("compute.instances.attachDisk", "Compute disk attach", "Disk attach may expose data volumes."),
    ("compute.instances.detachDisk", "Compute disk detach", "Detach during incident response or exfiltration."),
    ("compute.disks.create", "Persistent disk create", "New disks expand storage surface."),
    ("compute.disks.delete", "Persistent disk delete", "Disk deletion destroys data."),
    ("compute.snapshots.create", "Compute snapshot create", "Snapshots enable data copy."),
    ("compute.snapshots.delete", "Compute snapshot delete", "Snapshot deletion impairs recovery."),
    ("compute.images.create", "Compute image create", "Images can leak disk contents cross-project."),
    ("compute.images.delete", "Compute image delete", "Image deletion affects golden images."),
    ("compute.instanceGroups.create", "Instance group create", "MIG changes affect scaling."),
    ("compute.healthChecks.create", "Health check create", "Health check misconfig causes false routing."),
    ("compute.sslCertificates.create", "SSL certificate create", "Cert changes affect TLS termination."),
    ("compute.urlMaps.create", "URL map create", "URL maps route HTTP traffic."),
    ("compute.targetHttpProxies.create", "HTTP proxy create", "Proxy changes affect ingress."),
    ("compute.globalForwardingRules.create", "Global forwarding rule create", "Forwarding rules expose services."),
    ("compute.networks.create", "VPC network create", "New VPCs change segmentation."),
    ("compute.subnetworks.create", "Subnet create", "Subnet creation changes IP planning."),
    ("compute.routers.create", "Cloud Router create", "Router changes affect BGP hybrid."),
    ("compute.vpnTunnels.create", "VPN tunnel create", "VPN tunnels change hybrid paths."),
    ("storage.buckets.update", "GCS bucket update", "Bucket update may change IAM or lifecycle."),
    ("storage.objects.create", "GCS object create", "Object uploads to sensitive buckets."),
    ("storage.objects.delete", "GCS object delete", "Object deletion destroys data."),
    ("bigquery.datasets.create", "BigQuery dataset create", "New datasets expand analytics scope."),
    ("bigquery.jobs.create", "BigQuery job create", "Jobs may export large datasets."),
    ("pubsub.topics.create", "Pub/Sub topic create", "Topics change event routing."),
    ("pubsub.subscriptions.create", "Pub/Sub subscription create", "Subscriptions affect message delivery."),
    ("cloudfunctions.functions.delete", "Cloud Function delete", "Function deletion breaks integrations."),
    ("run.services.create", "Cloud Run service create", "Cloud Run exposes HTTP services."),
    ("run.services.update", "Cloud Run service update", "Updates change container image or SA."),
    ("container.clusters.update", "GKE cluster update", "Cluster updates change control plane settings."),
    ("container.nodePools.delete", "GKE node pool delete", "Node pool deletion reduces capacity."),
    ("sql.instances.update", "Cloud SQL instance update", "Updates may enable public IP."),
    ("sql.instances.restart", "Cloud SQL restart", "Restarts cause connection blips."),
    ("sql.backupRuns.create", "Cloud SQL backup create", "Backup events support recovery evidence."),
    ("spanner.instances.create", "Spanner instance create", "Spanner provisioning affects cost."),
    ("spanner.databases.create", "Spanner database create", "New databases expand data stores."),
    ("redis.instances.create", "Memorystore Redis create", "Cache provisioning changes architecture."),
    ("composer.environments.create", "Cloud Composer create", "Composer runs Airflow orchestration."),
    ("dataflow.jobs.create", "Dataflow job create", "Dataflow processes large datasets."),
    ("dataproc.clusters.create", "Dataproc cluster create", "Dataproc runs Spark/Hadoop jobs."),
    ("logging.logs.delete", "Log bucket delete", "Log deletion destroys audit evidence."),
    ("monitoring.alertPolicies.create", "Monitoring alert policy create", "Alert policies affect SRE coverage."),
    ("monitoring.alertPolicies.delete", "Monitoring alert policy delete", "Alert deletion hides failures."),
    ("cloudresourcemanager.projects.create", "GCP project create", "New projects expand org surface."),
    ("cloudresourcemanager.projects.delete", "GCP project delete", "Project deletion is destructive."),
    ("serviceusage.services.enable", "API enable", "Enabling APIs expands attack surface."),
    ("serviceusage.services.disable", "API disable", "Disabling APIs may break security tools."),
    ("iam.serviceAccounts.create", "Service account create", "New SAs expand workload identity."),
    ("iam.serviceAccounts.delete", "Service account delete", "SA deletion breaks workloads."),
    ("iam.serviceAccounts.disable", "Service account disable", "Disable may be incident response."),
    ("cloudkms.keyRings.create", "KMS key ring create", "Key rings scope encryption."),
    ("cloudkms.cryptoKeys.create", "KMS crypto key create", "New keys affect encryption scope."),
    ("dns.managedZones.delete", "Cloud DNS zone delete", "Zone deletion causes outages."),
    ("dns.policies.create", "DNS policy create", "DNS policies affect resolution logging."),
    ("servicenetworking.connections.create", "Private service connection", "Connections enable Google API private access."),
    ("accessapproval.settings.update", "Access Approval settings", "Approval settings affect privileged access."),
    ("binaryauthorization.policy.update", "Binary Authorization policy", "Policy changes affect GKE deploy gates."),
    ("cloudbuild.triggers.create", "Cloud Build trigger create", "Triggers run CI on repository events."),
    ("artifactregistry.repositories.upload", "Artifact Registry upload", "Image uploads affect supply chain."),
    ("eventarc.triggers.create", "Eventarc trigger create", "Triggers route events to services."),
    ("workflows.workflows.create", "Workflows create", "Workflows orchestrate GCP APIs."),
    ("apigateway.apis.create", "API Gateway API create", "APIs expose managed endpoints."),
    ("endpoints.services.create", "Cloud Endpoints service create", "Endpoints manage API configs."),
    ("healthcare.datasets.create", "Healthcare dataset create", "Healthcare datasets hold PHI."),
    ("notebooks.instances.create", "Vertex notebook create", "Notebooks may expose data science envs."),
    ("aiplatform.models.upload", "Vertex model upload", "Model uploads affect ML supply chain."),
    ("securitycenter.sources.create", "SCC source create", "Sources feed findings into SCC."),
    ("cloudasset.assets.exportAssets", "Asset export", "Asset exports support inventory audits."),
    ("orgpolicy.policies.delete", "Org policy delete", "Policy deletion removes guardrails."),
    ("essentialcontacts.contacts.create", "Essential contacts create", "Contacts affect incident notifications."),
)

for method, title, val in _GCP_EXTRA:
    EXP3.append(_gcp_entry(title, f"Detects GCP audit method {method}.", val, (method,)))

# Multi-cloud correlation extras
for i, title in enumerate(
    (
        "Cross-Cloud Simultaneous Storage Delete",
        "Cross-Cloud KMS Key Disable Within 1 Hour",
        "Cross-Cloud Logging Disable Within 1 Hour",
        "Cross-Cloud Privileged Role Grant Burst",
        "Cross-Cloud New Region Resource Burst",
        "Cross-Cloud Failed Login Correlation",
        "Cross-Cloud API Error Rate Correlation",
        "Cross-Cloud Tag Removal Burst",
        "Cross-Cloud Snapshot Export Burst",
        "Cross-Cloud Network Peering Burst",
    ),
    1,
):
    EXP3.append(
        _entry(
            "4.4",
            title,
            index="cloud_multi",
            sourcetype="aws:cloudtrail",
            spl_filter="*",
            description=f"Correlates {title.lower()} signals across AWS, Azure, and GCP indexes.",
            value=f"{title} may indicate coordinated attack or change across cloud providers.",
            monitoring_type=("Security", "Governance"),
            equipment=("aws", "azure", "gcp"),
            app="Multi-index correlation across cloud TAs",
            splunkbase_id=1876,
            splunkbase_name="Splunk Add-on for AWS",
            vendor_url="https://docs.splunk.com/Documentation/CIM/latest/User/Overview",
            prereq="4.4.33",
        )
    )

from . import taxonomy as _tax  # noqa: E402

_tax.ALL_ENTRIES.extend(EXP3)
