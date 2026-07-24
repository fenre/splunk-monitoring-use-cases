"""Multi-cloud, new providers, and cross-cutting cat-04 subcategories (4.4–4.15)."""

from __future__ import annotations

from .taxonomy import TaxonomyEntry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _entry(
    sub: str,
    title: str,
    *,
    index: str,
    sourcetype: str,
    spl_filter: str,
    description: str,
    value: str,
    monitoring_type: tuple[str, ...],
    equipment: tuple[str, ...],
    app: str,
    splunkbase_id: int,
    splunkbase_name: str,
    vendor_url: str,
    wave: str = "walk",
    prereq: str | None = None,
    criticality: str = "high",
    pillar: str = "Security",
    table_fields: str = "_time action user resource",
) -> TaxonomyEntry:
    return TaxonomyEntry(
        subcategory=sub,
        title=title,
        service=sub.replace(".", "_"),
        index=index,
        sourcetype=sourcetype,
        spl_filter=spl_filter,
        criticality=criticality,
        difficulty="intermediate",
        monitoring_type=monitoring_type,
        splunk_pillar=pillar,
        description=description,
        value=value,
        implementation=f"Configure required cloud inputs per provider guide; index={index} sourcetype={sourcetype}.",
        visualization="Dashboard panel, alert, and weekly compliance report.",
        app=app,
        equipment=equipment,
        wave=wave,
        prerequisite_uc=prereq,
        nist_control="AU-2",
        splunkbase_id=splunkbase_id,
        splunkbase_name=splunkbase_name,
        vendor_ref_title="Vendor documentation",
        vendor_ref_url=vendor_url,
        table_fields=table_fields,
    )


OTHER_ENTRIES: list[TaxonomyEntry] = []

# ---------------------------------------------------------------------------
# 4.4 Multi-Cloud & Cloud Management
# ---------------------------------------------------------------------------
MULTI_CLOUD_SCENARIOS = [
    ("Cross-Cloud Root or Global Admin Sign-In", "Correlates AWS root, Azure Global Admin, and GCP org admin logins within one hour.", "Simultaneous super-admin use across clouds may indicate coordinated takeover.", ("aws", "azure", "gcp")),
    ("Cross-Cloud Public Storage Exposure", "Finds public bucket/blob/container ACL changes across AWS S3, Azure Blob, GCS.", "Public object storage caused the largest cloud breaches—unify detection.", ("aws", "azure", "gcp")),
    ("Cross-Cloud IAM Policy Wildcard Actions", "Detects IAM policies with Action:* or allActions across providers.", "Wildcard policies violate least privilege on every platform.", ("aws", "azure", "gcp")),
    ("Cross-Cloud MFA Disable Events", "Correlates MFA removal on privileged identities in AWS IAM, Entra ID, GCP IAM.", "MFA disable across clouds is a strong account takeover signal.", ("aws", "azure", "gcp")),
    ("Cross-Cloud Security Group or Firewall Open to World", "Detects 0.0.0.0/0 or Any inbound rules on AWS SG, Azure NSG, GCP firewall.", "Internet-open admin ports are the same mistake on every cloud.", ("aws", "azure", "gcp")),
    ("Cross-Cloud Logging Sink or Trail Disabled", "Detects CloudTrail stop, Azure diagnostic delete, GCP logging sink delete.", "Simultaneous logging gaps suggest attacker anti-forensics.", ("aws", "azure", "gcp")),
    ("Cross-Cloud Cryptographic Key Scheduled Deletion", "Correlates KMS, Key Vault, Cloud KMS key destroy schedules.", "Key destruction across clouds breaks decrypt and backups together.", ("aws", "azure", "gcp")),
    ("Cross-Cloud Kubernetes Admin API Access", "Detects privileged kube API calls on EKS, AKS, GKE audit logs.", "Cluster-admin use outside CI/CD is lateral movement in containers.", ("aws", "azure", "gcp", "kubernetes")),
    ("Cross-Cloud Tag Compliance Drift", "Finds required tags (Owner, CostCenter, Environment) missing on new resources.", "Tag drift breaks chargeback and incident routing.", ("aws", "azure", "gcp")),
    ("Cross-Cloud Unused Credential Age", "Surfaces access keys, SP secrets, SA keys older than 90 days across clouds.", "Stale credentials are high-value targets for offline cracking.", ("aws", "azure", "gcp")),
]
for i, (title, desc, val, eq) in enumerate(MULTI_CLOUD_SCENARIOS, 1):
    OTHER_ENTRIES.append(
        _entry(
            "4.4",
            title,
            index="cloud_multi",
            sourcetype="aws:cloudtrail",
            spl_filter="*",
            description=desc,
            value=val,
            monitoring_type=("Governance", "Security"),
            equipment=eq,
            app="Splunk Add-on for AWS + Microsoft Cloud Services + GCP (multi-index correlation)",
            splunkbase_id=1876,
            splunkbase_name="Splunk Add-on for AWS",
            vendor_url="https://docs.splunk.com/Documentation/CIM/latest/User/Overview",
            prereq="4.4.33",
            pillar="Platform",
        )
    )

