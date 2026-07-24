"""Taxonomy rows for cat-04 cloud UC expansion.

Each row maps to one real monitoring scenario grounded in vendor audit logs,
metrics, or posture findings. Event names and operations are from published
AWS CloudTrail, Azure Activity Log, and GCP Cloud Audit Log references.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TaxonomyEntry:
    subcategory: str  # e.g. "4.1"
    title: str
    service: str
    index: str
    sourcetype: str
    spl_filter: str  # provider-specific filter clause (no leading index=)
    criticality: str
    difficulty: str
    monitoring_type: tuple[str, ...]
    splunk_pillar: str
    description: str
    value: str
    implementation: str
    visualization: str
    app: str
    equipment: tuple[str, ...]
    equipment_models: tuple[str, ...] = ()
    mitre_attack: tuple[str, ...] = ()
    cim_models: tuple[str, ...] = ()
    cim_spl: str = ""
    known_false_positives: str = ""
    wave: str = "walk"
    prerequisite_uc: str | None = None  # bare id like "4.1.78"
    cis_control: str | None = None  # CIS benchmark shorthand for compliance[]
    nist_control: str | None = None
    cost_tier: str = "medium"
    splunkbase_id: int = 1876
    splunkbase_name: str = "Splunk Add-on for AWS"
    vendor_ref_title: str = ""
    vendor_ref_url: str = ""
    security_domain: str = "cloud"
    table_fields: str = "_time userIdentity.arn eventName sourceIPAddress errorCode"


def _aws_ct(
    *,
    title: str,
    service: str,
    events: tuple[str, ...],
    description: str,
    value: str,
    criticality: str = "high",
    difficulty: str = "beginner",
    monitoring_type: tuple[str, ...] = ("Security", "Audit"),
    mitre: tuple[str, ...] = ("T1078.004",),
    cis: str | None = None,
    nist: str | None = "AU-2",
    wave: str = "walk",
    prereq: str | None = "4.1.78",
    cim: tuple[str, ...] = ("Change",),
    vendor_url: str = "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference.html",
) -> TaxonomyEntry:
    ev_clause = " OR ".join(f'eventName="{e}"' for e in events)
    return TaxonomyEntry(
        subcategory="4.1",
        title=title,
        service=service,
        index="aws",
        sourcetype="aws:cloudtrail",
        spl_filter=f"({ev_clause})",
        criticality=criticality,
        difficulty=difficulty,
        monitoring_type=monitoring_type,
        splunk_pillar="Security" if "Security" in monitoring_type else "Observability",
        description=description,
        value=value,
        implementation=(
            f"Enable organization-wide CloudTrail with management and data events for {service}. "
            f"Configure `Splunk_TA_aws` CloudTrail S3 or CloudWatch Logs input into `index=aws`. "
            f"Save as a real-time alert on matching `{events[0]}` events; tune exclusions via saved lookup for break-glass roles."
        ),
        visualization="Events list (critical alert), Timeline by eventName, Table of actor and resource.",
        app="Splunk Add-on for AWS (`Splunk_TA_aws`, Splunkbase 1876)",
        equipment=("aws",),
        equipment_models=("aws_cloudtrail",),
        mitre_attack=mitre,
        cim_models=cim,
        known_false_positives=(
            "Planned change windows registered in CMDB; automation roles used by CI/CD pipelines "
            "with documented service accounts; sandbox accounts excluded via `aws:accountId` lookup."
        ),
        wave=wave,
        prerequisite_uc=prereq,
        cis_control=cis,
        nist_control=nist,
        splunkbase_id=1876,
        splunkbase_name="Splunk Add-on for AWS",
        vendor_ref_title="AWS CloudTrail event reference",
        vendor_ref_url=vendor_url,
    )


def _aws_svc(
    *,
    title: str,
    service: str,
    sourcetype: str,
    spl_filter: str,
    description: str,
    value: str,
    monitoring_type: tuple[str, ...],
    criticality: str = "high",
    pillar: str = "Security",
    table_fields: str = "_time severity findingType resourceDetails",
) -> TaxonomyEntry:
    return TaxonomyEntry(
        subcategory="4.1",
        title=title,
        service=service,
        index="aws",
        sourcetype=sourcetype,
        spl_filter=spl_filter,
        criticality=criticality,
        difficulty="intermediate",
        monitoring_type=monitoring_type,
        splunk_pillar=pillar,
        description=description,
        value=value,
        implementation=(
            f"Enable {service} integration in AWS and forward findings/logs via `Splunk_TA_aws` "
            f"into `index=aws` with `sourcetype={sourcetype}`. Validate field extractions before alerting."
        ),
        visualization="Notable-style table, severity timeline, single-value open finding count.",
        app="Splunk Add-on for AWS (`Splunk_TA_aws`, Splunkbase 1876)",
        equipment=("aws",),
        mitre_attack=("T1190",),
        wave="walk",
        prerequisite_uc="4.1.78",
        nist_control="SI-4",
        splunkbase_id=1876,
        splunkbase_name="Splunk Add-on for AWS",
        vendor_ref_title=f"AWS {service} documentation",
        vendor_ref_url="https://docs.aws.amazon.com/",
        table_fields=table_fields,
    )


# ---------------------------------------------------------------------------
# Crawl UCs (one per major provider) — prerequisite anchors
# ---------------------------------------------------------------------------

CRAWL_AWS = TaxonomyEntry(
    subcategory="4.1",
    title="AWS CloudTrail Baseline Ingestion and Health",
    service="cloudtrail",
    index="aws",
    sourcetype="aws:cloudtrail",
    spl_filter="*",
    criticality="critical",
    difficulty="beginner",
    monitoring_type=("Audit", "Operations"),
    splunk_pillar="Platform",
    description=(
        "Verifies that AWS CloudTrail management events are flowing into Splunk via the AWS add-on, "
        "with recent events across regions and no prolonged ingestion gaps that would blind security monitoring."
    ),
    value=(
        "CloudTrail is the foundational audit plane for every other AWS detection in this catalog. "
        "Without continuous, multi-region CloudTrail ingestion, IAM, network, and data-plane changes "
        "become invisible until an incident or audit reveals the gap."
    ),
    implementation=(
        "Enable an organization trail or account-level trails in all active regions. Configure "
        "`Splunk_TA_aws` CloudTrail input (S3 bucket or CloudWatch Logs subscription). "
        "Alert when no events arrive for 60 minutes during business hours."
    ),
    visualization="Single value (events last 24h), ingestion lag chart, region coverage matrix.",
    app="Splunk Add-on for AWS (`Splunk_TA_aws`, Splunkbase 1876)",
    equipment=("aws",),
    equipment_models=("aws_cloudtrail",),
    mitre_attack=("N/A (operational baseline)",),
    cim_models=("Change",),
    wave="crawl",
    prerequisite_uc=None,
    nist_control="AU-2",
    cost_tier="medium",
    splunkbase_id=1876,
    splunkbase_name="Splunk Add-on for AWS",
    vendor_ref_title="AWS CloudTrail user guide",
    vendor_ref_url="https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html",
    table_fields="_time eventName awsRegion userIdentity.arn",
)

# ---------------------------------------------------------------------------
# AWS CloudTrail expansion (~250 scenarios via event groups)
# ---------------------------------------------------------------------------

_AWS_IAM_EVENTS: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("IAM User Creation", "Detects CreateUser API calls that add new IAM principals.", "New IAM users expand the credential surface; unapproved accounts often precede persistence or data theft.", ("CreateUser",)),
    ("IAM User Deletion", "Detects DeleteUser removing IAM principals.", "Sudden user deletion may indicate cover-up after compromise or destructive insider activity.", ("DeleteUser",)),
    ("IAM Access Key Creation", "Detects CreateAccessKey for long-lived programmatic credentials.", "New access keys outside approved automation are a common persistence mechanism after initial access.", ("CreateAccessKey",)),
    ("IAM Access Key Deletion", "Detects DeleteAccessKey removing programmatic credentials.", "Key deletion can indicate cleanup after exfiltration or destructive changes to break integrations.", ("DeleteAccessKey",)),
    ("IAM Login Profile Changes", "Detects CreateLoginProfile, UpdateLoginProfile, DeleteLoginProfile on console passwords.", "Console password changes on service or human users require review—attackers enable console access after key theft.", ("CreateLoginProfile", "UpdateLoginProfile", "DeleteLoginProfile")),
    ("IAM Role Creation", "Detects CreateRole adding new assumable roles.", "New roles with broad trust policies are a privilege-escalation path via sts:AssumeRole.", ("CreateRole",)),
    ("IAM Role Policy Attachment", "Detects AttachRolePolicy and PutRolePolicy modifying role permissions.", "Policy changes on roles used by workloads can silently grant data access across accounts.", ("AttachRolePolicy", "PutRolePolicy", "DetachRolePolicy", "DeleteRolePolicy")),
    ("IAM User Policy Attachment", "Detects AttachUserPolicy and inline PutUserPolicy on users.", "Direct user policy attachments bypass group-based governance and are high risk in production.", ("AttachUserPolicy", "PutUserPolicy", "DetachUserPolicy", "DeleteUserPolicy")),
    ("IAM Policy Version Changes", "Detects CreatePolicyVersion and SetDefaultPolicyVersion.", "Default policy version swaps can restore overly permissive statements without a full policy replace.", ("CreatePolicyVersion", "SetDefaultPolicyVersion", "DeletePolicyVersion")),
    ("IAM MFA Device Deactivation", "Detects DeactivateMFADevice and DeleteVirtualMFADevice.", "MFA removal on privileged users is a strong signal of account takeover preparation.", ("DeactivateMFADevice", "DeleteVirtualMFADevice"),),
    ("IAM Group Membership Changes", "Detects AddUserToGroup and RemoveUserFromGroup.", "Group changes move users into privileged groups without creating new credentials.", ("AddUserToGroup", "RemoveUserFromGroup")),
    ("IAM SAML Provider Changes", "Detects CreateSAMLProvider, UpdateSAMLProvider, DeleteSAMLProvider.", "SAML provider edits affect federated login trust and can enable unauthorized IdP federation.", ("CreateSAMLProvider", "UpdateSAMLProvider", "DeleteSAMLProvider")),
    ("IAM Password Policy Changes", "Detects UpdateAccountPasswordPolicy weakening requirements.", "Weaker password policy reduces brute-force resistance for console users.", ("UpdateAccountPasswordPolicy",)),
]

_AWS_EC2_EVENTS: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("EC2 Instance Launch", "Detects RunInstances creating new virtual machines.", "Unexpected instance launches may indicate cryptomining, rogue workloads, or shadow IT.", ("RunInstances",)),
    ("EC2 Instance Termination", "Detects TerminateInstances destroying VMs.", "Mass terminations cause outages; targeted kills may follow data theft.", ("TerminateInstances",)),
    ("EC2 Security Group Ingress Open", "Detects AuthorizeSecurityGroupIngress allowing inbound traffic.", "Security group changes exposing 0.0.0.0/0 are a leading cause of cloud breaches.", ("AuthorizeSecurityGroupIngress", "ModifySecurityGroupRules")),
    ("EC2 Security Group Egress Changes", "Detects AuthorizeSecurityGroupEgress and RevokeSecurityGroupEgress.", "Egress rule changes can enable data exfiltration paths to attacker C2.", ("AuthorizeSecurityGroupEgress", "RevokeSecurityGroupEgress")),
    ("EC2 Security Group Deletion", "Detects DeleteSecurityGroup removing network controls.", "Deleting security groups may bypass segmentation during an attack.", ("DeleteSecurityGroup",)),
    ("EC2 Metadata Service Modification", "Detects ModifyInstanceMetadataOptions (IMDSv1 enablement).", "IMDSv1 exposes instance credentials to SSRF; CIS requires IMDSv2.", ("ModifyInstanceMetadataOptions",)),
    ("EC2 Snapshot Creation", "Detects CreateSnapshot and CopySnapshot.", "Snapshots copy disk data and can be shared cross-account for exfiltration.", ("CreateSnapshot", "CopySnapshot")),
    ("EC2 Snapshot Deletion", "Detects DeleteSnapshot removing recovery points.", "Snapshot deletion impairs forensics and disaster recovery.", ("DeleteSnapshot",)),
    ("EC2 Volume Modification", "Detects ModifyVolume and AttachVolume changes.", "Volume attach to unexpected instances may expose data stores.", ("ModifyVolume", "AttachVolume", "DetachVolume")),
    ("EC2 Elastic IP Association", "Detects AssociateAddress assigning public IPs.", "New public IPs on private subnets may expose admin interfaces.", ("AssociateAddress", "AllocateAddress")),
    ("EC2 VPC Flow Log Changes", "Detects CreateFlowLogs and DeleteFlowLogs.", "Disabling flow logs blinds network detection during incidents.", ("CreateFlowLogs", "DeleteFlowLogs")),
    ("EC2 Route Table Changes", "Detects CreateRoute, ReplaceRoute, DeleteRoute.", "Route table edits can redirect traffic through attacker-controlled gateways.", ("CreateRoute", "ReplaceRoute", "DeleteRoute", "CreateRouteTable", "DeleteRouteTable")),
    ("EC2 Internet Gateway Attachment", "Detects AttachInternetGateway to VPCs.", "IGW attachment enables direct internet egress from previously isolated VPCs.", ("AttachInternetGateway", "CreateInternetGateway")),
    ("EC2 NAT Gateway Changes", "Detects CreateNatGateway and DeleteNatGateway.", "NAT changes affect egress monitoring choke points.", ("CreateNatGateway", "DeleteNatGateway")),
]

_AWS_S3_EVENTS: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("S3 Bucket Creation", "Detects CreateBucket in unexpected regions.", "Buckets in unapproved regions may violate data residency or hide exfiltration staging.", ("CreateBucket",)),
    ("S3 Bucket Deletion", "Detects DeleteBucket removing object stores.", "Bucket deletion causes irreversible data loss and audit gaps.", ("DeleteBucket",)),
    ("S3 Bucket Encryption Changes", "Detects PutBucketEncryption and DeleteBucketEncryption.", "Removing default encryption exposes objects at rest.", ("PutBucketEncryption", "DeleteBucketEncryption")),
    ("S3 Bucket Logging Disabled", "Detects PutBucketLogging with empty target.", "Access logging gaps hide object-level exfiltration.", ("PutBucketLogging",)),
    ("S3 Object ACL Changes", "Detects PutObjectAcl granting public or cross-account access.", "Object ACL changes are a common public exposure path.", ("PutObjectAcl",)),
    ("S3 Replication Rule Changes", "Detects PutBucketReplication and DeleteBucketReplication.", "Replication to external accounts can exfiltrate data continuously.", ("PutBucketReplication", "DeleteBucketReplication")),
]

_AWS_RDS_EVENTS: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("RDS Instance Creation", "Detects CreateDBInstance provisioning databases.", "Shadow databases may store stolen data or bypass backup policies.", ("CreateDBInstance",)),
    ("RDS Instance Deletion", "Detects DeleteDBInstance destroying databases.", "Production DB deletion is both availability and compliance critical.", ("DeleteDBInstance",)),
    ("RDS Instance Modification", "Detects ModifyDBInstance including public accessibility.", "Publicly accessible RDS instances are a top attack vector.", ("ModifyDBInstance",)),
    ("RDS Snapshot Sharing", "Detects ModifyDBSnapshotAttribute and ModifyDBClusterSnapshotAttribute.", "Snapshot sharing to external accounts enables data theft.", ("ModifyDBSnapshotAttribute", "ModifyDBClusterSnapshotAttribute")),
    ("RDS Cluster Changes", "Detects CreateDBCluster and DeleteDBCluster for Aurora.", "Aurora cluster lifecycle changes affect HA and backup posture.", ("CreateDBCluster", "DeleteDBCluster", "ModifyDBCluster")),
]

_AWS_LAMBDA_EVENTS: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("Lambda Function Creation", "Detects CreateFunction deploying new code.", "Unauthorized functions may run cryptominers or proxy C2.", ("CreateFunction",)),
    ("Lambda Function Configuration Update", "Detects UpdateFunctionConfiguration including IAM role changes.", "Role changes on functions grant their execution role permissions to attackers.", ("UpdateFunctionConfiguration",)),
    ("Lambda Resource Policy Changes", "Detects AddPermission and RemovePermission on function URLs.", "Public function URLs or cross-account invoke permissions expose serverless endpoints.", ("AddPermission", "RemovePermission")),
]

_AWS_KMS_EVENTS: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("KMS Key Disablement", "Detects DisableKey and ScheduleKeyDeletion.", "Key disablement causes decrypt failures and may precede ransomware.", ("DisableKey", "ScheduleKeyDeletion")),
    ("KMS Key Policy Changes", "Detects PutKeyPolicy altering key administrators.", "Key policy edits can grant decrypt access to external accounts.", ("PutKeyPolicy",)),
    ("KMS Grant Creation", "Detects CreateGrant delegating key usage.", "Grants can allow ephemeral decrypt without permanent IAM changes.", ("CreateGrant", "RetireGrant")),
]

_AWS_ORG_EVENTS: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("AWS Organizations Account Creation", "Detects CreateAccount in the org.", "New accounts outside provisioning workflow expand unmanaged attack surface.", ("CreateAccount",)),
    ("AWS Organizations Policy Changes", "Detects CreatePolicy and AttachPolicy for SCPs.", "SCP changes can remove guardrails that block risky API calls.", ("CreatePolicy", "AttachPolicy", "DetachPolicy", "DeletePolicy")),
    ("AWS Organizations Leave", "Detects LeaveOrganization and RemoveAccountFromOrganization.", "Removing accounts from org removes centralized logging and SCP protection.", ("LeaveOrganization", "RemoveAccountFromOrganization")),
]

_AWS_OTHER_EVENTS: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("Secrets Manager Secret Deletion", "Detects DeleteSecret and CancelRotateSecret.", "Secret deletion breaks applications and may hide attacker credential theft.", ("DeleteSecret", "CancelRotateSecret")),
    ("Secrets Manager Secret Value Update", "Detects PutSecretValue changing stored credentials.", "Unexpected secret updates may indicate persistence in application credentials.", ("PutSecretValue", "UpdateSecret")),
    ("CloudFormation Stack Deletion", "Detects DeleteStack removing infrastructure.", "Stack deletes can remove detective controls and backups.", ("DeleteStack",)),
    ("CloudFormation Stack Update", "Detects UpdateStack changing templates.", "Template updates may open security groups or IAM paths.", ("UpdateStack", "CreateStack")),
    ("API Gateway REST API Changes", "Detects CreateRestApi, UpdateRestApi, DeleteRestApi.", "API Gateway changes expose new HTTP attack surface.", ("CreateRestApi", "UpdateRestApi", "DeleteRestApi")),
    ("Route53 DNS Record Changes", "Detects ChangeResourceRecordSets.", "DNS hijacking redirects users to phishing or C2 infrastructure.", ("ChangeResourceRecordSets",)),
    ("CloudFront Distribution Changes", "Detects CreateDistribution, UpdateDistribution, DeleteDistribution.", "CDN changes can serve malicious content from trusted domains.", ("CreateDistribution", "UpdateDistribution", "DeleteDistribution")),
    ("WAF Web ACL Changes", "Detects CreateWebACL, UpdateWebACL, DeleteWebACL.", "WAF rule removal opens applications to exploitation.", ("CreateWebACL", "UpdateWebACL", "DeleteWebACL", "AssociateWebACL", "DisassociateWebACL")),
    ("Config Recorder Stop", "Detects StopConfigurationRecorder and DeleteConfigurationRecorder.", "Stopping AWS Config halts configuration compliance evidence.", ("StopConfigurationRecorder", "DeleteConfigurationRecorder", "PutConfigurationRecorder")),
    ("Config Rule Changes", "Detects PutConfigRule and DeleteConfigRule.", "Config rule deletion removes automated compliance checks.", ("PutConfigRule", "DeleteConfigRule")),
    ("CloudWatch Alarm Deletion", "Detects DeleteAlarms removing operational alerts.", "Alarm deletion hides performance and security anomalies.", ("DeleteAlarms", "PutMetricAlarm")),
    ("EKS Cluster Creation", "Detects CreateCluster for Kubernetes control planes.", "New EKS clusters expand container attack surface.", ("CreateCluster", "DeleteCluster", "UpdateClusterConfig")),
    ("ECS Task Definition Registration", "Detects RegisterTaskDefinition with new container images.", "Task definitions running privileged containers increase host compromise risk.", ("RegisterTaskDefinition", "DeregisterTaskDefinition")),
    ("DynamoDB Table Deletion", "Detects DeleteTable destroying NoSQL data stores.", "Table deletion is irreversible without backups.", ("DeleteTable", "CreateTable", "UpdateTable")),
    ("SageMaker Notebook Instance Creation", "Detects CreateNotebookInstance and CreateTrainingJob.", "ML instances with internet access can exfiltrate datasets.", ("CreateNotebookInstance", "CreateTrainingJob")),
    ("Redshift Cluster Changes", "Detects CreateCluster and ModifyCluster for data warehouses.", "Warehouse exposure changes affect analytics data classification.", ("CreateCluster", "DeleteCluster", "ModifyCluster")),
    ("SQS Queue Policy Changes", "Detects SetQueueAttributes and AddPermission on queues.", "Queue policy changes may allow cross-account message theft.", ("SetQueueAttributes", "AddPermission")),
    ("SNS Topic Policy Changes", "Detects SetTopicAttributes and AddPermission on topics.", "Public SNS topics leak event data to subscribers.", ("SetTopicAttributes", "AddPermission")),
    ("STS AssumeRole Anomalies", "Surfaces AssumeRole with unusual source IPs or external principals.", "Cross-account role assumption is core to cloud lateral movement.", ("AssumeRole",)),
    ("Cognito User Pool Changes", "Detects UpdateUserPool and DeleteUserPool.", "Identity pool changes affect customer-facing authentication.", ("UpdateUserPool", "DeleteUserPool", "CreateUserPool")),
    ("Backup Vault Changes", "Detects CreateBackupVault and DeleteBackupVault.", "Backup vault deletion impairs ransomware recovery.", ("CreateBackupVault", "DeleteBackupVault")),
    ("Control Tower Enrollment", "Detects EnableOrganizationAccess and RegisterDelegatedAdministrator.", "Control Tower changes affect landing zone guardrails.", ("RegisterDelegatedAdministrator", "EnableOrganizationAccess")),
]

_AWS_POSTURE: list[TaxonomyEntry] = [
    _aws_svc(
        title="GuardDuty High-Severity Findings",
        service="guardduty",
        sourcetype="aws:guardduty",
        spl_filter='severity>=7',
        description="Surfaces Amazon GuardDuty findings at high or critical severity ingested via the AWS add-on.",
        value="GuardDuty correlates CloudTrail, VPC flow, and DNS logs for threat detections—high-severity findings warrant immediate SOC review.",
        monitoring_type=("Security", "Threat"),
    ),
    _aws_svc(
        title="Security Hub Failed Controls",
        service="securityhub",
        sourcetype="aws:securityhub:findings",
        spl_filter='Compliance.Status=FAILED OR RecordState=ACTIVE',
        description="Lists active Security Hub findings where compliance status is FAILED against enabled standards.",
        value="Security Hub aggregates CIS, PCI, and FSBP controls—failed checks show measurable posture gaps.",
        monitoring_type=("Compliance", "Security"),
    ),
    _aws_svc(
        title="AWS Config Non-Compliant Resources",
        service="config",
        sourcetype="aws:config:notification",
        spl_filter='configurationItemStatus=ResourceDiscovered OR complianceType=NON_COMPLIANT',
        description="Detects AWS Config notifications marking resources NON_COMPLIANT against enabled rules.",
        value="Config rule failures prove drift from approved baselines before auditors or attackers find gaps.",
        monitoring_type=("Compliance", "Configuration"),
    ),
    _aws_svc(
        title="Macie Sensitive Data Findings",
        service="macie",
        sourcetype="aws:macie",
        spl_filter="*",
        description="Ingests Amazon Macie findings for S3 buckets containing sensitive data classifications.",
        value="Macie findings show where PII or secrets sit in object storage—critical for data-loss prevention.",
        monitoring_type=("Security", "Data Quality"),
    ),
    _aws_svc(
        title="Inspector Vulnerability Findings",
        service="inspector",
        sourcetype="aws:inspector:findings",
        spl_filter="*",
        description="Surfaces Amazon Inspector findings for EC2, ECR, and Lambda package vulnerabilities.",
        value="Inspector findings drive patch prioritization for exploitable CVEs in cloud workloads.",
        monitoring_type=("Vulnerability", "Security"),
    ),
    _aws_svc(
        title="VPC Flow Log Rejected Connections Spike",
        service="vpc",
        sourcetype="aws:vpcflow",
        spl_filter='action=REJECT',
        description="Aggregates rejected VPC flow records to detect port scans and lateral movement attempts.",
        value="Rejected flow spikes reveal reconnaissance and blocked exfiltration that CloudTrail alone misses.",
        monitoring_type=("Security", "Network"),
        pillar="Security",
        table_fields="_time src_ip dest_ip dest_port action bytes",
    ),
    _aws_svc(
        title="S3 Access Log Anonymous Requests",
        service="s3",
        sourcetype="aws:s3:accesslogs",
        spl_filter='operation=REST.GET.OBJECT AND http_status=200',
        description="Finds successful S3 object reads from anonymous or unexpected principals in access logs.",
        value="Anonymous GET success on sensitive buckets indicates public exposure beyond policy intent.",
        monitoring_type=("Security", "Audit"),
        table_fields="_time bucket key requester_ip operation http_status",
    ),
    _aws_svc(
        title="CloudFront 4xx/5xx Error Rate Spike",
        service="cloudfront",
        sourcetype="aws:cloudfront:accesslogs",
        spl_filter="sc_status>=400",
        description="Tracks elevated HTTP error rates on CloudFront distributions from access logs.",
        value="CDN error spikes may indicate origin misconfiguration, DDoS, or WAF bypass attempts.",
        monitoring_type=("Availability", "Performance"),
        pillar="Observability",
        criticality="medium",
        table_fields="_time cs_host sc_status cs_uri_stem time_taken",
    ),
    _aws_svc(
        title="AWS CUR Daily Cost Anomaly",
        service="billing",
        sourcetype="aws:cur",
        spl_filter="*",
        description="Compares daily AWS Cost and Usage Report spend against a seven-day baseline per linked account.",
        value="Cost anomalies catch cryptomining, mis-provisioned resources, and billing fraud before finance close.",
        monitoring_type=("Cost", "Anomaly"),
        pillar="Observability",
        criticality="medium",
        table_fields="_time lineItem/UnblendedCost lineItem/ProductCode bill/PayerAccountId",
    ),
    _aws_svc(
        title="Lambda Error Rate by Function",
        service="lambda",
        sourcetype="aws:lambda:cloudwatchlogs",
        spl_filter='report=REPORT OR ERROR',
        description="Calculates error and throttle rates from Lambda platform REPORT lines in CloudWatch Logs.",
        value="Serverless error spikes break dependent microservices and often precede deployment regressions.",
        monitoring_type=("Availability", "Performance"),
        pillar="Observability",
        criticality="medium",
        table_fields="_time function_name duration billed_duration memory_size",
    ),
]


def _build_aws_cloudtrail_entries() -> list[TaxonomyEntry]:
    out: list[TaxonomyEntry] = [CRAWL_AWS]
    groups = [
        ("iam", _AWS_IAM_EVENTS, "1.1"),
        ("ec2", _AWS_EC2_EVENTS, "4.3"),
        ("s3", _AWS_S3_EVENTS, "2.1"),
        ("rds", _AWS_RDS_EVENTS, "2.3"),
        ("lambda", _AWS_LAMBDA_EVENTS, "2.2"),
        ("kms", _AWS_KMS_EVENTS, "3.6"),
        ("organizations", _AWS_ORG_EVENTS, "1.2"),
        ("misc", _AWS_OTHER_EVENTS, "1.3"),
    ]
    for svc, rows, cis in groups:
        for title_suffix, desc, val, events in rows:
            out.append(
                _aws_ct(
                    title=f"AWS {title_suffix}",
                    service=svc,
                    events=events,
                    description=desc,
                    value=val,
                    cis=cis,
                )
            )
    out.extend(_AWS_POSTURE)
    return out


def crawl_uc_ids() -> dict[str, str]:
    """Return subcategory -> crawl UC id (bare, no UC- prefix)."""
    return {
        "4.1": "4.1.78",
        "4.2": "4.2.58",
        "4.3": "4.3.41",
        "4.4": "4.4.33",
        "4.5": "4.5.16",
        "4.6": "4.6.7",
        "4.7": "4.7.1",
        "4.8": "4.8.1",
        "4.9": "4.9.1",
        "4.10": "4.10.1",
        "4.11": "4.11.1",
        "4.12": "4.12.1",
        "4.13": "4.13.1",
        "4.14": "4.14.1",
        "4.15": "4.15.1",
    }


# Import provider-specific builders (azure, gcp, other subcats)
from .taxonomy_azure import AZURE_ENTRIES  # noqa: E402
from .taxonomy_gcp import GCP_ENTRIES  # noqa: E402
from .taxonomy_other import OTHER_ENTRIES  # noqa: E402

ALL_ENTRIES: list[TaxonomyEntry] = (
    _build_aws_cloudtrail_entries() + AZURE_ENTRIES + GCP_ENTRIES + OTHER_ENTRIES
)
