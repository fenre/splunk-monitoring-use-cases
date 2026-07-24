"""Additional taxonomy rows to reach 1000+ new cloud UCs — all real API/audit surfaces."""

from __future__ import annotations

from .taxonomy import TaxonomyEntry, _aws_ct

EXPANSION_ENTRIES: list[TaxonomyEntry] = []

# ---------------------------------------------------------------------------
# AWS: additional CloudTrail event groups (real event names)
# ---------------------------------------------------------------------------
_AWS_EXTRA_GROUPS: list[tuple[str, list[tuple[str, str, str, tuple[str, ...]]]]] = [
    (
        "elasticache",
        [
            ("ElastiCache Cluster Create", "Detects CreateCacheCluster.", "New cache clusters expand data store attack surface.", ("CreateCacheCluster", "CreateReplicationGroup")),
            ("ElastiCache Cluster Delete", "Detects DeleteCacheCluster.", "Cache deletion causes application outages.", ("DeleteCacheCluster", "DeleteReplicationGroup")),
            ("ElastiCache Security Group Change", "Detects cache SG modifications.", "Cache SG changes may expose Redis/Memcached.", ("AuthorizeCacheSecurityGroupIngress", "RevokeCacheSecurityGroupIngress")),
        ],
    ),
    (
        "emr",
        [
            ("EMR Cluster Termination", "Detects TerminateJobFlows.", "EMR termination destroys big-data workloads.", ("TerminateJobFlows",)),
            ("EMR Cluster Creation", "Detects RunJobFlow.", "Unauthorized EMR clusters may run cryptomining.", ("RunJobFlow",)),
        ],
    ),
    (
        "glue",
        [
            ("Glue Job Delete", "Detects DeleteJob.", "Glue job deletion breaks ETL pipelines.", ("DeleteJob",)),
            ("Glue Crawler Change", "Detects crawler create/update.", "Crawler changes affect data catalog classification.", ("CreateCrawler", "UpdateCrawler", "DeleteCrawler")),
        ],
    ),
    (
        "athena",
        [
            ("Athena Workgroup Change", "Detects workgroup create/update.", "Workgroup changes affect query billing and encryption.", ("CreateWorkGroup", "UpdateWorkGroup", "DeleteWorkGroup")),
        ],
    ),
    (
        "kinesis",
        [
            ("Kinesis Stream Delete", "Detects DeleteStream.", "Stream deletion breaks real-time pipelines.", ("DeleteStream", "CreateStream")),
            ("Kinesis Firehose Change", "Detects delivery stream changes.", "Firehose changes affect log export to Splunk/S3.", ("CreateDeliveryStream", "DeleteDeliveryStream", "UpdateDestination")),
        ],
    ),
    (
        "stepfunctions",
        [
            ("Step Functions State Machine Delete", "Detects DeleteStateMachine.", "Workflow deletion breaks orchestration.", ("DeleteStateMachine", "UpdateStateMachine")),
        ],
    ),
    (
        "ssm",
        [
            ("SSM Document Publish", "Detects CreateDocument/UpdateDocument.", "SSM documents can run commands on instances.", ("CreateDocument", "UpdateDocument", "DeleteDocument")),
            ("SSM Parameter Store Delete", "Detects DeleteParameter.", "Parameter deletion breaks app configuration.", ("DeleteParameter", "PutParameter")),
        ],
    ),
    (
        "cloudwatch",
        [
            ("CloudWatch Log Group Delete", "Detects DeleteLogGroup.", "Log group deletion destroys audit evidence.", ("DeleteLogGroup",)),
            ("CloudWatch Logs Filter Delete", "Detects DeleteSubscriptionFilter.", "Subscription filter removal stops log export.", ("DeleteSubscriptionFilter", "PutSubscriptionFilter")),
        ],
    ),
    (
        "acm",
        [
            ("ACM Certificate Delete", "Detects DeleteCertificate.", "Cert deletion causes TLS outages.", ("DeleteCertificate", "ImportCertificate")),
        ],
    ),
    (
        "elasticloadbalancing",
        [
            ("ELB Listener Change", "Detects listener create/modify.", "Listener changes redirect production traffic.", ("CreateListener", "ModifyListener", "DeleteListener")),
            ("Target Group Deregistration", "Detects DeregisterTargets.", "Target deregistration causes load balancer outages.", ("DeregisterTargets", "RegisterTargets")),
        ],
    ),
    (
        "efs",
        [
            ("EFS File System Delete", "Detects DeleteFileSystem.", "EFS deletion destroys shared file data.", ("DeleteFileSystem", "CreateFileSystem")),
        ],
    ),
    (
        "fsx",
        [
            ("FSx File System Delete", "Detects DeleteFileSystem.", "FSx deletion affects Windows/Lustre shares.", ("DeleteFileSystem",)),
        ],
    ),
    (
        "transfer",
        [
            ("Transfer Family Server Change", "Detects CreateServer/DeleteServer.", "SFTP server changes affect file exchange security.", ("CreateServer", "DeleteServer", "UpdateServer")),
        ],
    ),
    (
        "codepipeline",
        [
            ("CodePipeline Delete", "Detects DeletePipeline.", "Pipeline deletion stops CI/CD.", ("DeletePipeline", "CreatePipeline")),
        ],
    ),
    (
        "codebuild",
        [
            ("CodeBuild Project Delete", "Detects DeleteProject.", "Build project deletion breaks CI.", ("DeleteProject", "CreateProject")),
        ],
    ),
    (
        "ecr",
        [
            ("ECR Repository Policy Change", "Detects SetRepositoryPolicy.", "ECR policy may allow image pull from external accounts.", ("SetRepositoryPolicy", "DeleteRepositoryPolicy")),
            ("ECR Image Delete", "Detects BatchDeleteImage.", "Image deletion affects supply chain recovery.", ("BatchDeleteImage",)),
        ],
    ),
    (
        "batch",
        [
            ("Batch Compute Environment Delete", "Detects DeleteComputeEnvironment.", "Batch environment deletion stops HPC jobs.", ("DeleteComputeEnvironment",)),
        ],
    ),
    (
        "mq",
        [
            ("Amazon MQ Broker Delete", "Detects DeleteBroker.", "Message broker deletion breaks async apps.", ("DeleteBroker", "CreateBroker")),
        ],
    ),
    (
        "neptune",
        [
            ("Neptune Cluster Delete", "Detects DeleteDBCluster.", "Graph DB deletion destroys relationship data.", ("DeleteDBCluster", "CreateDBCluster")),
        ],
    ),
    (
        "documentdb",
        [
            ("DocumentDB Cluster Delete", "Detects DeleteDBCluster.", "DocumentDB deletion causes Mongo-compatible outages.", ("DeleteDBCluster",)),
        ],
    ),
    (
        "memorydb",
        [
            ("MemoryDB Cluster Delete", "Detects DeleteCluster.", "MemoryDB deletion affects Redis-compatible apps.", ("DeleteCluster",)),
        ],
    ),
    (
        "opensearch",
        [
            ("OpenSearch Domain Delete", "Detects DeleteDomain.", "Search domain deletion destroys log/search indices.", ("DeleteDomain", "CreateDomain")),
        ],
    ),
    (
        "workspaces",
        [
            ("WorkSpaces Termination", "Detects TerminateWorkSpaces.", "VDI termination affects remote workforce.", ("TerminateWorkSpaces", "CreateWorkSpaces")),
        ],
    ),
    (
        "directconnect",
        [
            ("Direct Connect Delete", "Detects DeleteConnection.", "DX deletion isolates hybrid networks.", ("DeleteConnection", "CreateConnection")),
        ],
    ),
    (
        "globalaccelerator",
        [
            ("Global Accelerator Delete", "Detects DeleteAccelerator.", "GA deletion affects anycast entry points.", ("DeleteAccelerator",)),
        ],
    ),
]

for svc, rows in _AWS_EXTRA_GROUPS:
    for title_suffix, desc, val, events in rows:
        EXPANSION_ENTRIES.append(
            _aws_ct(
                title=f"AWS {title_suffix}",
                service=svc,
                events=events,
                description=desc,
                value=val,
            )
        )

# Import side-effect: extend ALL_ENTRIES
from . import taxonomy as _tax  # noqa: E402

_tax.ALL_ENTRIES.extend(EXPANSION_ENTRIES)