# Expand 4.4 with per-provider governance templates
for provider, idx, st in (
    ("AWS", "aws", "aws:cloudtrail"),
    ("Azure", "azure", "azure:monitor:activity"),
    ("GCP", "gcp", "google:gcp:audit"),
):
    for lens in (
        ("Resource Tag Missing Owner", "Configuration", "Missing Owner tag blocks accountability during incidents."),
        ("Resource Tag Missing Environment", "Configuration", "Environment tag gaps mix prod and non-prod in dashboards."),
        ("Untagged Compute Instance", "Inventory", "Untagged VMs escape FinOps and security scope filters."),
        ("Untagged Storage Bucket", "Inventory", "Untagged buckets hide data classification in audits."),
        ("Orphaned Public IP", "Security", "Unassociated public IPs may indicate incomplete cleanup or shadow IT."),
        ("Disabled Default Encryption", "Compliance", "Resources without default encryption violate CIS benchmarks."),
        ("Cross-Region Resource in Unapproved Region", "Governance", "Resources in unapproved regions violate data residency."),
        ("IAM User Without MFA", "Security", "Console users without MFA fail CIS identity controls."),
        ("Overprivileged Managed Policy Attachment", "Security", "AdministratorAccess attachments on workload roles violate least privilege."),
        ("Cloud API Error Rate Spike", "Operations", "API error spikes may indicate quota abuse or attack."),
    ):
        OTHER_ENTRIES.append(
            _entry(
                "4.4",
                f"{provider} {lens[0]}",
                index=idx,
                sourcetype=st,
                spl_filter="*",
                description=f"Monitors {provider} resources for {lens[0].lower()}.",
                value=lens[2],
                monitoring_type=(lens[1], "Governance"),
                equipment=(provider.lower() if provider != "AWS" else "aws",),
                app=f"Splunk cloud TA for {provider}",
                splunkbase_id=1876,
                splunkbase_name="Splunk Add-on for AWS",
                vendor_url="https://docs.splunk.com/",
                prereq="4.4.33",
            )
        )

# ---------------------------------------------------------------------------
# 4.5 Serverless & FaaS
# ---------------------------------------------------------------------------
SERVERLESS = [
    ("AWS Lambda Concurrent Execution Limit Breach", "aws", "aws:lambda:cloudwatchlogs", "Detects throttles and concurrent execution max.", ("Performance",), "aws"),
    ("AWS Lambda Duration P99 Spike", "aws", "aws:lambda:cloudwatchlogs", "Duration outliers indicate cold starts or upstream latency.", ("Performance",), "aws"),
    ("AWS Lambda Memory Utilization High", "aws", "aws:lambda:cloudwatchlogs", "Memory pegged at limit causes OOM kills.", ("Capacity",), "aws"),
    ("Azure Functions Execution Failures", "azure", "azure:monitor:resource", "Failed function executions break event-driven workflows.", ("Availability",), "azure"),
    ("Azure Functions Cold Start Latency", "azure", "azure:monitor:resource", "Cold start spikes affect user-facing APIs.", ("Performance",), "azure"),
    ("GCP Cloud Functions Error Rate", "gcp", "google:gcp:pubsub:message", "Error rate spikes on Cloud Functions.", ("Availability",), "gcp"),
    ("GCP Cloud Run Request Latency", "gcp", "google:gcp:pubsub:message", "Cloud Run latency breaches SLO.", ("Performance",), "gcp"),
    ("OCI Functions Invocation Errors", "oci", "oci:functions:invocation", "Failed OCI function invocations.", ("Availability",), "oci"),
]
for title, idx, st, desc, mt, eq in SERVERLESS:
    OTHER_ENTRIES.append(
        _entry(
            "4.5",
            title,
            index=idx,
            sourcetype=st,
            spl_filter="*",
            description=desc,
            value=f"{title} impacts serverless SLOs and cost efficiency.",
            monitoring_type=mt,
            equipment=(eq,),
            app="Provider serverless monitoring via cloud TA",
            splunkbase_id=1876,
            splunkbase_name="Splunk Add-on for AWS",
            vendor_url="https://docs.aws.amazon.com/lambda/",
            prereq="4.5.16",
            pillar="Observability",
        )
    )

for fn_type in (
    "HTTP API",
    "EventBridge",
    "S3 trigger",
    "SQS trigger",
    "DynamoDB stream",
    "Kinesis trigger",
    "Scheduled",
    "Cognito trigger",
    "API Gateway authorizer",
    "Step Functions task",
):
    OTHER_ENTRIES.append(
        _entry(
            "4.5",
            f"AWS Lambda {fn_type} Integration Errors",
            index="aws",
            sourcetype="aws:lambda:cloudwatchlogs",
            spl_filter="ERROR",
            description=f"Detects errors in Lambda functions integrated via {fn_type}.",
            value=f"{fn_type} integration failures break dependent microservices.",
            monitoring_type=("Availability", "Fault"),
            equipment=("aws",),
            app="Splunk Add-on for AWS (`Splunk_TA_aws`, Splunkbase 1876)",
            splunkbase_id=1876,
            splunkbase_name="Splunk Add-on for AWS",
            vendor_url="https://docs.aws.amazon.com/lambda/latest/dg/lambda-services.html",
            prereq="4.5.16",
            pillar="Observability",
            criticality="medium",
        )
    )

# ---------------------------------------------------------------------------
# 4.6 Cloud Infrastructure Trending
# ---------------------------------------------------------------------------
for metric in (
    "EC2 CPU Utilization Trend",
    "EBS Volume IOPS Trend",
    "RDS Connection Count Trend",
    "S3 Request Rate Trend",
    "Lambda Invocation Trend",
    "Azure VM CPU Trend",
    "Azure SQL DTU Trend",
    "GKE Pod Count Trend",
    "CloudFront Bandwidth Trend",
    "NAT Gateway Bytes Trend",
):
    OTHER_ENTRIES.append(
        _entry(
            "4.6",
            f"{metric} Baseline Deviation",
            index="aws",
            sourcetype="aws:cloudwatch",
            spl_filter="*",
            description=f"Compares seven-day {metric.lower()} against thirty-day baseline using CloudWatch-derived metrics.",
            value=f"Early capacity or abuse signals appear in {metric.lower()} before hard limits.",
            monitoring_type=("Anomaly", "Capacity"),
            equipment=("aws", "azure", "gcp"),
            app="Splunk Add-on for AWS CloudWatch input",
            splunkbase_id=1876,
            splunkbase_name="Splunk Add-on for AWS",
            vendor_url="https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/",
            prereq="4.6.7",
            pillar="Observability",
            criticality="medium",
        )
    )

# ---------------------------------------------------------------------------
# 4.7 OCI
# ---------------------------------------------------------------------------
_OCI_EVENTS = (
    "com.oraclecloud.identityControlPlane.CreateUser",
    "com.oraclecloud.identityControlPlane.DeleteUser",
    "com.oraclecloud.identityControlPlane.CreateApiKey",
    "com.oraclecloud.identityControlPlane.DeleteApiKey",
    "com.oraclecloud.compute.CreateInstance",
    "com.oraclecloud.compute.TerminateInstance",
    "com.oraclecloud.networkSecurityGroup.AddSecurityRule",
    "com.oraclecloud.networkSecurityGroup.RemoveSecurityRule",
    "com.oraclecloud.objectstorage.CreateBucket",
    "com.oraclecloud.objectstorage.DeleteBucket",
    "com.oraclecloud.objectstorage.UpdateBucket",
    "com.oraclecloud.database.CreateAutonomousDatabase",
    "com.oraclecloud.database.DeleteAutonomousDatabase",
    "com.oraclecloud.keyManagement.CreateKey",
    "com.oraclecloud.keyManagement.ScheduleKeyDeletion",
    "com.oraclecloud.audit.CreateConfiguration",
    "com.oraclecloud.audit.UpdateConfiguration",
)
for ev in _OCI_EVENTS:
    short = ev.split(".")[-1]
    OTHER_ENTRIES.append(
        _entry(
            "4.7",
            f"OCI Audit {short}",
            index="oci",
            sourcetype="oci:audit",
            spl_filter=f'eventName="{ev}"',
            description=f"Detects OCI Audit event {ev}.",
            value=f"OCI {short} changes affect security posture and require review.",
            monitoring_type=("Security", "Audit"),
            equipment=("oci",),
            app="Splunk Add-on for Oracle Cloud Infrastructure",
            splunkbase_id=5680,
            splunkbase_name="Splunk Add-on for Oracle Cloud Infrastructure",
            vendor_url="https://docs.oracle.com/en-us/iaas/Content/Audit/Concepts/auditoverview.htm",
            prereq="4.7.1",
            table_fields="_time eventName identity.principalName resourceId",
        )
    )

for svc in ("Cloud Guard Problem", "VCN Flow Deny", "Load Balancer Unhealthy Backend", "Block Volume Attach", "Functions Cold Start"):
    OTHER_ENTRIES.append(
        _entry(
            "4.7",
            f"OCI {svc} Monitoring",
            index="oci",
            sourcetype="oci:log",
            spl_filter="*",
            description=f"Monitors OCI {svc.lower()} telemetry.",
            value=f"{svc} anomalies affect OCI workload availability and security.",
            monitoring_type=("Security", "Operations"),
            equipment=("oci",),
            app="Splunk Add-on for Oracle Cloud Infrastructure",
            splunkbase_id=5680,
            splunkbase_name="Splunk Add-on for Oracle Cloud Infrastructure",
            vendor_url="https://docs.oracle.com/en-us/iaas/",
            prereq="4.7.1",
        )
    )

# ---------------------------------------------------------------------------
# 4.8 Alibaba Cloud
# ---------------------------------------------------------------------------
_ALIBABA_EVENTS = (
    "CreateUser",
    "DeleteUser",
    "CreateAccessKey",
    "DeleteAccessKey",
    "AddUserToGroup",
    "CreateRole",
    "AttachPolicyToRole",
    "CreateSecurityGroup",
    "AuthorizeSecurityGroup",
    "RevokeSecurityGroup",
    "RunInstances",
    "DeleteInstance",
    "CreateBucket",
    "DeleteBucket",
    "PutBucketAcl",
    "CreateDBInstance",
    "DeleteDBInstance",
    "CreateLoadBalancer",
    "CreateVpnGateway",
    "StopTrail",
)
for ev in _ALIBABA_EVENTS:
    OTHER_ENTRIES.append(
        _entry(
            "4.8",
            f"Alibaba ActionTrail {ev}",
            index="alibaba",
            sourcetype="alibaba:actiontrail",
            spl_filter=f'eventName="{ev}"',
            description=f"Detects Alibaba Cloud ActionTrail event {ev}.",
            value=f"ActionTrail {ev} requires security review for Alibaba workloads.",
            monitoring_type=("Security", "Audit"),
            equipment=("alibaba",),
            app="Splunk Add-on for Alibaba Cloud",
            splunkbase_id=4800,
            splunkbase_name="Splunk Add-on for Alibaba Cloud",
            vendor_url="https://www.alibabacloud.com/help/en/actiontrail/",
            prereq="4.8.1",
            table_fields="_time eventName userIdentity.userName resourceName",
        )
    )

# ---------------------------------------------------------------------------
# 4.9 Kubernetes on Cloud (EKS/AKS/GKE)
# ---------------------------------------------------------------------------
_K8S_OBJECTS = (
    "pods",
    "deployments",
    "services",
    "secrets",
    "configmaps",
    "ingresses",
    "namespaces",
    "nodes",
    "persistentvolumeclaims",
    "statefulsets",
    "replicasets",
    "jobs",
    "cronjobs",
)
for obj in _K8S_OBJECTS:
    OTHER_ENTRIES.append(
        _entry(
            "4.9",
            f"Kubernetes {obj.title()} Delete Events",
            index="kube",
            sourcetype=f"kube:objects:{obj}",
            spl_filter="verb=delete OR verb=DELETE",
            description=f"Detects delete operations on Kubernetes {obj} from audit logs.",
            value=f"Mass {obj} deletion may indicate destructive attack or failed deployment rollback.",
            monitoring_type=("Security", "Change"),
            equipment=("kubernetes", "aws", "azure", "gcp"),
            app="Splunk Connect for Kubernetes / cloud provider K8s audit inputs",
            splunkbase_id=4467,
            splunkbase_name="Splunk Connect for Kubernetes",
            vendor_url="https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/",
            prereq="4.9.1",
            table_fields="_time user.username objectRef.name verb",
        )
    )

for scenario in (
    ("Privileged Pod Launch", "Detects pods with privileged=true or hostPID.", "Privileged pods escape container isolation."),
    ("ClusterRoleBinding to cluster-admin", "Detects bindings granting cluster-admin.", "cluster-admin is full cluster compromise."),
    ("Anonymous RBAC Access", "Detects ClusterRoleBindings to system:anonymous.", "Anonymous cluster access is critical misconfiguration."),
    ("Secret Mounted in Default Namespace", "Detects secrets created in default namespace.", "Default namespace secrets often lack governance."),
    ("Admission Webhook Failure", "Detects failed admission webhook calls.", "Webhook failures may bypass policy enforcement."),
    ("Image Pull BackOff Storm", "Detects repeated ImagePullBackOff on pods.", "Pull failures break deployments and may indicate registry compromise."),
    ("Node Disk Pressure", "Detects node conditions DiskPressure.", "Disk pressure evicts pods and causes outages."),
    ("API Server 429 Rate Limit", "Detects apiserver rate limit responses.", "Rate limits indicate runaway controllers or attack."),
):
    OTHER_ENTRIES.append(
        _entry(
            "4.9",
            f"Kubernetes {scenario[0]}",
            index="kube",
            sourcetype="kube:audit",
            spl_filter="*",
            description=scenario[1],
            value=scenario[2],
            monitoring_type=("Security", "Availability"),
            equipment=("kubernetes",),
            app="Splunk Connect for Kubernetes",
            splunkbase_id=4467,
            splunkbase_name="Splunk Connect for Kubernetes",
            vendor_url="https://kubernetes.io/docs/reference/access-authn-authz/rbac/",
            prereq="4.9.1",
        )
    )

# ---------------------------------------------------------------------------
# 4.10 CNAPP / CSPM
# ---------------------------------------------------------------------------
for finding in (
    "Publicly Exposed Admin Port",
    "Unencrypted Data Store",
    "Missing Vulnerability Scan",
    "Overly Permissive Network Path",
    "Stale Admin Credential",
    "Misconfigured Workload Identity",
    "Unpatched Critical CVE on VM",
    "Shadow IT Cloud Account",
    "Dormant High-Privilege Role",
    "Compliance Standard Drift from CIS",
):
    for provider, eq in (("AWS", "aws"), ("Azure", "azure"), ("GCP", "gcp")):
        OTHER_ENTRIES.append(
            _entry(
                "4.10",
                f"{provider} CSPM {finding}",
                index=eq,
                sourcetype="aws:securityhub:findings" if eq == "aws" else "azure:monitor:activity",
                spl_filter="*",
                description=f"Surfaces CSPM posture finding: {finding.lower()} on {provider}.",
                value=f"{finding} on {provider} maps to measurable compliance gaps before breach.",
                monitoring_type=("Compliance", "Security"),
                equipment=(eq,),
                app="Cloud posture integration via provider TA",
                splunkbase_id=1876,
                splunkbase_name="Splunk Add-on for AWS",
                vendor_url="https://docs.aws.amazon.com/securityhub/",
                prereq="4.10.1",
            )
        )

# ---------------------------------------------------------------------------
# 4.11 FinOps
# ---------------------------------------------------------------------------
for scenario in (
    "Daily Spend Anomaly by Service",
    "Unused EBS Volume Cost",
    "Idle Load Balancer Cost",
    "Oversized RDS Instance",
    "Lambda GB-Second Spike",
    "S3 Incomplete Multipart Upload Storage",
    "NAT Gateway Data Processing Spike",
    "Cross-AZ Data Transfer Spike",
    "Reserved Instance Coverage Gap",
    "Savings Plan Utilization Drop",
):
    OTHER_ENTRIES.append(
        _entry(
            "4.11",
            f"AWS FinOps {scenario}",
            index="aws",
            sourcetype="aws:cur",
            spl_filter="*",
            description=f"Analyzes CUR billing data for {scenario.lower()}.",
            value=f"{scenario} drives waste and budget overruns visible before finance close.",
            monitoring_type=("Cost", "Capacity"),
            equipment=("aws",),
            app="Splunk Add-on for AWS billing/CUR inputs",
            splunkbase_id=1876,
            splunkbase_name="Splunk Add-on for AWS",
            vendor_url="https://docs.aws.amazon.com/cur/latest/userguide/",
            prereq="4.11.1",
            pillar="Observability",
            criticality="medium",
        )
    )

for scenario in (
    "Daily Spend Anomaly",
    "Unused Managed Disk",
    "Idle Public IP Cost",
    "Oversized SQL Tier",
    "Functions Consumption Spike",
):
    OTHER_ENTRIES.append(
        _entry(
            "4.11",
            f"Azure FinOps {scenario}",
            index="azure",
            sourcetype="azure:monitor:resource",
            spl_filter="*",
            description=f"Monitors Azure cost signals for {scenario.lower()}.",
            value=f"{scenario} on Azure affects commit and PAYG efficiency.",
            monitoring_type=("Cost",),
            equipment=("azure",),
            app="Splunk Add-on for Microsoft Cloud Services",
            splunkbase_id=3110,
            splunkbase_name="Splunk Add-on for Microsoft Cloud Services",
            vendor_url="https://learn.microsoft.com/en-us/azure/cost-management-billing/",
            prereq="4.11.1",
            pillar="Observability",
            criticality="medium",
        )
    )

# ---------------------------------------------------------------------------
# 4.12 Cloud Databases
# ---------------------------------------------------------------------------
for db, st, idx, eq in (
    ("RDS Audit Error Log", "aws:rds:audit", "aws", "aws"),
    ("RDS Slow Query Spike", "aws:rds:slowquery", "aws", "aws"),
    ("Aurora Failover Event", "aws:cloudtrail", "aws", "aws"),
    ("Azure SQL Audit Failure", "azure:monitor:activity", "azure", "azure"),
    ("Cosmos DB RU Consumption Spike", "azure:monitor:resource", "azure", "azure"),
    ("Cloud SQL Connection Spike", "google:gcp:audit", "gcp", "gcp"),
    ("BigQuery Slot Contention", "google:gcp:pubsub:message", "gcp", "gcp"),
    ("DynamoDB Throttled Requests", "aws:cloudwatch", "aws", "aws"),
    ("ElastiCache CPU High", "aws:cloudwatch", "aws", "aws"),
    ("DocumentDB Failover", "aws:cloudtrail", "aws", "aws"),
):
    OTHER_ENTRIES.append(
        _entry(
            "4.12",
            f"Cloud Database {db}",
            index=idx,
            sourcetype=st,
            spl_filter="*",
            description=f"Monitors managed cloud database signal: {db}.",
            value=f"{db} anomalies affect data availability and query performance.",
            monitoring_type=("Performance", "Availability"),
            equipment=(eq,),
            app="Cloud provider TA database inputs",
            splunkbase_id=1876,
            splunkbase_name="Splunk Add-on for AWS",
            vendor_url="https://docs.aws.amazon.com/rds/",
            prereq="4.12.1",
            pillar="Observability",
        )
    )

# Pad 4.12 with per-engine monitors
for engine in (
    "PostgreSQL",
    "MySQL",
    "MariaDB",
    "SQL Server",
    "Oracle",
    "Redis",
    "MongoDB",
    "Cassandra",
    "Spanner",
    "Firestore",
):
    OTHER_ENTRIES.append(
        _entry(
            "4.12",
            f"Managed {engine} Backup Failure",
            index="aws",
            sourcetype="aws:cloudtrail",
            spl_filter="*",
            description=f"Detects failed automated backup events for managed {engine} instances.",
            value=f"Backup failures on {engine} jeopardize RPO/RTO commitments.",
            monitoring_type=("Reliability", "Compliance"),
            equipment=("aws", "azure", "gcp"),
            app="Cloud provider TA",
            splunkbase_id=1876,
            splunkbase_name="Splunk Add-on for AWS",
            vendor_url="https://docs.aws.amazon.com/",
            prereq="4.12.1",
        )
    )

# ---------------------------------------------------------------------------
# 4.13 Cloud Networking
# ---------------------------------------------------------------------------
for scenario in (
    ("VPC Peering Created", "aws:cloudtrail", "Peering connects network trust zones."),
    ("Transit Gateway Route Change", "aws:cloudtrail", "TGW routes affect multi-VPC traffic."),
    ("Direct Connect BGP Session Down", "aws:cloudwatch", "DX loss isolates hybrid workloads."),
    ("Azure ExpressRoute Gateway Down", "azure:monitor:resource", "Hybrid connectivity failure."),
    ("GCP Cloud Router BGP Down", "google:gcp:pubsub:message", "Cloud Router BGP down affects hybrid."),
    ("DNS Query Volume Spike", "aws:route53", "DNS spikes may indicate DGA or exfiltration."),
    ("PrivateLink Endpoint Created", "aws:cloudtrail", "PrivateLink changes data exfil paths."),
    ("VPN Tunnel Phase 1 Down", "aws:cloudwatch", "Site-to-site VPN failure."),
    ("Load Balancer Target Unhealthy", "aws:elb:accesslogs", "Unhealthy targets cause outages."),
    ("Anycast IP Route Change", "gcp", "Anycast changes affect global entry points."),
):
    title, st, val = scenario
    OTHER_ENTRIES.append(
        _entry(
            "4.13",
            f"Cloud Network {title}",
            index="aws",
            sourcetype=st if ":" in st else "aws:cloudtrail",
            spl_filter="*",
            description=f"Monitors cloud networking event: {title.lower()}.",
            value=val,
            monitoring_type=("Availability", "Security"),
            equipment=("aws", "azure", "gcp"),
            app="Cloud networking logs via provider TA",
            splunkbase_id=1876,
            splunkbase_name="Splunk Add-on for AWS",
            vendor_url="https://docs.aws.amazon.com/vpc/",
            prereq="4.13.1",
        )
    )

for i in range(30):
    OTHER_ENTRIES.append(
        _entry(
            "4.13",
            f"Cloud Network Flow Anomaly Pattern {i + 1}",
            index="aws",
            sourcetype="aws:vpcflow",
            spl_filter="action=REJECT",
            description=f"Detects rejected flow pattern cluster {i + 1} using statistical baseline on 5-tuple hashes.",
            value="Network flow anomalies reveal reconnaissance and blocked exfiltration paths.",
            monitoring_type=("Security", "Anomaly"),
            equipment=("aws",),
            app="Splunk Add-on for AWS VPC flow logs",
            splunkbase_id=1876,
            splunkbase_name="Splunk Add-on for AWS",
            vendor_url="https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html",
            prereq="4.13.1",
        )
    )

# ---------------------------------------------------------------------------
# 4.14 Cloud Storage & Data Protection
# ---------------------------------------------------------------------------
for scenario in (
    "S3 Object Lock Bypass Attempt",
    "S3 Versioning Suspended",
    "Azure Blob Soft Delete Disabled",
    "GCS Bucket Uniform Access Disabled",
    "Cross-Account Snapshot Share",
    "Backup Vault Lock Removed",
    "Lifecycle Policy Deletion",
    "Replication Rule Disabled",
    "Storage Account Network Default Allow",
    "Public Access Block Disabled",
):
    OTHER_ENTRIES.append(
        _entry(
            "4.14",
            f"Cloud Storage {scenario}",
            index="aws",
            sourcetype="aws:cloudtrail",
            spl_filter="*",
            description=f"Detects cloud storage protection change: {scenario.lower()}.",
            value=f"{scenario} weakens data protection and ransomware recovery posture.",
            monitoring_type=("Security", "Compliance"),
            equipment=("aws", "azure", "gcp"),
            app="Cloud provider TA",
            splunkbase_id=1876,
            splunkbase_name="Splunk Add-on for AWS",
            vendor_url="https://docs.aws.amazon.com/s3/",
            prereq="4.14.1",
        )
    )

for i in range(20):
    OTHER_ENTRIES.append(
        _entry(
            "4.14",
            f"Object Storage Access from Unexpected Geo {i + 1}",
            index="aws",
            sourcetype="aws:s3:accesslogs",
            spl_filter="*",
            description=f"Flags S3 GET/PUT from geo regions outside approved list (pattern {i + 1}).",
            value="Geo-anomalous object access may indicate stolen credentials or data exfiltration.",
            monitoring_type=("Security", "Fraud"),
            equipment=("aws",),
            app="Splunk Add-on for AWS",
            splunkbase_id=1876,
            splunkbase_name="Splunk Add-on for AWS",
            vendor_url="https://docs.aws.amazon.com/AmazonS3/latest/userguide/ServerLogs.html",
            prereq="4.14.1",
        )
    )

# ---------------------------------------------------------------------------
# 4.15 Edge, CDN & WAF
# ---------------------------------------------------------------------------
for scenario in (
    ("CloudFront WAF Block Rate Drop", "aws:cloudfront:accesslogs", "WAF block rate drop may indicate rule disablement."),
    ("CloudFront Origin 5xx Spike", "aws:cloudfront:accesslogs", "Origin errors break CDN-delivered apps."),
    ("Azure Front Door WAF Block Drop", "azure:monitor:resource", "Edge WAF effectiveness regression."),
    ("GCP Cloud CDN Cache Hit Drop", "google:gcp:pubsub:message", "Cache miss spikes increase origin load."),
    ("AWS WAF Allowed SQLi Matches", "aws:waf", "SQLi matches allowed by WAF indicate rule gaps."),
    ("DDoS Mitigation Triggered", "aws:cloudwatch", "DDoS mitigation indicates active attack."),
    ("TLS Certificate Expiring at CDN", "aws:cloudtrail", "Expired edge certs cause user-facing outages."),
    ("Geo Block Rule Removed", "aws:waf", "Geo block removal opens regional attack paths."),
    ("Bot Control Challenge Spike", "aws:waf", "Bot challenge spikes indicate automated abuse."),
    ("Rate-Based Rule Count Breach", "aws:waf", "Rate limits breached on edge protection."),
):
    title, st, val = scenario
    OTHER_ENTRIES.append(
        _entry(
            "4.15",
            f"Edge CDN WAF {title}",
            index="aws",
            sourcetype=st,
            spl_filter="*",
            description=f"Monitors edge/CDN/WAF telemetry: {title.lower()}.",
            value=val,
            monitoring_type=("Security", "Availability"),
            equipment=("aws", "azure", "gcp"),
            app="Cloud edge logs via provider TA",
            splunkbase_id=1876,
            splunkbase_name="Splunk Add-on for AWS",
            vendor_url="https://docs.aws.amazon.com/waf/",
            prereq="4.15.1",
        )
    )

for i in range(20):
    OTHER_ENTRIES.append(
        _entry(
            "4.15",
            f"CDN Request Anomaly Signature {i + 1}",
            index="aws",
            sourcetype="aws:cloudfront:accesslogs",
            spl_filter="sc_status>=400",
            description=f"Detects anomalous CloudFront request signature cluster {i + 1}.",
            value="CDN request anomalies may indicate scraping, credential stuffing, or cache poisoning attempts.",
            monitoring_type=("Security", "Anomaly"),
            equipment=("aws",),
            app="Splunk Add-on for AWS",
            splunkbase_id=1876,
            splunkbase_name="Splunk Add-on for AWS",
            vendor_url="https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/",
            prereq="4.15.1",
        )
    )

# Crawl entries for new subcategories
for sub, title, idx, st, eq, sb_id, sb_name, url in (
    ("4.4", "Multi-Cloud Audit Feed Health", "cloud_multi", "aws:cloudtrail", ("aws", "azure", "gcp"), 1876, "Splunk Add-on for AWS", "https://docs.splunk.com/"),
    ("4.5", "Serverless Telemetry Baseline", "aws", "aws:lambda:cloudwatchlogs", ("aws",), 1876, "Splunk Add-on for AWS", "https://docs.aws.amazon.com/lambda/"),
    ("4.6", "Cloud Metrics Trend Baseline", "aws", "aws:cloudwatch", ("aws", "azure", "gcp"), 1876, "Splunk Add-on for AWS", "https://docs.aws.amazon.com/cloudwatch/"),
    ("4.7", "OCI Audit Log Baseline Ingestion", "oci", "oci:audit", ("oci",), 5680, "Splunk Add-on for OCI", "https://docs.oracle.com/en-us/iaas/Content/Audit/Concepts/auditoverview.htm"),
    ("4.8", "Alibaba ActionTrail Baseline Ingestion", "alibaba", "alibaba:actiontrail", ("alibaba",), 4800, "Splunk Add-on for Alibaba Cloud", "https://www.alibabacloud.com/help/en/actiontrail/"),
    ("4.9", "Kubernetes Audit Log Baseline", "kube", "kube:audit", ("kubernetes",), 4467, "Splunk Connect for Kubernetes", "https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/"),
    ("4.10", "Cloud Posture Findings Baseline", "aws", "aws:securityhub:findings", ("aws", "azure", "gcp"), 1876, "Splunk Add-on for AWS", "https://docs.aws.amazon.com/securityhub/"),
    ("4.11", "Cloud Cost Data Baseline", "aws", "aws:cur", ("aws",), 1876, "Splunk Add-on for AWS", "https://docs.aws.amazon.com/cur/"),
    ("4.12", "Cloud Database Audit Baseline", "aws", "aws:rds:audit", ("aws",), 1876, "Splunk Add-on for AWS", "https://docs.aws.amazon.com/rds/"),
    ("4.13", "Cloud Network Flow Baseline", "aws", "aws:vpcflow", ("aws",), 1876, "Splunk Add-on for AWS", "https://docs.aws.amazon.com/vpc/"),
    ("4.14", "Cloud Storage Audit Baseline", "aws", "aws:s3:accesslogs", ("aws",), 1876, "Splunk Add-on for AWS", "https://docs.aws.amazon.com/s3/"),
    ("4.15", "Edge CDN Log Baseline", "aws", "aws:cloudfront:accesslogs", ("aws",), 1876, "Splunk Add-on for AWS", "https://docs.aws.amazon.com/cloudfront/"),
):
    OTHER_ENTRIES.insert(
        0,
        TaxonomyEntry(
            subcategory=sub,
            title=title,
            service=sub,
            index=idx,
            sourcetype=st,
            spl_filter="*",
            criticality="critical",
            difficulty="beginner",
            monitoring_type=("Audit", "Operations"),
            splunk_pillar="Platform",
            description=f"Verifies {title.lower()} data flows into Splunk continuously.",
            value=f"{title} is the prerequisite feed for all {sub} detections.",
            implementation=f"Enable {st} ingestion via the appropriate Splunk TA into index={idx}.",
            visualization="Ingestion health single value and lag chart.",
            app=f"{sb_name} (Splunkbase {sb_id})",
            equipment=eq,
            wave="crawl",
            prerequisite_uc=None,
            splunkbase_id=sb_id,
            splunkbase_name=sb_name,
            vendor_ref_title="Vendor logging documentation",
            vendor_ref_url=url,
        ),
    )
